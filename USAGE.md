# 使用文档

## 快速开始

将任何 OpenAI 兼容的客户端指向 `http://localhost:8800/v1/chat/completions`，并在 Header 中提供：

- `Authorization: Bearer <YOUR_MODEL_API_KEY>`
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

兼容所有 OpenAI `/v1/chat/completions` 接口格式的模型，包括：

| 模型厂商 | API 地址 |
|---------|---------|
| DeepSeek | `https://api.deepseek.com/v1/chat/completions` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4/chat/completions` |
| MiniMax | `https://api.minimax.chat/v1/text/chatcompletion_v2` |
| 腾讯混元 | `https://api.hunyuan.cloud.tencent.com/v1/chat/completions` |
| Kimi (月之暗面) | `https://api.moonshot.cn/v1/chat/completions` |
| OpenAI | `https://api.openai.com/v1/chat/completions` |

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
|------|---------|------------|
| `lite` | 省略礼貌用语，保持完整语法 | 40%-50% |
| `full` | 省略冠词代词，仅保留关键词 | 50%-65% |
| `ultra` | 仅输出答案片段，无完整句子 | 65%-75% |

## 编译模式说明

| 模式 | 策略 | 预期输入节省 |
|------|------|------------|
| `safe` | 去重行 + 过滤填充词 | 20%-40% |
| `aggressive` | 截断70% + 过滤填充词 | 50%-75% |

## Python SDK 集成

如果使用 OpenAI Python SDK：

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
