# Docker 路径修复总结

## 问题描述

将 `docker-compose.dev.yml` 和 `docker-compose.prod.yml` 文件移动到 `./docker` 目录后，出现了路径引用错误，导致 Docker 构建失败。

## 错误信息

```
failed to solve: failed to compute cache key: failed to calculate checksum of ref: "/requirements.txt": not found
```

## 根本原因

当 `docker-compose.yml` 文件在 `./docker` 子目录中时，其中的相对路径 `.` 指向的是 `./docker` 目录，而不是项目根目录。这导致：

1. **构建上下文错误**：`context: .` 指向 `./docker` 而不是项目根目录
2. **Dockerfile 路径错误**：`dockerfile: Dockerfile.dev` 在 `./docker` 目录中找不到
3. **Volume 挂载路径错误**：`./app` 指向 `./docker/app` 而不是项目根目录的 `./app`

## 已修复的文件

### 1. `docker/docker-compose.dev.yml`

**修复内容：**

```yaml
# 修复前
app-dev:
  build:
    context: .
    dockerfile: Dockerfile.dev
  volumes:
    - ./app:/app/app
    - ./main.py:/app/main.py
    - ./config.yaml:/app/config.yaml
    - ./init_db.py:/app/init_db.py
    - ./logs:/app/logs

# 修复后
app-dev:
  build:
    context: ..              # 指向父目录（项目根目录）
    dockerfile: docker/Dockerfile.dev  # 相对于项目根目录的路径
  volumes:
    - ../app:/app/app        # 相对于 docker 目录的父目录
    - ../main.py:/app/main.py
    - ../config.yaml:/app/config.yaml
    - ../init_db.py:/app/init_db.py
    - ../logs:/app/logs
```

### 2. `docker/docker-compose.prod.yml`

**修复内容：**

```yaml
# 修复前
app-prod:
  build:
    context: .
    dockerfile: Dockerfile.prod
  volumes:
    - ./logs:/app/logs

# 修复后
app-prod:
  build:
    context: ..              # 指向父目录（项目根目录）
    dockerfile: docker/Dockerfile.prod  # 相对于项目根目录的路径
  volumes:
    - ../logs:/app/logs      # 相对于 docker 目录的父目录
```

### 3. `start-docker-dev.ps1`

**修复内容：**
- 重新保存为正确的 UTF-8 编码，解决中文字符乱码问题
- 文件内容保持不变，路径引用正确（`docker/docker-compose.dev.yml`）

### 4. `docker/Dockerfile.dev`

**优化内容：**
- 添加了国内镜像源配置注释（可选启用）
- 用于解决网络不稳定时的包下载问题

## 路径说明

### 当前目录结构

```
general_scaffold_backend_python/
├── app/                          # 应用代码
├── docker/                       # Docker 配置目录
│   ├── docker-compose.dev.yml   # 开发环境配置
│   ├── docker-compose.prod.yml  # 生产环境配置
│   ├── Dockerfile.dev           # 开发环境镜像
│   ├── Dockerfile.prod          # 生产环境镜像
│   ├── docker-dev.ps1           # 开发环境管理脚本（Windows）
│   ├── docker-dev.sh            # 开发环境管理脚本（Linux/Mac）
│   └── docker-prod.sh           # 生产环境管理脚本
├── main.py                       # 应用入口
├── requirements.txt              # Python 依赖
├── config.yaml                   # 配置文件
├── init_db.py                    # 数据库初始化脚本
└── start-docker-dev.ps1         # 快速启动脚本

```

### 路径解析规则

1. **docker-compose.yml 中的路径**：
   - `context: ..` → 指向 `general_scaffold_backend_python/`
   - `dockerfile: docker/Dockerfile.dev` → 指向 `general_scaffold_backend_python/docker/Dockerfile.dev`
   - `../app` → 指向 `general_scaffold_backend_python/app/`

2. **启动脚本中的路径**：
   - `docker-compose -f docker/docker-compose.dev.yml` → 从项目根目录执行

## 使用方法

### 开发环境

**Windows:**
```powershell
# 快速启动（推荐）
.\start-docker-dev.ps1

# 或使用管理脚本
.\docker\docker-dev.ps1 start
.\docker\docker-dev.ps1 logs
.\docker\docker-dev.ps1 stop
```

**Linux/Mac:**
```bash
# 快速启动
./start-docker-dev.sh

# 或使用管理脚本
./docker/docker-dev.sh start
./docker/docker-dev.sh logs
./docker/docker-dev.sh stop
```

### 生产环境

**Linux/Mac:**
```bash
./docker/docker-prod.sh start
./docker/docker-prod.sh logs
./docker/docker-prod.sh backup
```

## 验证修复

修复后，Docker 能够：
1. ✅ 正确找到项目根目录的 `requirements.txt`
2. ✅ 正确找到 `docker/Dockerfile.dev`
3. ✅ 正确挂载项目文件到容器
4. ✅ 成功构建和启动容器

## 常见问题

### Q1: 如果遇到网络下载失败怎么办？

**A:** 这是临时网络问题，有两种解决方案：

1. **重试构建**（推荐）：
   ```powershell
   .\start-docker-dev.ps1
   ```

2. **启用国内镜像源**：
   编辑 `docker/Dockerfile.dev`，取消注释这一行：
   ```dockerfile
   RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources
   ```

### Q2: 如何清理并重新构建？

```powershell
# Windows
.\docker\docker-dev.ps1 clean
.\docker\docker-dev.ps1 rebuild

# Linux/Mac
./docker/docker-dev.sh clean
./docker/docker-dev.sh rebuild
```

### Q3: 如何查看容器日志？

```powershell
# Windows
.\docker\docker-dev.ps1 logs

# Linux/Mac
./docker/docker-dev.sh logs
```

## 修复日期

2025-12-22

## 修复人员

AI Assistant (Claude 4.5 Sonnet)




