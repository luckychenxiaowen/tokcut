# Changelog

All notable changes to tokcut will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-05-02

### Added

- **Core**: FastAPI-based transparent LLM proxy server (`server.py`)
- **Output Compression**: Three-level compression engine (`lite`/`full`/`ultra`) via system prompt injection and post-processing (`compressor.py`)
- **Input Compression**: Two-mode semantic compression (`safe`/`aggressive`) with filler word removal and line deduplication (`prompt_compressor.py`)
- **Semantic Cache**: Request caching using `sentence-transformers` (memory + SQLite backends) with configurable similarity threshold and TTL (`cache.py`)
- **Content Protection**: Placeholder-based protection for code blocks, inline code, URLs, version numbers, and file paths (`protector.py`)
- **Token Counting**: tiktoken-based token estimation for input and output messages (`token_counter.py`)
- **Dynamic Control**: Per-request override via HTTP headers (`X-Tokcut-Compress`, `X-Tokcut-Level`, etc.)
- **Token Analytics**: Built-in statistics in every response showing input/output token savings
- **YAML Configuration**: Centralized config with `config/default.yaml` and programmatic defaults (`config.py`)
- **Benchmark Suite**: Automated comparison testing for 5 models × 5 task types (`tests/benchmarks/benchmark.py`)
- **Documentation**: README.md, USAGE.md, INSTALL.md, CONTRIBUTING.md, docs/BENCHMARK_REPORT.md

### Supported Models

- DeepSeek (V3, Reasoner)
- Zhipu GLM (GLM-4, GLM-4-Flash)
- MiniMax (abab6.5s-chat)
- Tencent Hunyuan (Turbo, Lite)
- Moonshot Kimi (kimi-v1-8k, v1-128k)
- OpenAI (GPT-4o, GPT-4-Turbo)
- Any OpenAI-compatible API
