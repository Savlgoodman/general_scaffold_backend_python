# General Scaffold Backend - FastAPI

基于 FastAPI 的后台管理系统后端项目，提供完整的用户管理、权限控制、API 日志记录等功能。

## 技术栈

-   **FastAPI**: 现代化的 Python Web 框架
-   **SQLAlchemy**: ORM 框架
-   **PostgreSQL**: 关系型数据库
-   **Redis**: 缓存和会话存储
-   **JWT**: 用户认证
-   **Docker**: 容器化部署
-   **Pydantic**: 数据验证
-   **Loguru**: 日志管理

## 项目结构

```
general_scaffold_backend_python/
├── app/                        # 应用主目录
│   ├── api/                    # API路由
│   │   ├── v1/                 # API v1版本
│   │   │   ├── auth.py         # 认证相关API
│   │   │   ├── users.py        # 用户管理API
│   │   │   └── api_logs.py     # API日志API
│   │   └── __init__.py
│   ├── core/                   # 核心模块
│   │   ├── app.py              # FastAPI应用创建
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   ├── redis.py            # Redis连接
│   │   ├── security.py         # 安全相关（JWT、密码加密）
│   │   └── logger.py           # 日志配置
│   ├── middleware/             # 中间件
│   │   ├── auth.py             # 认证中间件
│   │   └── api_logger.py       # API日志中间件
│   ├── models/                 # 数据库模型
│   │   ├── user.py             # 用户模型
│   │   └── api_log.py          # API日志模型
│   ├── schemas/                # Pydantic Schemas
│   │   ├── user.py             # 用户Schema
│   │   ├── api_log.py          # API日志Schema
│   │   └── common.py           # 通用Schema
│   ├── services/               # 业务逻辑层
│   │   ├── user_service.py     # 用户服务
│   │   └── api_log_service.py  # API日志服务
│   └── utils/                  # 工具函数
│       └── dependencies.py     # 依赖注入
├── logs/                       # 日志文件目录
├── config.yaml                 # 配置文件
├── main.py                     # 应用入口
├── requirements.txt            # Python依赖
├── Dockerfile                  # Docker镜像构建文件
├── docker-compose.yml          # Docker Compose配置
├── .gitignore                  # Git忽略文件
└── README.md                   # 项目说明

```

## 功能特性

### 1. 用户系统

-   ✅ 用户注册、登录
-   ✅ JWT Token 认证
-   ✅ 用户信息管理（CRUD）
-   ✅ 密码修改
-   ✅ 用户权限控制（普通用户/超级管理员）
-   ✅ 用户状态管理（激活/禁用）

### 2. API 日志系统

-   ✅ 自动记录所有 API 请求
-   ✅ 记录请求方法、路径、参数
-   ✅ 记录响应状态码、响应时长
-   ✅ 记录用户信息、IP 地址、User Agent
-   ✅ 支持多条件查询和分页
-   ✅ 日志统计功能
-   ✅ 旧日志清理功能

### 3. 中间件

-   ✅ 认证中间件：JWT Token 验证
-   ✅ API 日志中间件：自动记录 API 调用
-   ✅ CORS 中间件：跨域支持

### 4. 配置管理

-   ✅ 多环境配置（DEV/TEST/PROD）
-   ✅ YAML 配置文件
-   ✅ 环境变量覆盖
-   ✅ 配置热加载

## 快速开始

### 1. 环境要求

-   Python 3.11+
-   PostgreSQL 15+
-   Redis 7+
-   Docker & Docker Compose（可选）

### 2. 本地开发

#### 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 配置数据库

1. 创建 PostgreSQL 数据库：

```sql
CREATE DATABASE scaffold_dev;
```

2. 修改 `config.yaml` 中的数据库配置

#### 运行应用

```bash
# 直接运行
python main.py

# 或使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问：

-   API 文档：http://localhost:8000/docs
-   ReDoc 文档：http://localhost:8000/redoc
-   健康检查：http://localhost:8000/health

### 3. Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down

# 停止并删除数据
docker-compose down -v
```

