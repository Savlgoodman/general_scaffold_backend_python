# Design Document

## Overview

本设计文档描述了管理员用户管理增强功能和系统监控模块的实现方案。主要包括两个部分：

1. **管理员用户管理增强**：在现有的 `admin_users.py` API 模块中添加新的端点，用于管理用户权限覆盖、菜单覆盖、查看完整权限和菜单、以及控制用户启用状态。

2. **系统信息监控模块**：创建新的 `system_info.py` API 模块，提供后端系统的监控信息，包括 CPU、内存、网络、Redis 状态以及失败登录统计。

## Architecture

### 系统架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │  admin_users.py      │  │  system_info.py              │ │
│  │  - 权限覆盖管理      │  │  - CPU/内存监控              │ │
│  │  - 菜单覆盖管理      │  │  - 网络统计                  │ │
│  │  - 完整权限查看      │  │  - Redis 监控                │ │
│  │  - 用户状态控制      │  │  - 失败登录统计              │ │
│  └──────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │ admin_rbac_service   │  │  system_info_service         │ │
│  │ admin_user_service   │  │  (新建)                      │ │
│  └──────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Middleware Layer                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  auth.py (需要修改以支持用户状态检查)                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Layer (SQLAlchemy + Redis)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  PostgreSQL  │  │    Redis     │  │  psutil (系统)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

**权限/菜单管理流程：**
```
Client → API → Service → Database → Service → API → Client
```

**系统监控流程：**
```
Client → API → Service → psutil/Redis → Service → API → Client
```

## Components and Interfaces

### 1. Admin Users API 增强 (app/api/admin/admin_users.py)

#### 新增端点

##### 1.1 清除所有权限覆盖
```python
@router.post("/clear-permission-overrides/{user_id}", response_model=Response, summary="清除用户所有权限覆盖")
def clear_permission_overrides(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
)
```

**功能**：清除指定用户的所有权限覆盖记录
**HTTP 方法**：POST
**路径参数**：user_id (int)
**返回**：Response[None]

##### 1.2 清除所有菜单覆盖
```python
@router.post("/clear-menu-overrides/{user_id}", response_model=Response, summary="清除用户所有菜单覆盖")
def clear_menu_overrides(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
)
```

**功能**：清除指定用户的所有菜单覆盖记录
**HTTP 方法**：POST
**路径参数**：user_id (int)
**返回**：Response[None]

##### 1.3 查看完整菜单
```python
@router.get("/complete-menus/{user_id}", response_model=Response[List[AdminMenuTreeNode]], summary="获取用户完整菜单")
def get_complete_menus(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
)
```

**功能**：获取用户的完整菜单（角色菜单并集 + 覆盖）
**HTTP 方法**：GET
**路径参数**：user_id (int)
**返回**：Response[List[AdminMenuTreeNode]]
**复用逻辑**：调用 `AdminRBACService.get_user_menus()`

##### 1.4 查看完整权限（分页）
```python
@router.get("/complete-permissions/{user_id}", response_model=Response[PageResponse[AdminPermissionResponse]], summary="获取用户完整权限列表")
def get_complete_permissions(
    user_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
)
```

**功能**：获取用户的完整权限列表（角色权限并集 + 覆盖），支持分页和关键词搜索
**HTTP 方法**：GET
**路径参数**：user_id (int)
**查询参数**：
- page (int, 必填)
- page_size (int, 必填)
- keyword (str, 可选)
**返回**：Response[PageResponse[AdminPermissionResponse]]

##### 1.5 调整用户启用状态
```python
@router.post("/toggle-status/{user_id}", response_model=Response, summary="调整用户启用状态")
def toggle_user_status(
    user_id: int,
    is_active: bool = Body(..., description="是否启用"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
)
```

**功能**：启用或禁用管理员用户账户
**HTTP 方法**：POST
**路径参数**：user_id (int)
**请求体**：is_active (bool)
**返回**：Response[None]
**限制**：不能禁用自己的账户

### 2. System Info API (app/api/admin/system_info.py - 新建)

#### 端点定义

