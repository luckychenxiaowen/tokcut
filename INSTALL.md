# 安装指南

## 环境要求

- Python 3.10+
- pip

## 安装步骤

### 1. 进入项目目录

```bash
cd tokcut
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Linux / Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -e .
```

首次运行时 `sentence-transformers` 会自动下载 `all-MiniLM-L6-v2` 模型（约 80MB），请确保网络通畅。

### 4. （可选）修改配置

编辑 `config/default.yaml` 调整压缩等级和缓存策略：

- `compressor.level`: `lite` / `full` / `ultra`（输出压缩强度）
- `prompt_compressor.mode`: `safe` / `aggressive`（输入压缩模式）
- `cache.backend`: `memory` / `sqlite`（缓存后端）
- `cache.ttl_minutes`: 缓存有效期（分钟）

### 5. 启动服务

```bash
python -m tokcut.server
```

默认监听 `http://localhost:8800`。

### 6. 验证服务

```bash
curl http://localhost:8800/health
```

返回 `{"status":"ok"}` 即表示启动成功。
