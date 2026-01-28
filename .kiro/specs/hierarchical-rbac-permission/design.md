# Design Document: Hierarchical RBAC Permission System

## Overview

本设计文档描述了层级化RBAC权限系统的实现方案。该系统通过引入通配符模式、allow/deny机制和优先级控制，实现了灵活的API权限管理。系统的核心设计理念是：

1. **通配符模式**：使用 `/system/logs/*` 这样的模式来表达权限组，简化权限分配
2. **Effect机制**：支持 allow 和 deny 两种效果，通过优先级解决冲突
3. **自动同步**：从FastAPI的OpenAPI规范自动提取和同步API权限
4. **向后兼容**：保持与现有接口和数据结构的兼容性

系统采用Python + FastAPI + SQLAlchemy技术栈，遵循项目现有的架构规范。

## Architecture

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐   ┌──────────────┐ │
│  │   API Layer  │─────▶│Service Layer │──▶│  Data Layer  │ │
│  │              │      │              │   │              │ │
│  │ - permissions│      │ - permission │   │ - AdminPerm  │ │
│  │ - roles      │      │   _service   │   │ - AdminRole  │ │
│  │              │      │ - rbac       │   │   Permission │ │
│  └──────────────┘      │   _service   │   └──────────────┘ │
│                        └──────────────┘                     │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Permission Check Middleware                   │   │
│  │  - Extract request path & method                      │   │
│  │  - Match against resource patterns                    │   │
│  │  - Apply priority & effect rules                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  PostgreSQL DB   │
                    │                  │
                    │ - admin_         │
                    │   permissions    │
                    │ - admin_role_    │
                    │   permissions    │
                    └──────────────────┘

External:
┌──────────────┐
│ Sync Script  │──▶ Reads FastAPI routes ──▶ Updates DB
└──────────────┘
```

### 核心组件

1. **数据模型层**
   - `AdminPermission`: 权限表，支持通配符和分组
   - `AdminRolePermission`: 角色权限关联表，支持effect和priority

2. **服务层**
   - `AdminPermissionService`: 权限CRUD操作
   - `AdminRBACService`: 权限检查和验证逻辑
   - `PermissionSyncService`: OpenAPI同步服务

3. **API层**
   - `/permissions/*`: 权限管理接口
   - `/roles/*/permissions`: 角色权限管理接口

4. **中间件**
   - `PermissionCheckMiddleware`: 运行时权限验证

5. **工具脚本**
   - `sync_permissions_from_openapi.py`: 权限同步脚本

## Components and Interfaces

### 1. 数据模型组件

#### AdminPermission (权限表)

```python
class AdminPermission(Base):
    """管理员权限表 - 支持通配符和分组"""
    __tablename__ = "admin_permissions"
    
    id: int                          # 权限ID
    name: str                        # 权限名称
    resource_pattern: str            # 资源模式，支持通配符
    method: str                      # HTTP方法
    group_key: str                   # 分组标识
    group_name: str                  # 分组名称
    is_group: bool                   # 是否是组权限
    description: str                 # 描述
    status: int                      # 状态
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
```

#### AdminRolePermission (角色权限关联表)

```python
class AdminRolePermission(Base):
    """角色权限关联表 - 支持allow/deny和优先级"""
    __tablename__ = "admin_role_permissions"
    
    id: int                          # ID
    role_id: int                     # 角色ID
    permission_id: int               # 权限ID
    effect: str                      # allow/deny
    priority: int                    # 优先级
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
```

### 2. 服务层组件

#### AdminPermissionService

负责权限的CRUD操作，提供以下方法：

```python
class AdminPermissionService:
    @staticmethod
    def get_by_id(db: Session, permission_id: int) -> Optional[AdminPermission]
    
    @staticmethod
    def get_by_resource_pattern(db: Session, pattern: str) -> Optional[AdminPermission]
    
    @staticmethod
    def get_list(db: Session, skip: int, limit: int, 
                 keyword: str, status: int, group_key: str) -> tuple[List, int]
    
    @staticmethod
    def get_grouped_permissions(db: Session) -> Dict[str, List[AdminPermission]]
    
    @staticmethod
    def create(db: Session, permission_in: AdminPermissionCreate) -> AdminPermission
    
    @staticmethod
    def update(db: Session, permission_id: int, 
               permission_in: AdminPermissionUpdate) -> Optional[AdminPermission]
    
    @staticmethod
    def delete(db: Session, permission_id: int) -> bool
    
    @staticmethod
    def match_pattern(pattern: str, path: str) -> bool