##### 2.1 系统资源监控
```python
@router.get("/resources", response_model=Response[SystemResourcesResponse], summary="获取系统资源使用情况")
def get_system_resources(
    current_user: AdminUser = Depends(get_current_admin_user)
)
```

**功能**：获取 CPU 和内存使用情况
**HTTP 方法**：GET
**返回**：Response[SystemResourcesResponse]

##### 2.2 网络统计
```python
@router.get("/network", response_model=Response[NetworkStatsResponse], summary="获取网络统计信息")
def get_network_stats(
    current_user: AdminUser = Depends(get_current_admin_user)
)
```

**功能**：获取网络接口统计信息
**HTTP 方法**：GET
**返回**：Response[NetworkStatsResponse]

##### 2.3 Redis 状态
```python
@router.get("/redis/status", response_model=Response[RedisStatusResponse], summary="获取Redis状态")
def get_redis_status(
    current_user: AdminUser = Depends(get_current_admin_user)
)
```

**功能**：获取 Redis 连接状态和基本信息
**HTTP 方法**：GET
**返回**：Response[RedisStatusResponse]

##### 2.4 Redis 键值对查询
```python
@router.get("/redis/keys", response_model=Response[PageResponse[RedisKeyValueResponse]], summary="查询Redis键值对")
def get_redis_keys(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    pattern: Optional[str] = Query(None, description="键名模式"),
    current_user: AdminUser = Depends(get_current_admin_user)
)
```

**功能**：分页查询 Redis 键值对，支持模式匹配
**HTTP 方法**：GET
**查询参数**：
- page (int, 必填)
- page_size (int, 必填)
- pattern (str, 可选，支持 Redis 模式如 "user:*")
**返回**：Response[PageResponse[RedisKeyValueResponse]]

##### 2.5 失败登录统计
```python
@router.get("/failed-logins", response_model=Response[FailedLoginStatsResponse], summary="获取失败登录统计")
def get_failed_login_stats(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
)
```

**功能**：统计失败的登录尝试次数
**HTTP 方法**：GET
**查询参数**：
- start_date (str, 可选)
- end_date (str, 可选)
**返回**：Response[FailedLoginStatsResponse]

### 3. Service Layer 增强

#### 3.1 AdminRBACService 新增方法

```python
@staticmethod
def clear_all_permission_overrides(db: Session, admin_user_id: int) -> bool:
    """清除用户的所有权限覆盖"""
    pass

@staticmethod
def clear_all_menu_overrides(db: Session, admin_user_id: int) -> bool:
    """清除用户的所有菜单覆盖"""
    pass

@staticmethod
def get_user_complete_permissions(
    db: Session,
    admin_user_id: int,
    skip: int,
    limit: int,
    keyword: Optional[str] = None
) -> tuple[List[AdminPermission], int]:
    """获取用户的完整权限列表（分页）"""
    pass
```

#### 3.2 AdminUserService 新增方法

```python
@staticmethod
def toggle_status(db: Session, user_id: int, is_active: bool) -> Optional[AdminUser]:
    """切换用户启用状态"""
    pass
```

#### 3.3 SystemInfoService (新建 app/services/system_info_service.py)

```python
class SystemInfoService:
    """系统信息服务"""
    
    @staticmethod
    def get_system_resources() -> dict:
        """获取系统资源使用情况"""
        pass
    
    @staticmethod
    def get_network_stats() -> dict:
        """获取网络统计信息"""
        pass
    
    @staticmethod
    def get_redis_status() -> dict:
        """获取Redis状态"""
        pass
    
    @staticmethod
    def get_redis_keys(
        skip: int,
        limit: int,
        pattern: Optional[str] = None
    ) -> tuple[List[dict], int]:
        """获取Redis键值对（分页）"""
        pass
    
    @staticmethod
    def get_failed_login_stats(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """获取失败登录统计"""
        pass
```

### 4. Middleware 修改

#### 4.1 Auth Middleware (app/middleware/auth.py)

需要在 token 验证后添加用户状态检查：

```python
# 在验证 token 后添加
# 检查用户是否被禁用
from app.services.admin_user_service import AdminUserService

user = AdminUserService.get_by_id(db, user_id)
if user and not user.is_active:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"code": 401, "message": "账户已被禁用", "data": None}
    )
```

