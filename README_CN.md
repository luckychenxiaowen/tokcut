<p align="center">
  <img src="https://raw.githubusercontent.com/luckychenxiaowen/tokcut/main/docs/logo.png" alt="✂️ tokcut" width="160"/>
</p>

<h1 align="center">tokcut ✂️</h1>

<p align="center">
  <strong>多模型通用 Token 节省代理 — 透明削减 30%-65% 的 LLM 调用成本</strong>
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README_CN.md"><strong>中文</strong></a>
</p>

<p align="center">
  <a href="https://github.com/luckychenxiaowen/tokcut/stargazers"><img alt="GitHub Stars" src="https://img.shields.io/github/stars/luckychenxiaowen/tokcut?style=flat-square&color=10b981"></a>
  <a href="https://github.com/luckychenxiaowen/tokcut/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/luckychenxiaowen/tokcut?style=flat-square&color=6366f1"></a>
  <a href="https://pypi.org/project/tokcut"><img alt="PyPI" src="https://img.shields.io/pypi/v/tokcut?style=flat-square&color=f59e0b"></a>
  <a href="https://www.python.org/downloads/"><img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white"></a>
  <a href="https://github.com/luckychenxiaowen/tokcut/actions"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/luckychenxiaowen/tokcut/ci.yml?style=flat-square&branch=main"></a>
</p>

<p align="center">
  <a href="#-快速开始">快速开始</a> •
  <a href="#-什么是-tokcut">什么是 tokcut</a> •
  <a href="#-架构">架构</a> •
  <a href="#-功能特性">功能特性</a> •
  <a href="#-安装">安装</a> •
  <a href="#-使用指南">使用指南</a> •
  <a href="#-性能测试">性能测试</a> •
  <a href="#-参与贡献">参与贡献</a>
</p>

---

## 🎯 什么是 tokcut？

**tokcut** 是一个**轻量级透明代理层**，部署在你的应用与任意兼容 OpenAI 接口的 LLM API 之间。它通过三种正交技术自动削减 **30%-65%** 的 Token 消耗——无需修改任何现有代码。

简单来说，它就是 **LLM 成本的中间件**。只需将 API 客户端指向 `http://localhost:8800/v1`，tokcut 会自动处理剩下的一切。

## 🤔 为什么用 tokcut？

| 痛点 | tokcut 解决方案 |
|---|---|
| 💸 **API 调用成本高** | 跨模型 30%-65% Token 削减 |
| 🔄 **重复提示词** | 语义缓存对相似请求直接返回缓存结果 |
| 📝 **模型输出啰嗦** | 输出压缩器注入 Caveman 风格指令 |
| 📨 **用户输入冗余** | 输入压缩器去除填充词和重复行 |
| 🔧 **需要改代码** | 零改动 —— 完全透明的代理层 |

## 🏗️ 架构

```
┌─────────────┐     ┌─────────────────────────────────┐     ┌──────────────┐
│  你的应用    │────▶│           tokcut 代理            │────▶│  LLM API     │
│  (OpenAI SDK)│     │  ┌───────────────────────────┐  │     │  (DeepSeek,  │
│      │             │  │  1. 语义缓存检查            │  │     │   GLM,       │
│      │             │  │     (sentence-transformers) │  │     │   Kimi, ...) │
│      │             │  │          ↓ 未命中           │  │     │              │
│      │             │  │  2. 输入压缩               │  │     │              │
│      │             │  │     (safe / aggressive)     │  │     │              │
│      │             │  │          ↓                 │  │     │              │
│      │             │  │  3. 输出压缩增强            │  │     │              │
│      │             │  │     (lite / full / ultra)   │  │     │              │
│      │             │  │          ↓                 │  │     │              │
│      │             │  │  4. 转发至上游 API         │──│────▶│              │
│      │             │  │          ↓                 │  │     │              │
│      │             │  │  5. 响应后处理              │◀─│─────│              │
│      │             │  │          ↓                 │  │     │              │
│      │             │  │  6. 缓存 & 返回             │  │     │              │
│      │◀────────────│──│  7. Token 统计              │  │     │              │
└─────────────┘     └─────────────────────────────────┘     └──────────────┘
```

