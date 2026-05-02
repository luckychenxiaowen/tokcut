# 使用文档

> [English](USAGE.md) | **中文**

## 快速开始

将任何 OpenAI 兼容的客户端指向 `http://localhost:8800/v1/chat/completions`，并在 Header 中提供：

- `Authorization: Bearer <你的模型 API Key>`
- `X-Provider-URL: https://api.deepseek.com/v1/chat/completions`（或其他模型地址）

### curl 示例

```bash
curl -X POST http://localhost:8800/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxx" \
  -H "X-Provider-URL: https://api.deepseek.com/v1/chat/completions" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role":"user","content":"解释 React 的 useEffect 钩子"}]
  }'
```

## 支持的模型

兼容所有 OpenAI `/v1/chat/completions` 接口格式的模型：

| 模型厂商 | API 地址 |
|---------|---------|
| DeepSeek | `https://api.deepseek.com/v1/chat/completions` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4/chat/completions` |
| MiniMax | `https://api.minimax.chat/v1/text/chatcompletion_v2` |
| 腾讯混元 | `https://api.hunyuan.cloud.tencent.com/v1/chat/completions` |
| Kimi（月之暗面） | `https://api.moonshot.cn/v1/chat/completions` |
| OpenAI | `https://api.openai.com/v1/chat/completions` |

> **提示**：v0.1.0 起 tokcut 支持自动识别模型名称匹配上游 API 地址。如果 Header 中未指定 `X-Provider-URL`，tokcut 会根据 `model` 字段自动匹配已知的 API 地址。

## 动态控制开关

可在请求 Header 中添加以下字段覆盖默认配置：

| Header | 值 | 说明 |
|--------|-----|------|
| `X-Tokcut-Compress` | `true` / `false` | 开启/关闭输出风格压缩 |
| `X-Tokcut-Prompt-Compress` | `true` / `false` | 开启/关闭输入压缩 |
| `X-Tokcut-Cache` | `true` / `false` | 开启/关闭语义缓存 |
| `X-Tokcut-Level` | `lite` / `full` / `ultra` | 调整压缩等级 |

### 动态控制示例

```bash
# 仅使用 ultra 级别输出压缩，关闭缓存和输入压缩
curl -X POST http://localhost:8800/v1/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -H "X-Provider-URL: https://api.deepseek.com/v1/chat/completions" \
  -H "X-Tokcut-Compress: true" \
  -H "X-Tokcut-Level: ultra" \
  -H "X-Tokcut-Prompt-Compress: false" \
  -H "X-Tokcut-Cache: false" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"解释 React"}]}'
```

## 查看统计

每个响应 JSON 中包含 `tokcut` 字段，记录了输入/输出 Token 的前后对比：

```json
{
  "choices": [...],
  "usage": {...},
  "tokcut": {
    "cache_hit": false,
    "input_tokens_before": 150,
    "input_tokens_after_compression": 120,
    "output_tokens_approx": 200,
    "output_compression_applied": true,
    "prompt_compression_applied": false,
    "compression_level": "full"
  }
}
```

## 压缩等级说明

| 等级 | 输出风格 | 预期输出节省 |
|------|---------|-------------|
| `lite` | 省略礼貌用语，保持完整语法 | 40%-50% |
| `full` | 省略冠词代词，仅保留关键词 | 50%-65% |
| `ultra` | 仅输出答案片段，无完整语句 | 65%-75% |

## 输入压缩模式说明

| 模式 | 策略 | 预期输入节省 | 适用场景 |
|------|------|-------------|---------|
| `safe` | 去重行 + 过滤填充词 | 20%-40% | 一般对话、翻译 |
| `aggressive` | 截断70% + 过滤填充词 | 50%-75% | 长文档、批量处理 |

## Python SDK 集成

### 使用 OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8800/v1",
    api_key="sk-xxxxxxxxxxxx",
    default_headers={
        "X-Provider-URL": "https://api.deepseek.com/v1/chat/completions"
    }
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "解释 React 的 useEffect 钩子"}]
)

print(response.choices[0].message.content)
# 查看 tokcut 统计
print(response.model_extra.get("tokcut"))
```

### 动态切换压缩配置

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8800/v1",
    api_key="sk-xxx",
    default_headers={
        "X-Provider-URL": "https://api.deepseek.com/v1/chat/completions",
        "X-Tokcut-Level": "ultra",      # 使用极简压缩
        "X-Tokcut-Cache": "false"        # 关闭缓存
    }
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "Python 和 JavaScript 的主要区别"}]
)
```

## 部署建议

### 生产环境

```bash
# 使用 SQLite 持久化缓存
# 编辑 config/default.yaml
cache:
  enabled: true
  backend: sqlite
  ttl_minutes: 120
```

### 高并发场景

```bash
# 使用 Docker Compose + 多实例
docker-compose up -d --scale tokcut=3

# 前方建议放置 nginx 做负载均衡
```

## 环境变量参考

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TOKCUT_HOST` | `0.0.0.0` | 监听地址 |
| `TOKCUT_PORT` | `8800` | 监听端口 |
| `TOKCUT_LOG_LEVEL` | `info` | 日志级别 |
| `TOKCUT_CONFIG_PATH` | - | 配置文件路径 |

## 常见问题

### Q: 压缩后回答质量会下降吗？

经过 25 个测试用例验证，技术内容（代码、URL、数字）被 `ContentProtector` 保护后不会被压缩，技术准确性保持在 95% 以上。

### Q: 如何仅使用缓存功能，不压缩输出？

```bash
curl ... \
  -H "X-Tokcut-Compress: false" \
  -H "X-Tokcut-Cache: true"
```

### Q: 语义缓存命中率怎么样？

取决于请求的相似度。重复或高度相似的请求（如"帮我解释 XXX"类问题），命中率可达 60%-80%。完全不同的请求则不会命中。

### Q: 上游 API 报错怎么办？

服务器会透传错误状态码和错误信息。可以通过设置 `TOKCUT_LOG_LEVEL=debug` 查看详细日志。