## Data Models

### 新增 Schema 定义

#### SystemResourcesResponse
```python
class SystemResourcesResponse(BaseModel):
    """系统资源响应"""
    cpu_percent: float = Field(..., description="CPU使用率(%)")
    memory_total: int = Field(..., description="总内存(bytes)")
    memory_used: int = Field(..., description="已用内存(bytes)")
    memory_available: int = Field(..., description="可用内存(bytes)")
    memory_percent: float = Field(..., description="内存使用率(%)")
```

#### NetworkStatsResponse
```python
class NetworkStatsResponse(BaseModel):
    """网络统计响应"""
    bytes_sent: int = Field(..., description="发送字节数")
    bytes_recv: int = Field(..., description="接收字节数")
    packets_sent: int = Field(..., description="发送数据包数")
    packets_recv: int = Field(..., description="接收数据包数")
```

#### RedisStatusResponse
```python
class RedisStatusResponse(BaseModel):
    """Redis状态响应"""
    connected: bool = Field(..., description="是否连接")
    db_size: Optional[int] = Field(None, description="数据库大小(键数量)")
    used_memory: Optional[str] = Field(None, description="已用内存")
    used_memory_human: Optional[str] = Field(None, description="已用内存(人类可读)")
    error_message: Optional[str] = Field(None, description="错误信息")
```

#### RedisKeyValueResponse
```python
class RedisKeyValueResponse(BaseModel):
    """Redis键值对响应"""
    key: str = Field(..., description="键名")
    type: str = Field(..., description="值类型")
    value: str = Field(..., description="值内容")
    ttl: Optional[int] = Field(None, description="过期时间(秒)，-1表示永不过期")
```

#### FailedLoginStatsResponse
```python
class FailedLoginStatsResponse(BaseModel):
    """失败登录统计响应"""
    total_count: int = Field(..., description="失败登录总数")
    start_date: Optional[str] = Field(None, description="统计开始日期")
    end_date: Optional[str] = Field(None, description="统计结束日期")
```

## Correctness Properties

*属性是关于系统应该保持为真的特征或行为的陈述——本质上是关于系统应该做什么的正式声明。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### Property 1: 清除权限覆盖的完整性
*对于任何*用户，当清除所有权限覆盖后，该用户不应该有任何活动的权限覆盖记录
**验证需求：Requirements 1.1, 1.2**

### Property 2: 清除菜单覆盖的完整性
*对于任何*用户，当清除所有菜单覆盖后，该用户不应该有任何活动的菜单覆盖记录
**验证需求：Requirements 2.1, 2.2**

### Property 3: 完整菜单计算的正确性
*对于任何*用户，其完整菜单应该等于（所有角色菜单的并集 + ALLOW覆盖 - DENY覆盖）且只包含激活状态的菜单
**验证需求：Requirements 3.1, 3.2, 3.3**

### Property 4: 完整权限计算的正确性
*对于任何*用户，其完整权限应该等于（所有角色权限的并集 + ALLOW覆盖 - DENY覆盖）且只包含激活状态的权限
**验证需求：Requirements 4.2, 4.3, 4.4**

### Property 5: 分页一致性
*对于任何*分页查询，所有页面的项目总和应该等于总数，且不应有重复或遗漏的项目
**验证需求：Requirements 4.1, 4.5**

### Property 6: 用户状态切换的幂等性
*对于任何*用户和状态值，多次设置相同的状态应该产生相同的结果
**验证需求：Requirements 5.1, 5.2**

### Property 7: 禁用用户的认证拒绝
*对于任何*被禁用的用户（is_active = false），认证中间件应该拒绝其访问请求
**验证需求：Requirements 5.3, 5.4**

### Property 8: 自我禁用保护
*对于任何*管理员用户，不应该能够禁用自己的账户
**验证需求：Requirements 5.7**

### Property 9: 系统资源数据的有效性
*对于任何*系统资源查询，返回的 CPU 使用率应该在 0-100 之间，内存使用率应该在 0-100 之间
**验证需求：Requirements 6.1, 6.2**