```

#### AdminRBACService (增强版)

负责权限检查和验证，核心方法：

```python
class AdminRBACService:
    @staticmethod
    def get_user_permissions_with_effect(
        db: Session, 
        admin_user_id: int
    ) -> List[Tuple[AdminPermission, str, int]]
    
    @staticmethod
    def check_user_permission(
        db: Session, 
        admin_user_id: int, 
        api_path: str, 
        method: str
    ) -> bool
    
    @staticmethod
    def get_role_permissions_grouped(
        db: Session, 
        role_id: int
    ) -> Dict[str, Any]
    
    @staticmethod
    def assign_role_permissions(
        db: Session, 
        role_id: int, 
        permission_assignments: List[PermissionAssignment]
    ) -> bool
```

#### PermissionSyncService (新增)

负责从OpenAPI同步权限：

```python
class PermissionSyncService:
    @staticmethod
    def extract_routes_from_app(app: FastAPI) -> List[RouteInfo]
    
    @staticmethod
    def generate_group_key(path: str, tags: List[str]) -> str
    
    @staticmethod
    def sync_permissions(db: Session, routes: List[RouteInfo]) -> SyncResult
    
    @staticmethod
    def create_group_permissions(db: Session, group_keys: Set[str]) -> List[AdminPermission]
```

### 3. API接口组件

#### 权限管理接口

```python
# GET /api/admin/permissions/list
# 参数: page, page_size, keyword, status, group_key
# 返回: PageResponse[AdminPermissionResponse]

# GET /api/admin/permissions/detail/{permission_id}
# 返回: AdminPermissionResponse

# POST /api/admin/permissions/create
# 请求体: AdminPermissionCreate
# 返回: AdminPermissionResponse

# POST /api/admin/permissions/update/{permission_id}
# 请求体: AdminPermissionUpdate
# 返回: AdminPermissionResponse

# POST /api/admin/permissions/delete/{permission_id}
# 返回: Response

# GET /api/admin/permissions/groups
# 返回: Dict[str, List[AdminPermissionResponse]]
```

#### 角色权限管理接口

```python
# GET /api/admin/roles/{role_id}/permissions
# 返回: RolePermissionsGroupedResponse

# POST /api/admin/roles/{role_id}/permissions/assign
# 请求体: List[PermissionAssignment]
# 返回: Response

# POST /api/admin/roles/{role_id}/permissions/remove
# 请求体: List[int]  # permission_ids
# 返回: Response
```

### 4. 中间件组件

#### PermissionCheckMiddleware

```python
class PermissionCheckMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. 提取用户信息
        # 2. 提取请求路径和方法
        # 3. 检查是否在白名单中
        # 4. 调用 AdminRBACService.check_user_permission
        # 5. 返回结果或403错误
```

### 5. 工具脚本组件

#### sync_permissions_from_openapi.py

```python
def main():
    # 1. 加载FastAPI应用
    # 2. 提取所有路由
    # 3. 连接数据库
    # 4. 调用 PermissionSyncService.sync_permissions
    # 5. 输出同步结果
