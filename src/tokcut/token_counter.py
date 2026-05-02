"""tokcut Token 计数模块。

基于 tiktoken 库进行 Token 估算。
"""

import logging
from typing import Dict, List

import tiktoken

__all__ = ["count_tokens", "count_messages_tokens"]

logger = logging.getLogger(__name__)

# ── 缓存编码器以避免重复创建 ─────────────────────────────────

_encoder_cache: Dict[str, tiktoken.Encoding] = {}


def _get_encoder(model: str = "gpt-4") -> tiktoken.Encoding:
    """获取 tiktoken 编码器（带缓存）。

    Args:
        model: 模型名称，用于匹配编码器。

    Returns:
        tiktoken 编码器实例。
    """
    cache_key = model
    if cache_key not in _encoder_cache:
        try:
            _encoder_cache[cache_key] = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _encoder_cache[cache_key] = tiktoken.get_encoding("gpt2")
    return _encoder_cache[cache_key]


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """计算单段文本的 Token 数量。

    Args:
        text: 输入文本。
        model: 模型名称（用于匹配编码器）。默认 'gpt-4'。

    Returns:
        Token 估算数量。空文本返回 0。
    """
    if not text:
        return 0
    try:
        enc = _get_encoder(model)
        return len(enc.encode(text))
    except Exception as e:
        logger.warning(f"Token counting failed: {e}")
        return 0


def count_messages_tokens(
    messages: List[Dict[str, str]], model: str = "gpt-4"
) -> int:
    """计算消息列表的 Token 总数。

    遍历所有消息的 content 字段并累加 Token 数。

    Args:
        messages: 消息列表，每条包含 'role' 和 'content'。
        model: 模型名称。默认 'gpt-4'。

    Returns:
        所有消息的 Token 总数。
    """
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if content:
            total += count_tokens(content, model)
    return total