## ✨ 功能特性

### 🗜️ 三层压缩引擎

| 层级 | 方法 | 节省率 | 配置 |
|------|------|--------|------|
| **输出风格** | 注入 Caveman 风格 system prompt + 后处理 | 40%-75% 输出 | `lite` / `full` / `ultra` |
| **输入语义** | 去重复行、过滤填充词、截断 | 20%-75% 输入 | `safe` / `aggressive` |
| **语义缓存** | sentence-transformers 相似度 >0.95 直接返回 | 50%-90%（命中时） | 阈值 + 有效期 |

### 🔌 通用兼容性

完全兼容 OpenAI `/v1/chat/completions` 接口格式 —— 任何使用该协议的 API 均可透明接入：

| 厂商 | API 地址 | 模型示例 |
|------|---------|---------|
| **DeepSeek** | `api.deepseek.com/v1` | `deepseek-chat`, `deepseek-reasoner` |
| **智谱 GLM** | `open.bigmodel.cn/api/paas/v4` | `glm-4`, `glm-4-flash` |
| **MiniMax** | `api.minimax.chat/v1` | `abab6.5s-chat` |
| **腾讯混元** | `api.hunyuan.cloud.tencent.com` | `hunyuan-turbo`, `hunyuan-lite` |
| **月之暗面 Kimi** | `api.moonshot.cn` | `moonshot-v1-8k`, `moonshot-v1-128k` |
| **OpenAI** | `api.openai.com` | `gpt-4o`, `gpt-4-turbo` |
| **... 及其他** | 任意 OpenAI 兼容 API | |

### 🎛️ 动态控制

每个请求可通过 HTTP Header 动态覆盖压缩配置，无需重启服务：

```bash
X-Tokcut-Compress: true/false        # 开关输出压缩
X-Tokcut-Prompt-Compress: true/false  # 开关输入压缩
X-Tokcut-Cache: true/false            # 开关语义缓存
X-Tokcut-Level: lite/full/ultra      # 调整压缩强度
```

### 📊 内置 Token 统计

每个响应都包含 `tokcut` 字段，展示 Token 节省详情：

```json
{
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

### 🛡️ 技术内容保护

压缩时用占位符保护以下内容，压缩完成后还原：

- **代码块**（`` ``` ... ``` ``）
- **行内代码**（`` `...` ``）
- **URL**（`https://...`）
- **版本号**（`3.10.1`）
- **文件路径**

## 🚀 快速开始

### 1. 安装

```bash
pip install tokcut
```

### 2. 启动代理服务

```bash
python -m tokcut.server
# → http://localhost:8800
```

### 3. 配合任意 OpenAI 兼容客户端使用

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
    messages=[{"role": "user", "content": "解释 React 的 useEffect 钩子"}]
)

print(response.choices[0].message.content)
print(response.model_extra["tokcut"])  # 查看 Token 节省数据
```

### 或用 curl

```bash
curl -X POST http://localhost:8800/v1/chat/completions \
  -H "Authorization: Bearer sk-xxxxxxxx" \
  -H "X-Provider-URL: https://api.deepseek.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"解释 React 的 useEffect 钩子"}]}'