```

## Data Models

### 数据库表结构

#### admin_permissions (权限表)

| 字段 | 类型 | 说明 | 索引 |
|------|------|------|------|
| id | INTEGER | 主键 | PK |
| name | VARCHAR(100) | 权限名称 | - |
| resource_pattern | VARCHAR(255) | 资源模式 | UNIQUE |
| method | VARCHAR(10) | HTTP方法 | - |
| group_key | VARCHAR(100) | 分组标识 | INDEX |
| group_name | VARCHAR(100) | 分组名称 | - |
| is_group | BOOLEAN | 是否组权限 | - |
| description | TEXT | 描述 | - |
| status | INTEGER | 状态 | - |
| created_at | DATETIME | 创建时间 | - |
| updated_at | DATETIME | 更新时间 | - |
| is_deleted | BOOLEAN | 逻辑删除 | INDEX |

#### admin_role_permissions (角色权限关联表)

| 字段 | 类型 | 说明 | 索引 |
|------|------|------|------|
| id | INTEGER | 主键 | PK |
| role_id | INTEGER | 角色ID | INDEX |
| permission_id | INTEGER | 权限ID | INDEX |
| effect | VARCHAR(10) | allow/deny | - |
| priority | INTEGER | 优先级 | - |
| created_at | DATETIME | 创建时间 | - |
| updated_at | DATETIME | 更新时间 | - |
| is_deleted | BOOLEAN | 逻辑删除 | INDEX |

**约束**：
- UNIQUE(role_id, permission_id) - 同一角色不能对同一权限有重复关联

### Pydantic Schemas

#### AdminPermissionCreate

```python
class AdminPermissionCreate(BaseModel):
    name: str
    resource_pattern: str
    method: str = "POST"
    group_key: Optional[str] = None
    group_name: Optional[str] = None
    is_group: bool = False
    description: Optional[str] = None
    status: int = 1
```

#### AdminPermissionUpdate

```python
class AdminPermissionUpdate(BaseModel):
    name: Optional[str] = None
    resource_pattern: Optional[str] = None
    method: Optional[str] = None
    group_key: Optional[str] = None
    group_name: Optional[str] = None
    is_group: Optional[bool] = None
    description: Optional[str] = None
    status: Optional[int] = None
```

#### AdminPermissionResponse

```python
class AdminPermissionResponse(BaseModel):
    id: int
    name: str
    resource_pattern: str
    method: str
    group_key: Optional[str]
    group_name: Optional[str]
    is_group: bool
    description: Optional[str]
    status: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

#### PermissionAssignment

```python
class PermissionAssignment(BaseModel):
    permission_id: int
    effect: str = "allow"  # allow/deny
    priority: int = 0
```

#### RolePermissionsGroupedResponse

```python
class PermissionWithEffect(BaseModel):
    id: int
    name: str
    resource_pattern: str
    method: str
    effect: str
    priority: int
    is_inherited: bool
    is_overridden: bool

class PermissionGroup(BaseModel):
    group_key: str
    group_name: str
    group_permission: Optional[PermissionWithEffect]
    children: List[PermissionWithEffect]

class RolePermissionsGroupedResponse(BaseModel):
    role_id: int
    groups: List[PermissionGroup]
```

### 权限匹配算法

使用Python的 `fnmatch` 模块进行通配符匹配：

```python
import fnmatch

def match_pattern(pattern: str, path: str) -> bool:
    """
    匹配资源模式
    
    支持的通配符：
    - * : 匹配任意字符（不包括/）
    - ** : 匹配任意字符（包括/）
    - ? : 匹配单个字符
    
    示例：
    - /system/logs/* 匹配 /system/logs/list
    - /system/** 匹配 /system/logs/list
    - /system/logs/? 匹配 /system/logs/1
    """
    # 处理 ** 通配符
    if '**' in pattern:
        pattern = pattern.replace('**', '*')
    
    return fnmatch.fnmatch(path, pattern)
```

### 权限检查流程

