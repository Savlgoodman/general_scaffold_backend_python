# General Scaffold Backend - FastAPI

基于 FastAPI 的后台管理系统后端项目，提供完整的用户管理、权限控制、API日志记录等功能。

## 🚀 快速开始

### 方式一：Docker 开发（推荐）⭐

**Windows:**
```powershell
# 一键启动开发环境
.\start-docker-dev.ps1
```

**Linux/Mac:**
```bash
# 赋予执行权限
chmod +x start-docker-dev.sh

# 一键启动开发环境
./start-docker-dev.sh
```

启动后访问：
- **应用**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **默认账号**: admin / admin123

### 方式二：本地开发

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置数据库（修改 config.yaml）
# 4. 初始化数据库
python init_db.py

# 5. 启动应用
python main.py
```

## 📚 技术栈

- **FastAPI**: 现代化的 Python Web 框架
- **SQLAlchemy**: ORM 框架
- **Alembic**: 数据库迁移管理
- **PostgreSQL**: 关系型数据库
- **Redis**: 缓存和会话存储
- **JWT**: 用户认证
- **Docker**: 容器化部署
- **Pydantic**: 数据验证
- **Loguru**: 日志管理

## 📁 项目结构

```
general_scaffold_backend_python/
├── app/                        # 应用主目录
│   ├── api/v1/                 # API路由
│   ├── core/                   # 核心模块
│   ├── middleware/             # 中间件
│   ├── models/                 # 数据库模型
│   ├── schemas/                # Pydantic Schemas
│   ├── services/               # 业务逻辑层
│   └── utils/                  # 工具函数
├── alembic/                    # 数据库迁移
│   ├── versions/               # 迁移脚本
│   └── env.py                  # 迁移环境配置
├── docker/                     # Docker 配置
├── database/                   # 数据库脚本（旧）
├── docs/                       # 项目文档
├── tests/                      # 测试模块
├── logs/                       # 日志文件目录
├── alembic.ini                 # Alembic 配置
├── config.yaml                 # 配置文件
├── main.py                     # 应用入口
├── requirements.txt            # Python依赖
└── README.md                   # 项目说明
```

## ✨ 功能特性

### 1. 用户系统
- ✅ 用户注册、登录（JWT认证）
- ✅ 用户信息管理（CRUD）
- ✅ 密码加密（bcrypt）
- ✅ 权限控制（普通用户/超级管理员）
- ✅ 用户状态管理

### 2. API日志系统
- ✅ 自动记录所有API调用
- ✅ 记录请求方法、路径、参数、响应状态、响应时长
- ✅ 记录用户信息、IP地址、User Agent
- ✅ 支持多条件查询和分页
- ✅ 日志统计和清理功能

### 3. 中间件系统
- ✅ **认证中间件**：自动验证JWT Token
- ✅ **API日志中间件**：自动记录API调用到数据库
- ✅ **CORS中间件**：跨域支持

### 4. 配置管理
- ✅ 支持 DEV/TEST/PROD 三个环境
- ✅ YAML配置文件 + 环境变量覆盖
- ✅ 配置项包括：数据库、Redis、JWT、日志、CORS等

## 🐳 Docker 环境

### 开发环境特性

- ✅ **代码热更新**：修改代码自动重启应用
- ✅ **数据持久化**：数据库数据保存在 Docker Volume
- ✅ **自动初始化**：自动创建数据库表和管理员账号
- ✅ **调试模式**：启用详细日志和 API 文档

### 生产环境特性

- ✅ **多阶段构建**：优化镜像大小
- ✅ **非 root 用户**：提高安全性
- ✅ **Gunicorn + Uvicorn**：4 个 worker 进程
- ✅ **健康检查**：自动重启失败的服务
- ✅ **独立端口**：避免与开发环境冲突

### Docker 管理命令

详细文档请查看：[docker/README.md](docker/README.md)

**开发环境：**
```bash
# Linux/Mac
./docker/docker-dev.sh start    # 启动
./docker/docker-dev.sh logs     # 查看日志
./docker/docker-dev.sh shell    # 进入容器
./docker/docker-dev.sh stop     # 停止