### Property 10: Redis 键值查询的模式匹配
*对于任何*提供的模式，返回的所有键都应该匹配该模式
**验证需求：Requirements 9.2**

### Property 11: 失败登录统计的准确性
*对于任何*时间范围，失败登录统计应该只计算路径为 '/api/admin/auth/login' 且状态码不为 200 的记录
**验证需求：Requirements 10.2, 10.3**

## Error Handling

### API 层错误处理

1. **用户不存在**：返回 404 状态码，消息 "管理员用户不存在"
2. **自我禁用**：返回 400 状态码，消息 "不能禁用自己的账户"
3. **Redis 连接失败**：返回 503 状态码，消息 "Redis服务不可用"
4. **无效的日期格式**：返回 400 状态码，消息 "日期格式错误，请使用 YYYY-MM-DD"
5. **数据库查询错误**：返回 500 状态码，消息 "服务器内部错误"

### Service 层错误处理

1. **psutil 异常**：捕获并记录日志，返回默认值或错误信息
2. **Redis 异常**：捕获并返回连接状态为 false，包含错误消息
3. **数据库异常**：捕获并回滚事务，抛出 ValueError 供 API 层处理

### Middleware 层错误处理

1. **用户被禁用**：返回 401 状态码，消息 "账户已被禁用"
2. **数据库连接失败**：记录日志，返回 500 状态码

## Testing Strategy

### 单元测试

使用 pytest 框架进行单元测试，重点测试：

1. **Service 层方法**：
   - 清除权限/菜单覆盖的逻辑
   - 完整权限/菜单计算的逻辑
   - 用户状态切换的逻辑
   - 系统信息获取的逻辑

2. **特定示例**：
   - 清除空覆盖列表
   - 用户没有角色时的权限计算
   - Redis 未连接时的处理
   - 无效日期格式的处理

3. **边界情况**：
   - 分页边界（第一页、最后一页、空结果）
   - 大量键值对的 Redis 查询
   - 极端的系统资源值

### 属性测试

使用 Hypothesis 库进行属性测试，每个测试至少运行 100 次迭代：

1. **Property 1-2 测试**：
   - 生成随机用户和覆盖记录
   - 清除后验证无活动覆盖

2. **Property 3-4 测试**：
   - 生成随机角色、权限/菜单、覆盖
   - 验证计算结果的正确性

3. **Property 5 测试**：
   - 生成随机数据集和分页参数
   - 验证分页一致性

4. **Property 6 测试**：
   - 生成随机用户和状态值
   - 多次设置验证幂等性

5. **Property 7-8 测试**：
   - 生成随机用户状态
   - 验证认证行为

6. **Property 9-11 测试**：
   - 生成随机查询参数
   - 验证返回数据的有效性

### 集成测试

1. **API 端点测试**：使用 TestClient 测试所有新增端点
2. **中间件集成测试**：测试用户状态检查与认证流程的集成
3. **数据库集成测试**：测试 Service 层与数据库的交互

### 测试标记

每个属性测试必须包含注释，引用设计文档中的属性：

```python
# Feature: admin-user-management-enhancements, Property 1: 清除权限覆盖的完整性
@given(user_id=st.integers(min_value=1), ...)
def test_clear_permission_overrides_completeness(user_id, ...):
    ...
```

## Implementation Notes

### 依赖库

需要安装 `psutil` 库用于系统监控：
```bash
pip install psutil
```

### Redis 连接

复用现有的 Redis 连接配置（`app/core/redis.py`）

### 日志记录

所有操作应使用 `app_logger` 记录关键操作和错误

### 权限控制

所有新增端点都需要管理员权限，通过 `get_current_admin_user` 依赖注入验证

### 性能考虑

1. **Redis 键查询**：使用 SCAN 命令而不是 KEYS 命令，避免阻塞
2. **分页查询**：使用数据库索引优化查询性能
3. **系统监控**：考虑添加缓存，避免频繁调用 psutil

### 安全考虑

1. **敏感信息**：Redis 值内容超过 1000 字符时截断
2. **权限验证**：所有端点都需要认证
3. **输入验证**：使用 Pydantic 模型验证所有输入参数