```python
def check_permission(db: Session, user_id: int, path: str, method: str) -> bool:
    """
    权限检查流程：
    1. 获取用户所有角色
    2. 获取角色的所有权限（包括effect和priority）
    3. 匹配请求路径（支持通配符）
    4. 按优先级排序
    5. 应用最高优先级规则
    """
    # 1. 获取用户角色
    role_ids = get_user_roles(db, user_id)
    
    # 2. 获取角色权限
    role_permissions = db.query(AdminRolePermission).filter(
        AdminRolePermission.role_id.in_(role_ids),
        AdminRolePermission.is_deleted == False
    ).all()
    
    # 3. 获取权限详情
    permission_ids = [rp.permission_id for rp in role_permissions]
    permissions = db.query(AdminPermission).filter(
        AdminPermission.id.in_(permission_ids),
        AdminPermission.is_deleted == False,
        AdminPermission.status == 1
    ).all()
    
    # 4. 匹配路径并收集规则
    matched_rules = []
    for perm in permissions:
        if perm.method == method and match_pattern(perm.resource_pattern, path):
            # 找到对应的role_permission获取effect和priority
            rp = next((r for r in role_permissions if r.permission_id == perm.id), None)
            if rp:
                matched_rules.append((rp.effect, rp.priority))
    
    # 5. 如果没有匹配规则，默认拒绝
    if not matched_rules:
        return False
    
    # 6. 按优先级排序（降序）
    matched_rules.sort(key=lambda x: x[1], reverse=True)
    
    # 7. 应用最高优先级规则
    highest_priority_effect = matched_rules[0][0]
    
    return highest_priority_effect == "allow"
```

## Correctness Properties


*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Wildcard Pattern Storage and Retrieval

*For any* permission created with a wildcard pattern (containing `*` or `**`), the system should store it correctly and mark `is_group` as True, and retrieving it should return the exact same pattern.

**Validates: Requirements 1.1, 1.2**

### Property 2: Permission Data Integrity

*For any* permission created with group_key and group_name fields, querying the permission by ID should return the same group_key and group_name values.

**Validates: Requirements 1.3, 1.4**

### Property 3: Mixed Permission Query Completeness

*For any* database containing both group permissions (with wildcards) and individual permissions, querying all permissions should return both types without filtering either out.

**Validates: Requirements 1.5**

### Property 4: Effect Value Validation

*For any* role-permission association, the effect field should only accept "allow" or "deny" values, and storing then retrieving should preserve the exact value.

**Validates: Requirements 2.1**

### Property 5: Priority-Based Rule Selection

*For any* set of matching permission rules with different priorities, the permission check should apply the rule with the highest priority value.

**Validates: Requirements 2.3, 6.4, 6.5**

### Property 6: Default Priority Assignment

*For any* role-permission association created without specifying priority, if the effect is "allow", the priority should default to 0.

**Validates: Requirements 2.5**

### Property 7: Route Metadata Extraction Completeness

*For any* FastAPI route with path, method, tags, and summary, the sync process should extract all four fields and store them in the permission record.

**Validates: Requirements 3.3**

### Property 8: Sync Idempotence

*For any* route that already exists in the database, running the sync script twice should result in the same permission record (no duplicates created).

**Validates: Requirements 3.4, 3.5**

### Property 9: Group Key Generation Consistency

*For any* two routes with the same tags or path prefix, the sync process should generate the same group_key for both.

**Validates: Requirements 3.6**

### Property 10: Automatic Group Permission Creation

*For any* set of routes sharing the same group_key, the sync process should create exactly one group permission with a wildcard pattern for that group.

**Validates: Requirements 3.7**

### Property 11: Role Permission Grouping Structure

*For any* role with assigned permissions, querying role permissions should return them organized by group_key, with each group containing its group permission and child permissions.

**Validates: Requirements 4.1, 4.5, 5.1.1**

### Property 12: Child Permission Inclusion

*For any* role assigned a group permission, querying role permissions should include all individual permissions matching that group's pattern in the children list.

**Validates: Requirements 4.2, 5.1.2**

### Property 13: Override Flag Accuracy

*For any* child permission with an explicit deny rule while its group has an allow rule, the permission should be marked as `is_overridden: true` in the response.

**Validates: Requirements 4.3, 5.1.3**

### Property 14: Inheritance Flag Accuracy

*For any* permission in a role's permission list, if it's only present because of a group permission (not explicitly assigned), it should be marked as `is_inherited: true`.

**Validates: Requirements 4.4, 5.1.4**

### Property 15: Effective Permission Calculation

*For any* API path and role with multiple matching rules (group + individual, allow + deny), the calculated effective permission should match the result of applying the highest priority rule.

**Validates: Requirements 5.1.5**

### Property 16: Group Assignment Default Effect