## API 文档

### 认证相关

#### 用户登录

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

#### 用户注册

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "full_name": "New User"
}
```

#### 刷新 Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your_refresh_token"
}
```

### 用户管理

#### 获取当前用户信息

```http
GET /api/v1/users/me
Authorization: Bearer {access_token}
```

#### 获取用户列表（管理员）

```http
GET /api/v1/users?page=1&page_size=20&keyword=admin
Authorization: Bearer {access_token}
```

#### 创建用户（管理员）

```http
POST /api/v1/users
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "full_name": "Test User",
  "is_superuser": false
}
```

### API 日志

#### 获取 API 日志列表（管理员）

```http
GET /api/v1/logs?page=1&page_size=20&method=GET&path=/api/users
Authorization: Bearer {access_token}
```

#### 获取我的 API 日志

```http
GET /api/v1/logs/my/logs?page=1&page_size=20
Authorization: Bearer {access_token}
```

#### 获取日志统计（管理员）

```http
GET /api/v1/logs/statistics/summary
Authorization: Bearer {access_token}
```

## 配置说明

### config.yaml

配置文件支持三个环境：`dev`、`test`、`prod`

主要配置项：

-   `environment`: 当前环境（DEV/TEST/PROD）
-   `app`: 应用配置（名称、端口、调试模式等）
-   `database`: 数据库配置
-   `redis`: Redis 配置
-   `jwt`: JWT 认证配置
-   `logging`: 日志配置
-   `cors`: 跨域配置
-   `api_log`: API 日志配置

### 环境变量

可以通过环境变量覆盖配置文件：

```bash
export ENVIRONMENT=PROD
export DATABASE_HOST=your-db-host
export DATABASE_PASSWORD=your-db-password
export JWT_SECRET_KEY=your-secret-key
```

## 开发指南

### 添加新的 API 端点

1. 在 `app/api/v1/` 创建新的路由文件
2. 在 `app/api/v1/__init__.py` 中注册路由
3. 在 `app/services/` 创建对应的服务层
4. 在 `app/models/` 创建数据库模型（如需要）
5. 在 `app/schemas/` 创建 Pydantic Schema

### 数据库迁移

当前项目使用 SQLAlchemy 的 `create_all()` 方法创建表。

如需使用 Alembic 进行数据库迁移：

```bash
# 安装alembic
pip install alembic

# 初始化
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 代码规范

-   使用 Black 格式化代码
-   使用 Flake8 检查代码质量
-   使用 MyPy 进行类型检查

```bash
# 格式化代码
black app/

# 检查代码
flake8 app/

# 类型检查
mypy app/
```

## 测试

```bash
# 运行测试
pytest

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

## 生产部署建议

1. **安全配置**

    - 修改 `config.yaml` 中的 `jwt.secret_key`
    - 使用强密码
    - 配置防火墙规则
    - 启用 HTTPS

2. **性能优化**

    - 调整数据库连接池大小
    - 配置 Redis 持久化
    - 使用 Nginx 反向代理
    - 启用 Gzip 压缩

3. **监控和日志**

    - 配置日志轮转
    - 集成监控系统（如 Prometheus）
    - 配置告警规则

4. **备份**
    - 定期备份数据库
    - 备份配置文件
    - 备份日志文件

## 常见问题

### 1. 数据库连接失败

检查：

-   PostgreSQL 服务是否启动
-   数据库配置是否正确
-   网络连接是否正常

### 2. Redis 连接失败

检查：

-   Redis 服务是否启动
-   Redis 配置是否正确
-   防火墙是否开放端口

### 3. JWT Token 无效

检查：

-   Token 是否过期
-   secret_key 是否正确
-   Token 格式是否正确

## 许可证

MIT License

## 联系方式

如有问题，请提交 Issue 或联系开发团队。
