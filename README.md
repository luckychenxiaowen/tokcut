<p align="center">
  <img src="https://raw.githubusercontent.com/luckychenxiaowen/tokcut/main/docs/logo.png" alt="✂️ tokcut" width="160"/>
</p>

<h1 align="center">tokcut ✂️</h1>

<p align="center">
  <strong>Multi-Model Token Saving Proxy — Cut 30%-65% LLM Costs Transparently</strong>
</p>

<p align="center">
  <a href="README.md"><strong>English</strong></a> |
  <a href="README_CN.md">中文</a>
</p>

<p align="center">
  <a href="https://github.com/luckychenxiaowen/tokcut/stargazers"><img alt="GitHub Stars" src="https://img.shields.io/github/stars/luckychenxiaowen/tokcut?style=flat-square&color=10b981"></a>
  <a href="https://github.com/luckychenxiaowen/tokcut/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/luckychenxiaowen/tokcut?style=flat-square&color=6366f1"></a>
  <a href="https://pypi.org/project/tokcut"><img alt="PyPI" src="https://img.shields.io/pypi/v/tokcut?style=flat-square&color=f59e0b"></a>
  <a href="https://www.python.org/downloads/"><img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white"></a>
  <a href="https://github.com/luckychenxiaowen/tokcut/actions"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/luckychenxiaowen/tokcut/ci.yml?style=flat-square&branch=main"></a>
  <a href="https://discord.gg/example"><img alt="Discord" src="https://img.shields.io/badge/discord-join%20chat-7289da?style=flat-square&logo=discord&logoColor=white"></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-what-is-tokcut">What Is tokcut?</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-benchmarks">Benchmarks</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## 🎯 What is tokcut?

**tokcut** is a **lightweight, transparent proxy layer** that sits between your application and any OpenAI-compatible LLM API. It automatically reduces token consumption by **30%-65%** through three orthogonal techniques — without requiring any changes to your existing code.

Think of it as a **"middleware for LLM costs"**. Just point your API client to `http://localhost:8800/v1`, and tokcut handles the rest.

## 🤔 Why tokcut?

| Pain Point | tokcut Solution |
|---|---|
| 💸 **High API costs** | 30%-65% token reduction across all models |
| 🔄 **Repetitive prompts** | Semantic cache returns cached responses for similar queries |
| 📝 **Verbose model outputs** | Output compressor injects "caveman" style instructions |
| 📨 **Redundant user inputs** | Input compressor strips filler words and duplicate lines |
| 🔧 **Code changes required** | Zero — fully transparent OpenAI-compatible proxy |

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────────────────────────┐     ┌──────────────┐
│  Your App   │────▶│           tokcut Proxy           │────▶│  LLM API     │
│  (OpenAI SDK)│     │  ┌───────────────────────────┐  │     │  (DeepSeek,  │
│      │             │  │  1. Semantic Cache Check   │  │     │   GLM,       │
│      │             │  │     (sentence-transformers) │  │     │   Kimi, ...) │
│      │             │  │          ↓ miss            │  │     │              │
│      │             │  │  2. Input Compression      │  │     │              │
│      │             │  │     (safe / aggressive)     │  │     │              │
│      │             │  │          ↓                 │  │     │              │
│      │             │  │  3. Output Compression     │  │     │              │
│      │             │  │     (lite / full / ultra)   │  │     │              │
│      │             │  │          ↓                 │  │     │              │
│      │             │  │  4. Forward to Upstream    │──│────▶│              │
│      │             │  │          ↓                 │  │     │              │
│      │             │  │  5. Post-process Response  │◀─│─────│              │
│      │             │  │          ↓                 │  │     │              │
│      │             │  │  6. Cache & Return         │  │     │              │
│      │◀────────────│──│  7. Token Stats            │  │     │              │
└─────────────┘     └─────────────────────────────────┘     └──────────────┘
```

## ✨ Features

### 🗜️ Three-Layer Compression Engine

| Layer | Method | Savings | Config |
|-------|--------|---------|--------|
| **Output Style** | Inject "caveman" system prompt + post-process | 40%-75% output | `lite` / `full` / `ultra` |
| **Input Semantic** | Deduplicate lines, strip filler words, truncate | 20%-75% input | `safe` / `aggressive` |
| **Semantic Cache** | sentence-transformers similarity >0.95 | 50%-90% (on hit) | threshold + TTL |

### 🔌 Universal Compatibility

Fully compatible with OpenAI `/v1/chat/completions` — works with **any** API that speaks this protocol:

| Provider | API Endpoint | Model Example |
|----------|-------------|---------------|
| **DeepSeek** | `api.deepseek.com/v1` | `deepseek-chat`, `deepseek-reasoner` |
| **Zhipu GLM** | `open.bigmodel.cn/api/paas/v4` | `glm-4`, `glm-4-flash` |
| **MiniMax** | `api.minimax.chat/v1` | `abab6.5s-chat` |
| **Tencent Hunyuan** | `api.hunyuan.cloud.tencent.com` | `hunyuan-turbo`, `hunyuan-lite` |
| **Moonshot (Kimi)** | `api.moonshot.cn` | `moonshot-v1-8k`, `moonshot-v1-128k` |
| **OpenAI** | `api.openai.com` | `gpt-4o`, `gpt-4-turbo` |
| **... and more** | Any OpenAI-compatible API | |

### 🎛️ Dynamic Control

Override compression settings per-request via HTTP headers — no restart needed:

```bash
X-Tokcut-Compress: true/false       # Toggle output compression
X-Tokcut-Prompt-Compress: true/false # Toggle input compression
X-Tokcut-Cache: true/false           # Toggle semantic cache
X-Tokcut-Level: lite/full/ultra     # Adjust compression intensity
```

### 📊 Built-in Token Analytics

Every response includes `tokcut` statistics:

```json
{
  "tokcut": {
    "input_tokens_before": 150,
    "input_tokens_after_compression": 120,
    "output_tokens_approx": 200,
    "output_compression_applied": true,
    "prompt_compression_applied": false,
    "compression_level": "full",
    "cache_hit": false
  }
}
```

### 🛡️ Technical Content Protection

Protected content is wrapped in placeholders before compression and restored after:

- **Code blocks** (`` ``` ... ``` ``)
- **Inline code** (`` `...` ``)
- **URLs** (`https://...`)
- **Version numbers** (`3.10.1`)
- **File paths**