*For any* group permission assigned to a role without specifying effect, the system should create an "allow" rule with priority 0.

**Validates: Requirements 5.2**

### Property 17: Exclusion Creates High-Priority Deny

*For any* specific permission excluded from a group, the system should create a "deny" rule with priority higher than the group's allow rule.

**Validates: Requirements 5.3**

### Property 18: Assignment Removal Completeness

*For any* role-permission association, removing it should result in the association no longer appearing in queries for that role's permissions.

**Validates: Requirements 5.4**

### Property 19: Permission Existence Validation

*For any* attempt to assign a non-existent permission_id to a role, the system should reject the operation with an error.

**Validates: Requirements 5.5**

### Property 20: Duplicate Prevention

*For any* role-permission pair that already exists with a specific effect, attempting to create the same association again should be rejected or ignored.

**Validates: Requirements 5.6**

### Property 21: Pattern Matching Correctness

*For any* resource pattern containing wildcards and any request path, the matching algorithm should correctly determine if the path matches the pattern according to fnmatch rules.

**Validates: Requirements 6.3**

### Property 22: Query Filter Correctness

*For any* permission list query with filters (group_key, is_group, or status), the results should only include permissions matching all specified filter criteria.

**Validates: Requirements 7.2, 7.3, 7.4**

### Property 23: Query Response Completeness

*For any* permission returned in a query response, all group-related fields (group_key, group_name, is_group) should be included in the response.

**Validates: Requirements 7.5**

### Property 24: Migration Group Key Generation

*For any* existing permission with api_path like `/system/logs/list`, the migration should generate a group_key by extracting the path prefix (e.g., `system.logs`).

**Validates: Requirements 8.3**

### Property 25: Migration ID Preservation

*For any* permission existing before migration, after migration completes, the permission should retain the same ID and all role-permission associations should still reference the correct IDs.

**Validates: Requirements 8.6**

### Property 26: Backward Compatible Path Lookup

*For any* API path, calling get_by_api_path should find permissions where either resource_pattern equals the path exactly OR resource_pattern matches the path as a wildcard.

**Validates: Requirements 9.2**

### Property 27: Dual Format Permission Check

*For any* user permission check, the system should evaluate permissions using both legacy api_path format (if present) and new resource_pattern format, returning true if either matches.

**Validates: Requirements 9.4**

## Error Handling

### 1. 数据验证错误

**场景**: 创建或更新权限时提供无效数据

**处理策略**:
- 使用Pydantic进行输入验证
- 返回400 Bad Request with详细错误信息
- 错误信息应包含具体的字段和原因

**示例**:
```python
{
    "code": 400,
    "message": "验证失败",
    "data": {
        "errors": [
            {"field": "resource_pattern", "message": "资源模式不能为空"},
            {"field": "effect", "message": "effect必须是allow或deny"}
        ]
    }
}
```

### 2. 资源不存在错误

**场景**: 查询、更新或删除不存在的权限

**处理策略**:
- 返回404 Not Found
- 提供清晰的错误消息

**示例**:
```python
{
    "code": 404,
    "message": "权限不存在",
    "data": None
}
```

### 3. 重复资源错误

**场景**: 创建已存在的resource_pattern或重复的角色-权限关联

**处理策略**:
- 检查唯一性约束
- 返回400 Bad Request
- 提供具体的冲突信息

**示例**:
```python
{
    "code": 400,
    "message": "资源模式已存在: /system/logs/*",
    "data": None
}
```

### 4. 权限检查失败

**场景**: 用户尝试访问无权限的API

**处理策略**:
- 返回403 Forbidden
- 记录访问尝试日志
- 不泄露敏感信息

**示例**:
```python
{
    "code": 403,
    "message": "无权限访问此资源",
    "data": None
}
```

### 5. 数据库错误

**场景**: 数据库连接失败或查询错误

**处理策略**:
- 捕获SQLAlchemy异常
- 返回500 Internal Server Error
- 记录详细错误日志
- 向用户返回通用错误消息

**示例**:
```python
{
    "code": 500,
    "message": "服务器内部错误，请稍后重试",
    "data": None
}
```

