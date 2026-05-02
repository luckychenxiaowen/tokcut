"""tokcut 代理服务器 —— FastAPI 主入口。

作为透明的 LLM 代理层，兼容 OpenAI /v1/chat/completions 接口。
核心流程：缓存检查 → 输入压缩 → 输出压缩增强 → 转发 → 后处理 → 返回。
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .__version__ import __version__
from .cache import SemanticCache
from .compressor import OutputCompressor
from .config import load_config
from .prompt_compressor import PromptCompressor
from .token_counter import count_messages_tokens, count_tokens

# ── 加载环境变量 ──────────────────────────────────────────────

load_dotenv()

# ── 日志 ─────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tokcut")

# ── FastAPI 应用 ─────────────────────────────────────────────

app = FastAPI(
    title="tokcut",
    version=__version__,
    description="Multi-Model Token Saving Proxy — Cut 30%-65% LLM costs transparently.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── 全局组件 ─────────────────────────────────────────────────

# 优先从环境变量 TOKCUT_CONFIG_PATH 加载配置
config_path = os.getenv("TOKCUT_CONFIG_PATH")
config = load_config(config_path)

compressor = OutputCompressor(level=config["compressor"]["level"])
prompt_compressor = PromptCompressor(mode=config["prompt_compressor"]["mode"])
cache = SemanticCache(config["cache"])

logger.info(f"tokcut v{__version__} starting")
logger.info(
    f"Compressor: enabled={config['compressor']['enabled']}, "
    f"level={config['compressor']['level']}"
)
logger.info(
    f"Prompt Compressor: enabled={config['prompt_compressor']['enabled']}, "
    f"mode={config['prompt_compressor']['mode']}"
)
logger.info(
    f"Cache: enabled={config['cache']['enabled']}, "
    f"backend={config['cache']['backend']}, "
    f"ttl={config['cache']['ttl_minutes']}min"
)


# ── 工具函数 ─────────────────────────────────────────────────

def _parse_bool_header(value: Optional[str], default: bool) -> bool:
    """从 HTTP header 解析布尔值。

    Args:
        value: header 字符串值，可为 None。
        default: 默认值。

    Returns:
        解析后的布尔值。
    """
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes")


def _resolve_upstream_url(request: Request, data: Dict[str, Any]) -> str:
    """解析上游 LLM API 地址。

    优先级：X-Provider-URL header > model 字段自动匹配 > 配置。

    Args:
        request: FastAPI 请求对象。
        data: 请求 JSON body。

    Returns:
        上游 API URL。

    Raises:
        HTTPException: 无法解析上游地址时抛出。
    """
    url = request.headers.get("X-Provider-URL")

    if url:
        return url.strip()

    # 尝试从 model 字段自动匹配
    model = data.get("model", "")
    known_models: Dict[str, str] = {
        "deepseek": "https://api.deepseek.com/v1/chat/completions",
        "glm": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "hunyuan": "https://api.hunyuan.cloud.tencent.com/v1/chat/completions",
        "moonshot": "https://api.moonshot.cn/v1/chat/completions",
        "kimi": "https://api.moonshot.cn/v1/chat/completions",
        "minimax": "https://api.minimax.chat/v1/text/chatcompletion_v2",
        "gpt": "https://api.openai.com/v1/chat/completions",
    }
    for prefix, endpoint in known_models.items():
        if model.lower().startswith(prefix):
            logger.info(f"Auto-resolved upstream URL for model '{model}': {endpoint}")
            return endpoint

    raise HTTPException(
        status_code=400,
        detail=(
            "Missing X-Provider-URL header. "
            "Set X-Provider-URL header or use a known model prefix."
        ),
    )


def _build_tokcut_stats(
    orig_input_tokens: int,
    compressed_input_tokens: int,
    output_tokens: int,
    compress_enabled: bool,
    prompt_compress_enabled: bool,
    compress_level: str,
    cache_hit: bool = False,
) -> Dict[str, Any]:
    """构建 tokcut 统计信息字典。

    Args:
        orig_input_tokens: 原始输入 Token 数。
        compressed_input_tokens: 压缩后输入 Token 数。
        output_tokens: 输出 Token 数。
        compress_enabled: 是否启用输出压缩。
        prompt_compress_enabled: 是否启用输入压缩。
        compress_level: 压缩等级。
        cache_hit: 是否为缓存命中。

    Returns:
        tokcut 统计信息字典。
    """
    return {
        "cache_hit": cache_hit,
        "input_tokens_before": orig_input_tokens,
        "input_tokens_after_compression": compressed_input_tokens,
        "output_tokens_approx": output_tokens,
        "output_compression_applied": compress_enabled,
        "prompt_compression_applied": prompt_compress_enabled,
        "compression_level": compress_level,
    }


# ── 路由 ──────────────────────────────────────────────────────


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """主要的聊天补全代理端点，兼容 OpenAI API 格式。

    流程：缓存检查 → 输入压缩 → 注入压缩指令 → 转发 → 后处理 → 返回。

    Headers:
        Authorization: Bearer <API_KEY> - 上游 API 密钥。
        X-Provider-URL: 上游 API 地址（必需）。
        X-Tokcut-Compress: 覆盖输出压缩开关 (true/false)。
        X-Tokcut-Prompt-Compress: 覆盖输入压缩开关 (true/false)。
        X-Tokcut-Cache: 覆盖缓存开关 (true/false)。
        X-Tokcut-Level: 覆盖压缩等级 (lite/full/ultra)。
    """
    start_time = time.time()

    # 解析请求
    data = await request.json()
    messages: List[Dict[str, str]] = data.get("messages", [])
    model: str = data.get("model", "gpt-4")

    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    # 解析上游地址和 API Key
    upstream_url = _resolve_upstream_url(request, data)
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")

    # 动态控制
    compress_enabled = _parse_bool_header(
        request.headers.get("X-Tokcut-Compress"),
        config["compressor"]["enabled"],
    )
    prompt_compress_enabled = _parse_bool_header(
        request.headers.get("X-Tokcut-Prompt-Compress"),
        config["prompt_compressor"]["enabled"],
    )
    cache_enabled = _parse_bool_header(
        request.headers.get("X-Tokcut-Cache"),
        config["cache"]["enabled"],
    )
    compress_level = request.headers.get(
        "X-Tokcut-Level",
        config["compressor"].get("level", "full"),
    )

    if compress_level != config["compressor"].get("level"):
        compressor.level = compress_level
        logger.info(f"Compression level overridden to: {compress_level}")

    # Token 统计
    orig_input_tokens = count_messages_tokens(messages, model)

    # ── 1. 缓存检查 ──
    if cache_enabled:
        try:
            cached = cache.get(messages)
            if cached:
                elapsed_ms = (time.time() - start_time) * 1000
                cached_output_tokens = count_tokens(
                    cached["choices"][0]["message"]["content"]
                )
                logger.info(
                    f"Cache HIT - saved {orig_input_tokens + cached_output_tokens} "
                    f"tokens ({elapsed_ms:.0f}ms)"
                )
                return JSONResponse(
                    content={
                        **cached,
                        "tokcut": _build_tokcut_stats(
                            orig_input_tokens=orig_input_tokens,
                            compressed_input_tokens=orig_input_tokens,
                            output_tokens=cached_output_tokens,
                            compress_enabled=compress_enabled,
                            prompt_compress_enabled=prompt_compress_enabled,
                            compress_level=compress_level,
                            cache_hit=True,
                        ),
                    }
                )
        except Exception as e:
            logger.warning(f"Cache check failed: {e}, continuing without cache")

    # ── 2. 输入压缩 ──
    working_messages = messages
    if prompt_compress_enabled:
        try:
            working_messages = prompt_compressor.compress_messages(messages)
        except Exception as e:
            logger.warning(f"Prompt compression failed: {e}, using original")
            working_messages = messages
    compressed_input_tokens = count_messages_tokens(working_messages, model)

    # ── 3. 输出压缩增强 ──
    if compress_enabled:
        enhanced_messages = compressor.enhance_system_prompt(working_messages)
    else:
        enhanced_messages = working_messages

    # ── 4. 转发请求 ──
    forward_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    req_body = {**data, "messages": enhanced_messages}

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                upstream_url, json=req_body, headers=forward_headers
            )
            if resp.status_code != 200:
                logger.error(
                    f"Upstream error: {resp.status_code} - {resp.text[:500]}"
                )
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=resp.text[:1000],
                )
            response_data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream API timeout")
    except httpx.ConnectError as e:
        raise HTTPException(status_code=502, detail=f"Upstream connection failed: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during upstream request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # ── 5. 后处理压缩 ──
    if compress_enabled and response_data.get("choices"):
        try:
            original_content = response_data["choices"][0]["message"]["content"]
            compressed_content = compressor.post_process(original_content)
            response_data["choices"][0]["message"]["content"] = compressed_content
        except Exception as e:
            logger.warning(f"Post-processing failed: {e}")

    # ── 6. 缓存响应 ──
    if cache_enabled:
        try:
            cache.set(messages, response_data)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

    # ── 7. 统计信息 ──
    output_tokens = response_data.get("usage", {}).get("completion_tokens", 0)
    if not output_tokens and response_data.get("choices"):
        output_tokens = count_tokens(
            response_data["choices"][0]["message"]["content"], model
        )

    response_data["tokcut"] = _build_tokcut_stats(
        orig_input_tokens=orig_input_tokens,
        compressed_input_tokens=compressed_input_tokens,
        output_tokens=output_tokens,
        compress_enabled=compress_enabled,
        prompt_compress_enabled=prompt_compress_enabled,
        compress_level=compress_level,
    )

    elapsed_ms = (time.time() - start_time) * 1000
    logger.info(
        f"Request completed - input: {orig_input_tokens}→{compressed_input_tokens}, "
        f"output: {output_tokens}, {elapsed_ms:.0f}ms"
    )

    if "usage" not in response_data:
        response_data["usage"] = {}
    return JSONResponse(content=response_data)


@app.get("/health")
def health() -> Dict[str, str]:
    """健康检查端点。

    Returns:
        {'status': 'ok'} 表示服务正常运行。
    """
    return {"status": "ok", "version": __version__}


@app.get("/")
def root() -> Dict[str, str]:
    """根路径，返回服务信息。"""
    return {
        "service": "tokcut",
        "version": __version__,
        "docs": "/docs",
    }


# ── 启动入口 ─────────────────────────────────────────────────


def main() -> None:
    """tokcut 代理服务器启动入口。"""
    host = os.getenv("TOKCUT_HOST", "0.0.0.0")
    port = int(os.getenv("TOKCUT_PORT", "8800"))
    log_level = os.getenv("TOKCUT_LOG_LEVEL", "info")

    logger.info(f"Starting tokcut server on {host}:{port}")
    uvicorn.run(
        "tokcut.server:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False,
    )


if __name__ == "__main__":
    main()
