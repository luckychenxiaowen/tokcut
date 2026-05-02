# 参与贡献指南

> [English](CONTRIBUTING.md) | **中文**

感谢你对 tokcut 的贡献兴趣！🎉

tokcut 是一个透明的多模型 Token 节省代理。我们欢迎各种形式的贡献——Bug 报告、功能请求、文档改进、代码修改和基准测试报告。

## 目录

- [行为准则](#行为准则)
- [开始上手](#开始上手)
- [开发流程](#开发流程)
- [Pull Request 规范](#pull-request-规范)
- [代码风格](#代码风格)
- [测试](#测试)
- [文档](#文档)
- [发布流程](#发布流程)

## 行为准则

本项目遵守 [贡献者公约行为准则](CODE_OF_CONDUCT.md)。参与即表示同意遵守该准则。

## 开始上手

### 环境要求

- Python 3.10+
- Git
- 虚拟环境（推荐）

### 开发环境搭建

```bash
# 1. Fork 并克隆
git clone https://github.com/你的用户名/tokcut.git
cd tokcut

# 2. 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. 开发模式安装（含开发依赖）
pip install -e ".[dev]"

# 4. 运行测试验证环境
pytest tests/ -v
```

> **国内用户提示**：首次安装时 `sentence-transformers` 会下载模型文件，建议先设置 Hugging Face 镜像：
> ```bash
> export HF_ENDPOINT=https://hf-mirror.com
> ```

## 开发流程

1. **找到或创建 Issue** —— 在 [GitHub Issues](https://github.com/luckychenxiaowen/tokcut/issues) 中查找已有任务或创建新 Issue。
2. **创建特性分支**：

   ```bash
   git checkout -b feat/功能名称
   # 或者: fix/问题描述, docs/更新内容, perf/优化名称
   ```

3. **进行修改** —— 编写代码、添加测试、更新文档。
4. **运行完整测试套件**：

   ```bash
   pytest tests/ -v --cov=src/tokcut --cov-report=term-missing
   ```

5. **使用约定式提交**：

   ```bash
   git commit -m "feat: 添加流式响应支持"
   git commit -m "fix: 修复 sqlite 缓存空值异常"
   git commit -m "docs: 更新 USAGE_CN.md 添加流式示例"
   ```

6. **推送并创建 PR**：

   ```bash
   git push origin feat/功能名称
   ```

## Pull Request 规范

- **保持 PR 聚焦** —— 每个 PR 只包含一个功能或修复。
- **关联 Issue** —— 用 `Closes #123` 或 `Related to #456` 引用相关问题。
- **添加测试** —— 新功能必须包含测试，Bug 修复应包含回归测试。
- **更新文档** —— 如果改动影响用户行为，请同步更新相关文档。
- **通过 CI** —— 所有检查必须在 review 前通过。
- **等待审核** —— 维护者会审核你的 PR，请及时响应反馈。

### PR 标题规范

使用[约定式提交](https://www.conventionalcommits.org/zh-hans/)格式：

```
feat: 描述        # 新功能
fix: 描述         # Bug 修复
docs: 描述        # 仅文档更新
refactor: 描述    # 代码重构
perf: 描述        # 性能优化
test: 描述        # 添加测试
chore: 描述       # 维护任务
```

## 代码风格

我们使用 **Ruff** 进行代码检查和格式化。配置在 `pyproject.toml` 中。

```bash
# 检查代码风格
ruff check src/ tests/

# 自动修复
ruff check --fix src/ tests/

# 格式化代码
ruff format src/ tests/
```

### 风格指南

- **类型注解** —— 所有公开函数必须使用类型注解。
- **文档字符串** —— 公开模块和函数使用 Google 风格 docstring。
- **行长度** —— 最大 100 字符。
- **导入排序** —— 使用 `ruff` 自动排序（标准库 → 第三方 → 本地）。

## 测试

```bash
# 运行所有测试
pytest tests/

# 带覆盖率
pytest tests/ --cov=src/tokcut --cov-report=html

# 运行特定测试文件
pytest tests/test_compressor.py -v

# 详细输出
pytest tests/ -v -s
```

### 编写测试

- 测试放在 `tests/` 目录，文件名以 `test_` 为前缀，对应模块名称。
- 使用 `pytest` fixtures 创建可复用的测试数据。
- 单元测试中 mock 外部 API 调用。
- 包含管道流程的集成测试。

## 文档

- **README.md** — 项目概述、快速开始、功能特性（英文）。
- **README_CN.md** — 中文版项目概述。
- **USAGE.md / USAGE_CN.md** — 详细使用文档。
- **INSTALL.md / INSTALL_CN.md** — 各平台安装指南。
- **CONTRIBUTING.md / CONTRIBUTING_CN.md** — 贡献指南。
- **CHANGELOG.md** — 版本发布历史。

添加新功能时，请同步更新中英文文档。

## 项目结构

```
tokcut/
├── src/tokcut/          # 核心库
│   ├── server.py        # FastAPI 代理服务
│   ├── compressor.py    # 输出风格压缩器
│   ├── prompt_compressor.py  # 输入语义压缩器
│   ├── cache.py         # 语义缓存层
│   ├── protector.py     # 技术内容保护器
│   ├── token_counter.py # Token 计数工具
│   └── config.py        # 配置管理
├── tests/               # 测试套件
│   └── benchmarks/      # 基准测试脚本
├── config/              # 默认配置
├── docs/                # 文档
└── examples/            # 使用示例
```

## 发布流程

发布由维护者管理：

1. 更新 `src/tokcut/__version__.py` 和 `pyproject.toml` 中的版本号。
2. 更新 `CHANGELOG.md`。
3. 创建 git 标签：`git tag v0.1.0`。
4. 推送标签：`git push --tags`。
5. CI 流水线将自动构建并发布到 PyPI。

## 有问题？

- 创建 [GitHub Discussion](https://github.com/luckychenxiaowen/tokcut/discussions)
- 发送邮件给维护者

感谢你的贡献！🚀
