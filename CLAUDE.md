# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 FastAPI 的后台管理系统脚手架，集成 RBAC 权限系统，使用 PostgreSQL + Redis + SQLAlchemy。

## 常用命令

```bash
# 启动开发服务器（conda 环境：agent）
python -m uvicorn main:app --host 0.0.0.0 --port 27001 --reload

# 数据库迁移（Alembic）
C:/Users/pengy/miniconda3/envs/agent/Scripts/alembic.exe revision --autogenerate -m "描述"
C:/Users/pengy/miniconda3/envs/agent/Scripts/alembic.exe upgrade head
C:/Users/pengy/miniconda3/envs/agent/Scripts/alembic.exe downgrade -1

# 从 OpenAPI 同步权限到数据库
python script/sync_permissions_from_openapi.py

# 初始化 RBAC 数据（角色、权限、菜单）
python script/init_rbac.py

# 测试
python -m pytest
python -m pytest tests/test_specific.py -v
```

## 架构

### 请求流程
`Request → AuthMiddleware → APILoggerMiddleware → CORS → Router → Endpoint`

全局异常处理器在 `app/core/app.py` 中，捕获所有未处理异常，生产环境不会泄露堆栈信息。

### 分层结构
- **API 层** (`app/api/admin/`)：路由处理、请求校验。所有路由挂在 `/api/admin/` 下。
- **Service 层** (`app/services/`)：业务逻辑。Service 类的静态方法，第一个参数为 `db: Session`。
- **Model 层** (`app/models/`)：SQLAlchemy 模型。继承 `Base`（`app/core/database.py`），自动提供 `created_at`、`updated_at`、`is_deleted` 字段。
- **Schema 层** (`app/schemas/`)：Pydantic 模型，用于请求/响应数据校验。

### RBAC 权限系统
权限系统是项目核心复杂度所在（`admin_rbac_service.py` 约 2000 行）：
- 用户 → 角色 → 权限（标准 RBAC）
- 用户 → 角色 → 菜单（菜单可见性）
- 用户级覆盖：`admin_user_permission_overrides` 和 `admin_user_menu_overrides` 可按用户单独授权/拒绝，绕过角色分配
- 权限匹配使用 `resource_pattern` 字段，支持通配符（如 `/api/admin/users/detail/*`）
- `AuthMiddleware` 通过 `AdminRBACService.check_permission_detail()` 在每个请求上检查权限

### 关键约定
- **统一响应格式**：所有接口返回 `Response(code=, message=, data=)`，定义在 `app/schemas/common.py`
- **软删除**：模型使用 `is_deleted` 布尔字段，不做物理删除
- **配置管理**：`config.yaml` 支持 DEV/TEST/PROD 三环境，`app/core/config.py` 加载，环境变量可覆盖
- **日志**：通过 `app/core/logger.py` 的 `app_logger`（loguru）记录日志
- **数据库会话**：使用 `app/core/database.py` 的 `get_db()` 依赖注入

### 新增功能流程
1. 在 `app/models/` 创建模型，继承 `Base`
2. 在 `app/models/__init__.py`、`app/core/database.py:init_db()`、`alembic/env.py` 中添加模型导入
3. 执行 `alembic revision --autogenerate -m "描述"` 然后 `alembic upgrade head`
4. 在 `app/schemas/` 创建 Schema，`app/services/` 创建 Service，`app/api/admin/` 创建路由
5. 在 `app/api/admin/__init__.py` 中注册路由

### API 文档规范（OpenAPI 代码生成）
- **所有接口必须写清楚功能描述和用途**，前端将直接使用 OpenAPI Schema 自动生成 API 调用代码，实现无感对接
- 路由装饰器必须包含 `summary`（简短功能名）和 `description`（详细用途说明、参数含义、返回值说明）
- Schema 的每个字段使用 `Field(description=...)` 或 `json_schema_extra` 说明含义
- 响应模型使用 `response_model` 明确声明，确保 OpenAPI Schema 完整
- 枚举值在 description 中列出所有可选项及含义

### 数据库
- PostgreSQL + SQLAlchemy ORM（同步模式）
- Alembic 管理迁移，数据库 URL 由 `alembic/env.py` 从 `config.yaml` 动态读取
- 启动时 `Base.metadata.create_all()` 仍会运行（创建新表），但表结构变更应通过 Alembic 迁移