### 6. 同步脚本错误

**场景**: OpenAPI同步过程中出现错误

**处理策略**:
- 使用事务确保原子性
- 出错时回滚所有更改
- 记录详细错误日志
- 输出友好的错误消息

**错误类型**:
- FastAPI应用加载失败
- 数据库连接失败
- 权限创建失败

### 7. 迁移脚本错误

**场景**: 数据迁移过程中出现错误

**处理策略**:
- 在迁移前备份数据
- 使用事务确保原子性
- 提供回滚机制
- 详细记录迁移日志

## Testing Strategy

### 测试方法论

本项目采用**双重测试策略**：单元测试（Unit Tests）和基于属性的测试（Property-Based Tests）。两者互补，共同确保系统的正确性：

- **单元测试**: 验证特定示例、边界情况和错误条件
- **属性测试**: 验证通用属性在所有输入下都成立

### 属性测试框架

使用 **Hypothesis** 作为Python的属性测试库。Hypothesis通过生成大量随机输入来验证属性。

安装:
```bash
pip install hypothesis
```

配置: 每个属性测试至少运行100次迭代。

### 测试组织结构

```
tests/
├── unit/
│   ├── test_permission_service.py
│   ├── test_rbac_service.py
│   ├── test_sync_service.py
│   └── test_migration.py
├── property/
│   ├── test_permission_properties.py
│   ├── test_rbac_properties.py
│   ├── test_pattern_matching_properties.py
│   └── test_migration_properties.py
└── integration/
    ├── test_permission_api.py
    ├── test_role_permission_api.py
    └── test_permission_middleware.py
```

### 属性测试示例

#### 示例1: Property 1 - Wildcard Pattern Storage

```python
from hypothesis import given, strategies as st
import pytest

# Feature: hierarchical-rbac-permission, Property 1: Wildcard Pattern Storage and Retrieval

@given(
    name=st.text(min_size=1, max_size=100),
    pattern=st.one_of(
        st.just("/system/logs/*"),
        st.just("/api/**/users"),
        st.text(min_size=1).map(lambda s: f"/{s}/*")
    )
)
def test_wildcard_pattern_storage_and_retrieval(db_session, name, pattern):
    """
    Property 1: For any permission created with a wildcard pattern,
    the system should store it correctly and mark is_group as True.
    """
    # Create permission with wildcard
    permission = AdminPermission(
        name=name,
        resource_pattern=pattern,
        method="POST"
    )
    db_session.add(permission)
    db_session.commit()
    
    # Retrieve and verify
    retrieved = db_session.query(AdminPermission).filter_by(id=permission.id).first()
    
    assert retrieved is not None
    assert retrieved.resource_pattern == pattern
    assert retrieved.is_group == True  # Should be auto-set for wildcards
```

#### 示例2: Property 5 - Priority-Based Rule Selection

```python
from hypothesis import given, strategies as st, assume

# Feature: hierarchical-rbac-permission, Property 5: Priority-Based Rule Selection

@given(
    priorities=st.lists(st.integers(min_value=0, max_value=1000), min_size=2, max_size=10, unique=True)
)
def test_priority_based_rule_selection(db_session, test_user, test_role, priorities):
    """
    Property 5: For any set of matching permission rules with different priorities,
    the permission check should apply the rule with the highest priority value.
    """
    # Create permissions with different priorities
    path = "/test/api"
    permission = create_test_permission(db_session, resource_pattern=path)
    
    # Assign with different priorities and effects
    for i, priority in enumerate(priorities):
        effect = "deny" if i == 0 else "allow"  # Highest priority is deny
        create_role_permission(db_session, test_role.id, permission.id, effect, priority)
    
    # Check permission
    has_permission = AdminRBACService.check_user_permission(
        db_session, test_user.id, path, "POST"
    )
    
    # Should apply highest priority rule (which is deny)
    highest_priority = max(priorities)
    expected_effect = "deny" if priorities.index(highest_priority) == 0 else "allow"
    
    assert has_permission == (expected_effect == "allow")
```

### 单元测试示例

#### 示例1: 测试权限创建