## 🚀 Quick Start

### 1. Install

```bash
pip install tokcut
```

### 2. Start the proxy

```bash
python -m tokcut.server
# → http://localhost:8800
```

### 3. Use with any OpenAI-compatible client

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8800/v1",
    api_key="your-upstream-api-key",
    default_headers={
        "X-Provider-URL": "https://api.deepseek.com/v1/chat/completions"
    }
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "Explain React useEffect"}]
)

print(response.choices[0].message.content)
print(response.model_extra["tokcut"])  # See token savings
```

### Or with curl

```bash
curl -X POST http://localhost:8800/v1/chat/completions \
  -H "Authorization: Bearer sk-xxxxxxxx" \
  -H "X-Provider-URL: https://api.deepseek.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Explain React useEffect"}]}'
```

## 📦 Installation

### From PyPI

```bash
pip install tokcut
```

### From Source

```bash
git clone https://github.com/luckychenxiaowen/tokcut.git
cd tokcut
pip install -e .
```

### With Docker

```bash
docker build -t tokcut .
docker run -p 8800:8800 tokcut
```

Or with docker-compose:

```bash
docker-compose up -d
```

## ⚙️ Configuration

Edit `config/default.yaml` or set environment variables:

| Config Key | Default | Description |
|------------|---------|-------------|
| `compressor.enabled` | `true` | Enable output style compression |
| `compressor.level` | `full` | Compression level: `lite` / `full` / `ultra` |
| `prompt_compressor.enabled` | `false` | Enable input compression |
| `prompt_compressor.mode` | `safe` | Mode: `safe` / `aggressive` |
| `cache.enabled` | `true` | Enable semantic cache |
| `cache.backend` | `memory` | Backend: `memory` / `sqlite` |
| `cache.similarity_threshold` | `0.95` | Cache hit threshold (0-1) |
| `cache.ttl_minutes` | `60` | Cache TTL in minutes |

## 📊 Benchmarks

We tested **5 models × 5 task types × 25 cases**. Here are the real-world savings:

| Model | AVG Input Saved | AVG Output Saved | **Total Saved** |
|-------|----------------|------------------|-----------------|
| DeepSeek-V3 | 25% | 58% | **42%** |
| GLM-4 | 28% | 55% | **41%** |
| MiniMax-M2.5 | 22% | 62% | **44%** |
| Hunyuan | 30% | 50% | **40%** |
| Kimi | 20% | 60% | **38%** |

> **Test Tasks**: Code Fix, Text Summary, Q&A, Translation, Customer Dialogue  
> **Config**: `full` compression, no input compression, memory cache  
> Full report: [`docs/BENCHMARK_REPORT.md`](docs/BENCHMARK_REPORT.md)

### Quality Preservation

Despite aggressive compression, **technical accuracy remains ≥95%** across all tested models, thanks to `ContentProtector` which shields code, URLs, and numbers from compression.

## 🛠️ Development

```bash
# Clone
git clone https://github.com/luckychenxiaowen/tokcut.git
cd tokcut

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run benchmarks (requires API keys)
export DEEPSEEK_API_KEY=sk-xxxx
python tests/benchmarks/benchmark.py
```

## 🤝 Contributing

We welcome contributions! See [`CONTRIBUTING.md`](CONTRIBUTING.md) ([中文](CONTRIBUTING_CN.md)) for guidelines.

### Quick contribution flow:
1. Fork the repository
2. Create a feature branch: `git checkout -b feat/amazing-feature`
3. Commit changes: `git commit -m 'feat: add amazing feature'`
4. Push: `git push origin feat/amazing-feature`
5. Open a Pull Request

## 📄 License

tokcut is open-source under the [MIT License](LICENSE). See `LICENSE` for full text.

## ⭐ Star History

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=luckychenxiaowen/tokcut&type=Date&theme=dark"/>
  <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=luckychenxiaowen/tokcut&type=Date"/>
  <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=luckychenxiaowen/tokcut&type=Date"/>
</picture>

<p align="center">
  <sub>Built with ❤️ for the LLM community. Inspired by <a href="https://github.com/JuliusBrussee/caveman">Caveman</a>.</sub>
</p>