```

## 📦 安装

### 从 PyPI 安装

```bash
pip install tokcut
```

### 从源码安装

```bash
git clone https://github.com/luckychenxiaowen/tokcut.git
cd tokcut
pip install -e .
```

### Docker 部署

```bash
docker build -t tokcut .
docker run -p 8800:8800 tokcut
```

或使用 docker-compose：

```bash
docker-compose up -d
```

> 详细安装说明请参阅 [INSTALL_CN.md](INSTALL_CN.md)

## ⚙️ 配置

编辑 `config/default.yaml` 或设置环境变量：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `compressor.enabled` | `true` | 是否启输出风格压缩 |
| `compressor.level` | `full` | 压缩等级：`lite` / `full` / `ultra` |
| `prompt_compressor.enabled` | `false` | 是否启用输入压缩 |
| `prompt_compressor.mode` | `safe` | 模式：`safe`（安全）/ `aggressive`（激进） |
| `cache.enabled` | `true` | 是否启用语义缓存 |
| `cache.backend` | `memory` | 后端：`memory`（内存）/ `sqlite` |
| `cache.similarity_threshold` | `0.95` | 缓存命中阈值（0-1） |
| `cache.ttl_minutes` | `60` | 缓存有效期（分钟） |

### 压缩等级说明

| 等级 | 输出风格 | 预期输出节省 |
|------|---------|-------------|
| `lite` | 省略礼貌用语，保持语法完整 | 40%-50% |
| `full` | 省略冠词代词，仅保留关键词 | 50%-65% |
| `ultra` | 仅输出答案片段 | 65%-75% |

### 输入压缩模式说明

| 模式 | 策略 | 预期输入节省 |
|------|------|-------------|
| `safe` | 去重行 + 过滤填充词 | 20%-40% |
| `aggressive` | 截断70% + 过滤填充词 | 50%-75% |

## 📊 性能测试

我们在 **5个模型 × 5类任务 × 25个测试用例** 上进行了对比测试：

| 模型 | 输入平均节省 | 输出平均节省 | **总节省率** |
|------|------------|------------|------------|
| DeepSeek-V3 | 25% | 58% | **42%** |
| GLM-4 | 28% | 55% | **41%** |
| MiniMax-M2.5 | 22% | 62% | **44%** |
| 腾讯混元 | 30% | 50% | **40%** |
| Kimi | 20% | 60% | **38%** |

> **测试任务**：代码修复、文本总结、知识问答、翻译、客服对话  
> **测试配置**：`full` 级别压缩，关闭输入压缩，内存缓存  
> 完整报告：[`docs/BENCHMARK_REPORT.md`](docs/BENCHMARK_REPORT.md)

### 输出质量保持

尽管采用了激进压缩，由于 `ContentProtector` 保护了代码、URL、数字等技术内容，**所有测试模型的技术准确性保持在 ≥95%**。

## 🛠️ 开发指南

```bash
# 克隆仓库
git clone https://github.com/luckychenxiaowen/tokcut.git
cd tokcut

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 运行基准测试（需配置 API Key）
export DEEPSEEK_API_KEY=sk-xxxx
python tests/benchmarks/benchmark.py
```

## 项目结构

```
tokcut/
├── src/tokcut/          # 核心库
│   ├── server.py        # FastAPI 代理服务
│   ├── compressor.py    # 输出风格压缩器
│   ├── prompt_compressor.py  # 输入语义压缩器
│   ├── cache.py         # 语义缓存（内存 + SQLite）
│   ├── protector.py     # 技术内容保护器
│   ├── token_counter.py # Token 计数工具
│   └── config.py        # 配置管理
├── tests/               # 测试套件
│   └── benchmarks/      # 基准测试脚本
├── config/              # 默认配置文件
├── docs/                # 文档
└── examples/            # 使用示例
```

## 🤝 参与贡献

欢迎贡献！详情请参阅 [CONTRIBUTING_CN.md](CONTRIBUTING_CN.md)。

### 快速贡献流程：
1. Fork 本仓库
2. 创建特性分支：`git checkout -b feat/amazing-feature`
3. 提交更改：`git commit -m 'feat: 添加新功能'`
4. 推送分支：`git push origin feat/amazing-feature`
5. 发起 Pull Request

## 📄 开源协议

tokcut 基于 [MIT License](LICENSE) 开源。详见 `LICENSE` 文件。

## ⭐ Star 历史

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=luckychenxiaowen/tokcut&type=Date&theme=dark"/>
  <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=luckychenxiaowen/tokcut&type=Date"/>
  <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=luckychenxiaowen/tokcut&type=Date"/>
</picture>

<p align="center">
  <sub>为 LLM 社区用心构建。灵感源自 <a href="https://github.com/JuliusBrussee/caveman">Caveman</a>。</sub>
</p>