```python
def test_create_permission_success(db_session):
    """测试成功创建权限"""
    permission_in = AdminPermissionCreate(
        name="查看日志",
        resource_pattern="/system/logs/list",
        method="GET",
        group_key="system.logs",
        group_name="日志管理"
    )
    
    permission = AdminPermissionService.create(db_session, permission_in)
    
    assert permission.id is not None
    assert permission.name == "查看日志"
    assert permission.resource_pattern == "/system/logs/list"
    assert permission.group_key == "system.logs"
```

#### 示例2: 测试重复资源模式

```python
def test_create_permission_duplicate_pattern(db_session):
    """测试创建重复的资源模式应该失败"""
    permission_in = AdminPermissionCreate(
        name="权限1",
        resource_pattern="/system/logs/*",
        method="POST"
    )
    
    # 第一次创建成功
    AdminPermissionService.create(db_session, permission_in)
    
    # 第二次创建应该失败
    with pytest.raises(ValueError, match="资源模式已存在"):
        AdminPermissionService.create(db_session, permission_in)
```

#### 示例3: 测试通配符匹配

```python
@pytest.mark.parametrize("pattern,path,expected", [
    ("/system/logs/*", "/system/logs/list", True),
    ("/system/logs/*", "/system/logs/detail/123", False),
    ("/system/**", "/system/logs/list", True),
    ("/system/**", "/system/config/update", True),
    ("/api/*/users", "/api/v1/users", True),
    ("/api/*/users", "/api/v1/posts", False),
])
def test_pattern_matching(pattern, path, expected):
    """测试通配符模式匹配"""
    result = AdminPermissionService.match_pattern(pattern, path)
    assert result == expected
```

### 集成测试

#### 测试权限检查中间件

```python
def test_permission_middleware_allows_authorized_request(client, test_user_with_permission):
    """测试中间件允许有权限的请求"""
    # 设置认证token
    token = create_test_token(test_user_with_permission)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 发送请求
    response = client.get("/api/admin/permissions/list", headers=headers)
    
    assert response.status_code == 200

def test_permission_middleware_denies_unauthorized_request(client, test_user_without_permission):
    """测试中间件拒绝无权限的请求"""
    token = create_test_token(test_user_without_permission)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/admin/permissions/list", headers=headers)
    
    assert response.status_code == 403
    assert "无权限" in response.json()["message"]
```

### 测试数据生成器

为属性测试创建自定义生成器：

```python
from hypothesis import strategies as st

# 生成有效的资源模式
@st.composite
def resource_patterns(draw):
    """生成有效的资源模式"""
    segments = draw(st.lists(st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')), min_size=1, max_size=10), min_size=1, max_size=5))
    path = "/" + "/".join(segments)
    
    # 随机决定是否添加通配符
    if draw(st.booleans()):
        path += "/*"
    
    return path

# 生成有效的HTTP方法
http_methods = st.sampled_from(["GET", "POST"])

# 生成有效的effect值
effects = st.sampled_from(["allow", "deny"])

# 生成优先级
priorities = st.integers(min_value=0, max_value=1000)
```

### 测试覆盖率目标

- **单元测试覆盖率**: 至少80%
- **属性测试**: 覆盖所有27个correctness properties
- **集成测试**: 覆盖所有API端点和中间件

### 持续集成

在CI/CD流程中运行所有测试：

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install hypothesis pytest pytest-cov
      - name: Run tests
        run: |
          pytest tests/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### 测试最佳实践

1. **隔离性**: 每个测试应该独立，不依赖其他测试的状态
2. **可重复性**: 测试结果应该是确定的和可重复的
3. **清晰性**: 测试名称应该清楚地描述测试内容
4. **快速性**: 单元测试应该快速执行（< 1秒）
5. **完整性**: 测试应该覆盖正常路径、边界情况和错误情况

### 测试执行

```bash
# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unit/

# 运行属性测试
pytest tests/property/

# 运行特定测试文件
pytest tests/property/test_permission_properties.py

# 运行带覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 运行属性测试并显示详细输出
pytest tests/property/ -v --hypothesis-show-statistics
```
