# 安装指南

> [English](INSTALL.md) | **中文**

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

如果下载失败，可手动下载后放到本地：

```bash
# 设置 Hugging Face 镜像（国内用户推荐）
export HF_ENDPOINT=https://hf-mirror.com

# 或提前下载模型
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

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

## Docker 部署

### Docker 构建

```bash
docker build -t tokcut .
docker run -p 8800:8800 tokcut
```

### Docker Compose

```bash
docker-compose up -d
```

## 常见问题

### Q: sentence-transformers 模型下载很慢怎么办？

设置 Hugging Face 镜像加速：

```bash
# Linux / Mac
export HF_ENDPOINT=https://hf-mirror.com

# Windows PowerShell
$env:HF_ENDPOINT = "https://hf-mirror.com"
```

### Q: 如何切换缓存后端？

在 `config/default.yaml` 中修改：

```yaml
cache:
  backend: sqlite        # 从 memory 改为 sqlite
  sqlite_path: ./cache.db # 数据库文件路径
```

### Q: 如何修改监听端口？

通过环境变量设置：

```bash
# Linux / Mac
export TOKCUT_PORT=9900
python -m tokcut.server

# Windows PowerShell
$env:TOKCUT_PORT = "9900"
python -m tokcut.server
```