# Windows
.\docker\docker-dev.ps1 start
.\docker\docker-dev.ps1 logs
.\docker\docker-dev.ps1 shell
.\docker\docker-dev.ps1 stop
```

**生产环境：**
```bash
# 1. 配置环境变量
cp docker/.env.prod.example docker/.env.prod
nano docker/.env.prod

# 2. 启动生产环境
./docker/docker-prod.sh start   # Linux/Mac
.\docker\docker-prod.ps1 start  # Windows
```

## 📖 API 文档

启动应用后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要 API 端点

#### 认证相关
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/refresh` - 刷新Token

#### 用户管理
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新当前用户信息
- `POST /api/v1/users/me/change-password` - 修改密码
- `GET /api/v1/users` - 获取用户列表（管理员）
- `POST /api/v1/users` - 创建用户（管理员）
- `PUT /api/v1/users/{user_id}` - 更新用户（管理员）
- `DELETE /api/v1/users/{user_id}` - 删除用户（管理员）

#### API日志
- `GET /api/v1/logs` - 获取API日志列表（管理员）
- `GET /api/v1/logs/my/logs` - 获取我的API日志
- `GET /api/v1/logs/statistics/summary` - 获取日志统计（管理员）
- `DELETE /api/v1/logs/cleanup` - 清理旧日志（管理员）

## 🗄️ 数据库

### 数据库迁移 (Alembic)

本项目使用 Alembic 管理数据库结构变更。修改模型后通过迁移脚本同步数据库，无需手动 DROP 表。

```bash
# 修改模型后，生成迁移脚本
alembic revision --autogenerate -m "describe_your_change"

# 应用迁移到数据库
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 查看当前版本
alembic current
```

详细文档请查看：[docs/database-migration.md](docs/database-migration.md)

### 数据库表结构

- **users**: 用户表
- **api_logs**: API日志表

## 🧪 测试

```bash
# 运行测试
pytest

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

## 📝 配置说明

### config.yaml

配置文件支持三个环境：`dev`、`test`、`prod`

```yaml
environment: DEV  # 当前环境

dev:
  app:
    name: "General Scaffold Admin System"
    port: 8000
  database:
    host: "localhost"
    port: 5432
    username: "postgres"
    password: "postgres"
    database: "scaffold_dev"
  # ... 更多配置
```

### 环境变量

可以通过环境变量覆盖配置文件：

```bash
export ENVIRONMENT=PROD
export DATABASE_HOST=your-db-host
export DATABASE_PASSWORD=your-db-password
export JWT_SECRET_KEY=your-secret-key
```

## 🔒 安全建议

### 生产环境

1. **修改默认密码**
   - 修改 `docker/.env.prod` 中的所有密码
   - 修改 `config.yaml` 中的 JWT 密钥

2. **使用 HTTPS**
   - 配置 Nginx 反向代理
   - 申请 SSL 证书

3. **限制端口访问**
   - 不要暴露数据库端口到公网
   - 使用防火墙规则

4. **定期备份**
   ```bash
   ./docker/docker-prod.sh backup
   ```

## 📊 性能优化

1. **调整 Worker 数量**
   - 编辑 `docker/docker-compose.prod.yml`
   - 根据 CPU 核心数调整 workers

2. **数据库连接池**
   - 编辑 `config.yaml`
   - 调整 `pool_size` 和 `max_overflow`

3. **Redis 持久化**
   - 配置 AOF 或 RDB

## 🐛 常见问题

### 1. Docker 端口被占用

修改 `docker/docker-compose.dev.yml` 中的端口映射：
```yaml
ports:
  - "8080:8000"  # 改为其他端口
```

### 2. 数据库连接失败

- 检查 PostgreSQL 服务是否启动
- 检查 `config.yaml` 中的数据库配置
- 等待数据库启动完成（通常需要 5-10 秒）

### 3. 代码修改不生效（Docker）

```bash
# 重启容器
./docker/docker-dev.sh restart

# 或重新构建
./docker/docker-dev.sh rebuild
```

## 📚 相关文档

- [数据库迁移指南](docs/database-migration.md)
- [Docker 使用文档](docker/README.md)
- [数据库文档](database/README.md)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请提交 Issue 或联系开发团队。
