# Docker 文件说明

本目录包含所有 Docker 相关的配置文件。

## 📁 文件说明

### Dockerfile
- `Dockerfile.dev` - 开发环境镜像（支持热更新）
- `Dockerfile.prod` - 生产环境镜像（多阶段构建，优化大小）

### Docker Compose
- `docker-compose.dev.yml` - 开发环境编排配置
- `docker-compose.prod.yml` - 生产环境编排配置

### 管理脚本
- `docker-dev.sh` - 开发环境管理脚本（Linux/Mac）
- `docker-dev.ps1` - 开发环境管理脚本（Windows）
- `docker-prod.sh` - 生产环境管理脚本（Linux/Mac）

### 配置文件
- `.env.prod.example` - 生产环境配置示例

## 🚀 快速启动

### 方式一：使用根目录的快速启动脚本（推荐）

**Windows:**
```powershell
# 在项目根目录执行
.\start-docker-dev.ps1
```

**Linux/Mac:**
```bash
# 在项目根目录执行
chmod +x start-docker-dev.sh
./start-docker-dev.sh
```

### 方式二：使用管理脚本

**开发环境:**
```bash
# Linux/Mac
chmod +x docker/docker-dev.sh
./docker/docker-dev.sh start

# Windows
.\docker\docker-dev.ps1 start
```

**生产环境:**
```bash
# 1. 配置环境变量
cp docker/.env.prod.example docker/.env.prod
nano docker/.env.prod

# 2. 启动
./docker/docker-prod.sh start  # Linux/Mac
.\docker\docker-prod.ps1 start # Windows
```

## 📝 详细文档

完整的使用文档请查看 [README.md](README.md)

## 🔧 环境对比

| 特性 | 开发环境 (DEV) | 生产环境 (PROD) |
|------|---------------|----------------|
| 端口 | 8000 | 8001 |
| 热更新 | ✅ 支持 | ❌ 不支持 |
| 调试模式 | ✅ 开启 | ❌ 关闭 |
| API文档 | ✅ 可访问 | ❌ 禁用 |
| Worker数 | 1 | 4 |
| 镜像大小 | 较大 | 优化后较小 |
| 数据持久化 | ✅ 支持 | ✅ 支持 |
| 自动初始化 | ✅ 支持 | ✅ 支持 |

## 🔥 热更新说明

开发环境支持以下文件的热更新：
- `app/` 目录下的所有 Python 文件
- `main.py`
- `config.yaml`

**注意：** 修改 `requirements.txt` 或 `Dockerfile` 需要重新构建镜像。

## 💡 常用命令

### 开发环境

```bash
# 启动
./docker/docker-dev.sh start

# 查看日志
./docker/docker-dev.sh logs

# 进入容器
./docker/docker-dev.sh shell

# 进入数据库
./docker/docker-dev.sh db-shell

# 停止
./docker/docker-dev.sh stop

# 重新构建
./docker/docker-dev.sh rebuild

# 清理数据
./docker/docker-dev.sh clean
```

### 生产环境

```bash
# 启动
./docker/docker-prod.sh start

# 查看日志
./docker/docker-prod.sh logs

# 备份数据库
./docker/docker-prod.sh backup

# 停止
./docker/docker-prod.sh stop
```

## 🐛 故障排查

### 端口被占用

修改 `docker-compose.*.yml` 中的端口映射：
```yaml
ports:
  - "8080:8000"  # 改为其他端口
```

### 容器无法启动

```bash
# 查看日志
./docker/docker-dev.sh logs

# 重新构建
./docker/docker-dev.sh rebuild
```

### 数据库连接失败

等待数据库启动完成（通常需要 5-10 秒），或查看数据库日志：
```bash
docker logs scaffold_postgres_dev
```

## 📚 相关资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)
