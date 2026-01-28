# RBAC 权限系统架构文档

## 一、系统概述

本系统实现了一套完整的层级化 RBAC（基于角色的访问控制）权限管理系统，支持：

- **用户-角色-权限** 三层架构
- **组权限与子权限** 的层级继承
- **Allow/Deny 机制** 与优先级控制
- **用户权限覆盖** 机制
- **通配符模式匹配** 支持

---

## 二、核心架构图

### 2.1 实体关系图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           RBAC 权限架构                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   AdminUser  │
│   (用户)      │
└──────┬───────┘
       │
┌──────────────────────┼──────────────────────┐
│                      │                      │
▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐
│  AdminUserRole  │    │  AdminUserRole  │    │ AdminUserPermissionOverride │
│  (用户角色1)     │    │  (用户角色2)     │    │ (用户权限覆盖)              │
└────────┬────────┘    └────────┬────────┘    │ - permission_id            │
         │                      │             │ - effect: ALLOW/DENY       │
         ▼                      ▼             └─────────────────────────────┘
┌─────────────────┐    ┌─────────────────┐
│   AdminRole     │    │   AdminRole     │
│   (角色A)       │    │   (角色B)       │
└────────┬────────┘    └────────┬────────┘
         │                      │
         ▼                      ▼
┌─────────────────────────────────────────┐
│         AdminRolePermission             │
│  - role_id                              │
│  - permission_id                        │
│  - effect: allow/deny                   │
│  - priority: 0-100                      │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AdminPermission                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  组权限 (is_group=True)                                      │   │
│  │  - resource_pattern: /api/admin/users/**                    │   │
│  │  - method: *                                                │   │
│  │  - group_key: admin_users                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                    group_key 关联                                   │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  子权限 (is_group=False)                                     │   │
│  │  - resource_pattern: /api/admin/users/list                  │   │
│  │  - method: GET                                              │   │
│  │  - group_key: admin_users                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```


### 2.2 数据库表结构

#### admin_users（用户表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| username | VARCHAR(50) | 用户名 |
| password | VARCHAR(255) | 密码哈希 |
| is_superuser | BOOLEAN | 是否超级管理员 |
| is_active | BOOLEAN | 是否激活 |
| ... | ... | 其他字段 |

#### admin_roles（角色表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(50) | 角色名称 |
| description | TEXT | 角色描述 |
| status | INTEGER | 状态 |

#### admin_user_roles（用户角色关联表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| admin_user_id | INTEGER | 用户ID |
| role_id | INTEGER | 角色ID |
| is_deleted | BOOLEAN | 软删除标记 |

#### admin_permissions（权限表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(100) | 权限名称 |
| resource_pattern | VARCHAR(255) | 资源模式（支持通配符） |
| method | VARCHAR(10) | HTTP方法（GET/POST/PUT/DELETE/*） |
| group_key | VARCHAR(100) | 分组标识 |
| group_name | VARCHAR(100) | 分组名称 |
| is_group | BOOLEAN | 是否组权限 |
| description | TEXT | 描述 |
| status | INTEGER | 状态：1=启用，0=禁用 |

#### admin_role_permissions（角色权限关联表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| role_id | INTEGER | 角色ID |
| permission_id | INTEGER | 权限ID |
| effect | VARCHAR(10) | 效果：allow/deny |
| priority | INTEGER | 优先级（0-100，越大越高） |

#### admin_user_permission_overrides（用户权限覆盖表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| admin_user_id | INTEGER | 用户ID |
| permission_id | INTEGER | 权限ID |
| effect | ENUM | ALLOW/DENY |

---

## 三、权限计算流程

### 3.1 完整权限检查流程图

```
请求: GET /api/admin/users/detail/123
                    │
                    ▼
┌───────────────────────────────────────┐
│ 1. 认证中间件 (AuthMiddleware)         │
│    - 验证 JWT Token                   │
│    - 提取 user_id                     │
│    - 检查用户是否被禁用                │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│ 2. 超级管理员检查                      │
│    IF is_superuser == True            │
│    THEN 跳过权限验证，直接放行          │
└───────────────────┬───────────────────┘
                    │ (非超级管理员)
                    ▼
┌───────────────────────────────────────┐
│ 3. 获取用户所有角色                    │
│    User → [Role_A, Role_B, ...]       │
│    查询: AdminUserRole 表              │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│ 4. 获取角色的所有权限                  │
│    查询: AdminRolePermission 表        │
│    获取: permission_id, effect,        │
│          priority                      │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│ 5. 获取权限详情                        │
│    查询: AdminPermission 表            │
│    获取: resource_pattern, method,     │
│          is_group, group_key           │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│ 6. 路径匹配                            │
│    FOR EACH permission:                │
│      - 检查 method 匹配                │
│      - 检查 resource_pattern 匹配      │
│        (支持通配符: *, **, ?)          │
│      - 收集所有匹配的规则              │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│ 7. 优先级排序                          │
│    - 按 priority 降序排序              │
│    - 相同优先级时 deny 优先于 allow    │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│ 8. 应用最高优先级规则                  │
│    - 取排序后的第一条规则              │
│    - effect == "allow" → 允许          │
│    - effect == "deny" → 拒绝           │
│    - 无匹配规则 → 默认拒绝             │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│ 9. 返回结果                            │
│    - 允许: 继续处理请求                │
│    - 拒绝: 返回 403 Forbidden          │
└───────────────────────────────────────┘
```


### 3.2 权限优先级规则

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           权限计算优先级规则                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

优先级从高到低:

1. 超级管理员 (is_superuser=True)
   └── 直接放行，跳过所有权限检查

2. 用户权限覆盖 (AdminUserPermissionOverride)
   ├── ALLOW → 强制允许
   └── DENY  → 强制拒绝

3. 角色子权限 (AdminRolePermission where is_group=False)
   ├── 按 priority 值排序（越大越优先）
   ├── 相同 priority 时: deny 优先于 allow
   ├── 多角色冲突时: ALLOW 优先于 DENY（取并集）
   ├── allow → 允许
   └── deny  → 拒绝

4. 角色组权限 (AdminRolePermission where is_group=True)
   ├── 通过 group_key 继承到子权限
   ├── 按 priority 值排序
   ├── 多角色冲突时: ALLOW 优先于 DENY
   ├── allow → 允许
   └── deny  → 拒绝

5. 无匹配权限
   └── 默认拒绝
```

### 3.3 多角色权限合并规则

当用户拥有多个角色时，权限合并遵循以下规则：

```python
# 伪代码示例
def merge_role_permissions(role_permissions_list):
    """
    多角色权限合并
    规则：同一权限在多个角色中存在时，ALLOW 优先于 DENY
    """
    merged = {}
    
    for role_perms in role_permissions_list:
        for perm_id, (effect, priority) in role_perms.items():
            if perm_id not in merged:
                merged[perm_id] = (effect, priority)
            else:
                existing_effect, existing_priority = merged[perm_id]
                # 如果新的是 allow，或者优先级更高，则更新
                if effect == "allow" or priority > existing_priority:
                    merged[perm_id] = (effect, priority)
    
    return merged
```

**示例场景：**

| 角色 | 权限 | Effect | Priority |
|------|------|--------|----------|
| 角色A | 用户管理 | allow | 0 |
| 角色B | 用户管理 | deny | 0 |

**结果：** 用户拥有"用户管理"权限（ALLOW 优先）

---

## 四、通配符模式匹配

### 4.1 支持的通配符

| 通配符 | 说明 | 示例 |
|--------|------|------|
| `*` | 匹配任意字符（单个路径段） | `/users/*` 匹配 `/users/list` |
| `**` | 匹配任意字符（包括多个路径段） | `/users/**` 匹配 `/users/a/b/c` |
| `?` | 匹配单个字符 | `/users/?` 匹配 `/users/1` |

### 4.2 匹配示例

```
模式: /api/admin/users/**
├── ✅ /api/admin/users/list
├── ✅ /api/admin/users/detail/123
├── ✅ /api/admin/users/create
└── ❌ /api/admin/roles/list

模式: /api/admin/users/*
├── ✅ /api/admin/users/list
├── ✅ /api/admin/users/create
└── ❌ /api/admin/users/detail/123  (多层路径不匹配)

模式: /api/admin/users/detail/*
├── ✅ /api/admin/users/detail/123
├── ✅ /api/admin/users/detail/456
└── ❌ /api/admin/users/list
```

### 4.3 匹配算法实现

```python
def match_pattern(pattern: str, path: str) -> bool:
    """
    匹配资源模式
    
    Args:
        pattern: 资源模式（支持通配符）
        path: 请求路径
        
    Returns:
        是否匹配
    """
    # 处理 ** 通配符（匹配多个路径段）
    if '**' in pattern:
        import re
        regex_pattern = pattern.replace('**', '<<<DOUBLE_STAR>>>')
        regex_pattern = re.escape(regex_pattern)
        regex_pattern = regex_pattern.replace('<<<DOUBLE_STAR>>>', '.*')
        regex_pattern = regex_pattern.replace(r'\*', '[^/]*')
        regex_pattern = regex_pattern.replace(r'\?', '[^/]')
        regex_pattern = f'^{regex_pattern}$'
        return bool(re.match(regex_pattern, path))
    
    # 使用 fnmatch 处理单个 * 和 ? 通配符
    return fnmatch.fnmatch(path, pattern)
```


---

## 五、组权限与子权限继承

### 5.1 组权限概念

组权限是一种特殊的权限，用于批量管理一组相关的 API 权限：

```
┌─────────────────────────────────────────────────────────────────────┐
│                        组权限继承机制                                │
└─────────────────────────────────────────────────────────────────────┘

组权限 (is_group=True)
├── name: "用户管理"
├── resource_pattern: "/api/admin/users/**"
├── method: "*"
├── group_key: "admin_users"
└── group_name: "用户管理"
         │
         │ 通过 group_key 关联
         ▼
子权限 (is_group=False)
├── 用户列表
│   ├── resource_pattern: "/api/admin/users/list"
│   ├── method: "GET"
│   └── group_key: "admin_users"
│
├── 用户详情
│   ├── resource_pattern: "/api/admin/users/detail/*"
│   ├── method: "GET"
│   └── group_key: "admin_users"
│
├── 创建用户
│   ├── resource_pattern: "/api/admin/users/create"
│   ├── method: "POST"
│   └── group_key: "admin_users"
│
└── 删除用户
    ├── resource_pattern: "/api/admin/users/delete/*"
    ├── method: "POST"
    └── group_key: "admin_users"
```

### 5.2 继承规则

1. **授权组权限时**：自动继承该组下所有子权限
2. **子权限可覆盖**：可以单独为子权限设置不同的 effect
3. **优先级控制**：子权限的 priority 可以高于组权限，实现覆盖

### 5.3 继承示例

```
场景：角色"普通管理员"

授权配置：
├── 组权限: 用户管理 (effect=allow, priority=0)
└── 子权限: 删除用户 (effect=deny, priority=10)

结果：
├── ✅ /api/admin/users/list      → 允许（继承自组权限）
├── ✅ /api/admin/users/detail/*  → 允许（继承自组权限）
├── ✅ /api/admin/users/create    → 允许（继承自组权限）
└── ❌ /api/admin/users/delete/*  → 拒绝（子权限覆盖，priority=10 > 0）
```

### 5.4 判断子权限是否属于组权限

```python
def is_pattern_subset(parent_pattern: str, child_pattern: str) -> bool:
    """
    判断子权限模式是否属于父权限模式的范围
    
    Args:
        parent_pattern: 父权限模式（组权限）
        child_pattern: 子权限模式
        
    Returns:
        子权限是否属于父权限范围
    """
    # 如果父模式以 /** 结尾
    if parent_pattern.endswith('/**'):
        prefix = parent_pattern[:-3]
        return child_pattern.startswith(prefix + '/') or child_pattern == prefix
    
    # 如果父模式以 /* 结尾
    if parent_pattern.endswith('/*'):
        prefix = parent_pattern[:-2]
        if child_pattern.startswith(prefix + '/'):
            remaining = child_pattern[len(prefix) + 1:]
            return '/' not in remaining or remaining.endswith('/*')
        return False
    
    # 精确匹配
    return parent_pattern == child_pattern
```

---

## 六、用户权限覆盖机制

### 6.1 概述

用户权限覆盖（AdminUserPermissionOverride）允许为特定用户单独设置权限，优先级高于角色权限。

### 6.2 使用场景

1. **临时授权**：给用户临时开放某个权限
2. **特殊限制**：禁止某用户访问特定功能
3. **个性化配置**：为 VIP 用户开放额外功能

### 6.3 覆盖规则

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户权限覆盖流程                              │
└─────────────────────────────────────────────────────────────────────┘

用户请求 API
      │
      ▼
┌─────────────────────────────────┐
│ 1. 检查用户权限覆盖表            │
│    AdminUserPermissionOverride  │
└───────────────┬─────────────────┘
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
   有覆盖记录       无覆盖记录
        │               │
        ▼               ▼
┌───────────────┐ ┌───────────────┐
│ ALLOW → 允许  │ │ 继续检查      │
│ DENY  → 拒绝  │ │ 角色权限      │
└───────────────┘ └───────────────┘
```

### 6.4 API 接口

```
# 设置用户权限覆盖
POST /api/admin/admin-users/{user_id}/permission-overrides
{
    "permission_id": 1,
    "effect": "ALLOW"  // 或 "DENY"
}

# 获取用户权限覆盖列表
GET /api/admin/admin-users/{user_id}/permission-overrides

# 删除用户权限覆盖
DELETE /api/admin/admin-users/{user_id}/permission-overrides/{override_id}

# 清除用户所有权限覆盖
DELETE /api/admin/admin-users/{user_id}/permission-overrides/clear
```


---

## 七、核心服务层实现

### 7.1 服务类结构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        服务层架构                                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────┐
│     AdminRBACService            │
│     (RBAC 核心服务)              │
├─────────────────────────────────┤
│ + get_user_roles()              │  获取用户角色列表
│ + assign_user_roles()           │  分配用户角色
│ + get_user_permissions()        │  获取用户权限集合
│ + check_user_permission()       │  检查用户API权限 (已废弃)
│ + check_permission_detail()     │  检查用户API权限（返回详细结果）★新增
│ + get_role_permissions_grouped()│  获取角色分组权限 (已废弃)
│ + get_role_permissions_detail() │  获取角色权限详情（含来源追踪）★新增
│ + get_user_permissions_detail() │  获取用户权限详情（含来源追踪）★新增
│ + assign_role_permissions()     │  分配角色权限
│ + remove_role_permissions()     │  移除角色权限
│ + set_user_permission_overrides()│ 设置用户权限覆盖
│ + get_user_permission_overrides()│ 获取用户权限覆盖
└─────────────────────────────────┘
              │
              │ 调用
              ▼
┌─────────────────────────────────┐
│   AdminPermissionService        │
│   (权限服务)                     │
├─────────────────────────────────┤
│ + match_pattern()               │  通配符模式匹配
│ + is_pattern_subset()           │  判断子权限归属
│ + get_by_id()                   │  根据ID获取权限
│ + get_by_api_path()             │  根据路径获取权限
│ + find_matching_permissions()   │  查找匹配的权限
│ + get_grouped_permissions()     │  获取分组权限
└─────────────────────────────────┘
```

### 7.2 核心方法详解

#### 7.2.1 check_user_permission - 权限检查

```python
def check_user_permission(
    db: Session, 
    admin_user_id: int, 
    api_path: str, 
    method: str = "POST"
) -> bool:
    """
    检查用户是否有某个API的权限
    
    流程：
    1. 获取用户所有角色
    2. 获取角色的所有权限（包括effect和priority）
    3. 匹配请求路径（支持通配符）
    4. 按优先级排序
    5. 应用最高优先级规则
    6. 默认拒绝（无匹配规则时）
    """
    # 1. 获取用户角色
    role_ids = get_user_roles(db, admin_user_id)
    if not role_ids:
        return False
    
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
        # 检查方法匹配
        if perm.method != "*" and perm.method != method:
            continue
        
        # 检查路径匹配
        if perm.resource_pattern == api_path or \
           match_pattern(perm.resource_pattern, api_path):
            for rp in role_permissions:
                if rp.permission_id == perm.id:
                    matched_rules.append((rp.effect, rp.priority))
    
    # 5. 无匹配规则，默认拒绝
    if not matched_rules:
        return False
    
    # 6. 按优先级排序（降序），相同优先级时 deny 优先
    matched_rules.sort(
        key=lambda x: (x[1], 0 if x[0] == "deny" else 1), 
        reverse=True
    )
    
    # 7. 应用最高优先级规则
    return matched_rules[0][0] == "allow"
```

#### 7.2.2 get_role_permissions_grouped - 获取角色分组权限

```python
def get_role_permissions_grouped(
    db: Session, 
    role_id: int
) -> RolePermissionsGroupedResponse:
    """
    获取角色的分组权限信息
    
    返回结构：
    {
        "role_id": 1,
        "groups": [
            {
                "group_key": "admin_users",
                "group_name": "用户管理",
                "group_permission": {
                    "id": 1,
                    "name": "用户管理",
                    "effect": "allow",
                    "priority": 0
                },
                "children": [
                    {
                        "id": 2,
                        "name": "用户列表",
                        "effect": "allow",
                        "is_inherited": true
                    },
                    {
                        "id": 3,
                        "name": "删除用户",
                        "effect": "deny",
                        "is_inherited": false,
                        "is_overridden": true
                    }
                ]
            }
        ]
    }
    """
```


---

## 八、中间件实现

### 8.1 认证中间件流程

```python
class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件
    1. 验证 JWT Token
    2. 提取用户信息
    3. 检查用户状态
    4. 验证 API 权限
    """
    
    # 不需要认证的路径
    EXCLUDE_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/admin/auth/login",
        "/api/admin/auth/register",
        "/api/admin/auth/captcha",
        "/api/admin/system_info/config"
    ]
    
    async def dispatch(self, request: Request, call_next):
        # 1. 检查是否需要认证
        if self._should_skip_auth(request.url.path):
            return await call_next(request)
        
        # 2. 获取并验证 Token
        token = self._get_token_from_header(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "未提供认证令牌"}
            )
        
        payload = decode_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "无效的认证令牌"}
            )
        
        # 3. 注入用户信息到 request.state
        request.state.user_id = payload.get("user_id")
        request.state.username = payload.get("username")
        request.state.is_superuser = payload.get("is_superuser", False)
        
        # 4. 检查用户是否被禁用
        user = AdminUserService.get_by_id(db, user_id)
        if user and not user.is_active:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "账户已被禁用"}
            )
        
        # 5. 超级管理员跳过权限验证
        if not request.state.is_superuser:
            has_permission = await self._check_api_permission(
                request, 
                request.state.user_id
            )
            if not has_permission:
                return JSONResponse(
                    status_code=403,
                    content={"code": 403, "message": "无权访问该接口"}
                )
        
        # 6. 继续处理请求
        return await call_next(request)
```

### 8.2 权限检查方法

```python
async def _check_api_permission(
    self, 
    request: Request, 
    user_id: int
) -> PermissionCheckResult:
    """
    检查用户是否有访问该API的权限
    返回详细的权限检查结果，包含来源信息
    """
    api_path = request.url.path
    method = request.method
    
    # 调用 RBAC 服务检查权限（返回详细结果）
    return AdminRBACService.check_permission_detail(
        db, 
        user_id, 
        api_path, 
        method
    )
```

### 8.3 403 响应格式

当用户被拒绝访问时，返回详细的 403 响应：

```json
{
    "code": 403,
    "message": "无权访问该接口",
    "data": {
        "path": "/api/admin/users/delete/1",
        "method": "POST",
        "deny_reason": "拒绝于角色[普通管理员]的子权限[禁止删除用户]"
    }
}
```

deny_reason 可能的格式：
- `允许于角色[角色名]的组权限[权限名]`
- `允许于角色[角色名]的子权限[权限名]`
- `允许于用户权限覆盖`
- `拒绝于角色[角色名]的组权限[权限名]`
- `拒绝于角色[角色名]的子权限[权限名]`
- `拒绝于用户权限覆盖`
- `拒绝于无权限配置`

---

## 九、API 接口清单

### 9.1 权限管理接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/admin/permissions/list` | GET | 获取权限列表（分页） |
| `/api/admin/permissions/detail/{id}` | GET | 获取权限详情 |
| `/api/admin/permissions/create` | POST | 创建权限 |
| `/api/admin/permissions/update/{id}` | POST | 更新权限 |
| `/api/admin/permissions/delete/{id}` | POST | 删除权限 |
| `/api/admin/permissions/groups` | GET | 获取分组权限列表 |

### 9.2 角色权限管理接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/admin/roles/{role_id}/permissions/grouped` | GET | 获取角色分组权限 |
| `/api/admin/roles/{role_id}/permissions-detail` | GET | 获取角色权限详情（含来源追踪）★新增 |
| `/api/admin/roles/{role_id}/permissions/assign` | POST | 分配权限给角色 |
| `/api/admin/roles/{role_id}/permissions/remove` | POST | 移除角色权限 |
| `/api/admin/roles/{role_id}/group-permissions` | GET | 获取角色组权限列表 |
| `/api/admin/roles/{role_id}/non-group-permissions` | GET | 获取角色非组权限列表 |
| `/api/admin/roles/{role_id}/assign-group-permissions` | POST | 分配组权限 |
| `/api/admin/roles/{role_id}/assign-non-group-permissions` | POST | 分配非组权限 |

### 9.3 用户权限管理接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/admin/admin-users/{user_id}/roles` | GET | 获取用户角色 |
| `/api/admin/admin-users/{user_id}/roles` | POST | 分配用户角色 |
| `/api/admin/admin-users/{user_id}/permissions` | GET | 获取用户权限 |
| `/api/admin/admin-users/{user_id}/permissions-detail` | GET | 获取用户权限详情（含来源追踪）★新增 |
| `/api/admin/admin-users/{user_id}/permission-overrides` | GET | 获取用户权限覆盖 |
| `/api/admin/admin-users/{user_id}/permission-overrides` | POST | 设置用户权限覆盖 |
| `/api/admin/admin-users/{user_id}/permission-overrides/{id}` | DELETE | 删除权限覆盖 |


---

## 十、使用示例

### 10.1 创建组权限

```json
POST /api/admin/permissions/create
{
    "name": "用户管理",
    "resource_pattern": "/api/admin/users/**",
    "method": "*",
    "group_key": "admin_users",
    "group_name": "用户管理",
    "is_group": true,
    "description": "用户管理模块的所有权限"
}
```

### 10.2 创建子权限

```json
POST /api/admin/permissions/create
{
    "name": "用户列表",
    "resource_pattern": "/api/admin/users/list",
    "method": "GET",
    "group_key": "admin_users",
    "group_name": "用户管理",
    "is_group": false,
    "description": "查看用户列表"
}
```

### 10.3 为角色分配权限

```json
POST /api/admin/roles/1/permissions/assign
[
    {
        "permission_id": 1,
        "effect": "allow",
        "priority": 0
    },
    {
        "permission_id": 5,
        "effect": "deny",
        "priority": 10
    }
]
```

### 10.4 设置用户权限覆盖

```json
POST /api/admin/admin-users/1/permission-overrides
{
    "permission_id": 5,
    "effect": "ALLOW"
}
```

---

## 十一、权限同步工具

### 11.1 从 OpenAPI 同步权限

系统提供了自动从 FastAPI 应用的 OpenAPI 规范同步权限的脚本：

```bash
# 预览模式（不实际修改数据库）
python script/sync_permissions_from_openapi.py --dry-run

# 实际同步
python script/sync_permissions_from_openapi.py

# 详细输出
python script/sync_permissions_from_openapi.py --verbose
```

### 11.2 同步逻辑

```
┌─────────────────────────────────────────────────────────────────────┐
│                        权限同步流程                                  │
└─────────────────────────────────────────────────────────────────────┘

1. 读取 FastAPI 应用的 OpenAPI 规范
   └── 获取所有 API 路径和方法

2. 解析 API 路径
   ├── 提取 group_key（从路径前缀）
   ├── 生成权限名称
   └── 确定 HTTP 方法

3. 与数据库比对
   ├── 新增的权限 → 创建
   ├── 已存在的权限 → 更新（可选）
   └── 已删除的权限 → 标记删除（可选）

4. 自动创建组权限
   └── 为每个 group_key 创建对应的组权限
```

---

## 十二、最佳实践

### 12.1 权限设计原则

1. **最小权限原则**：默认拒绝，只授予必要的权限
2. **分组管理**：使用组权限批量管理相关 API
3. **优先级控制**：合理使用 priority 实现精细控制
4. **覆盖谨慎**：用户权限覆盖应作为例外情况使用

### 12.2 角色设计建议

```
推荐的角色层级：

超级管理员 (is_superuser=true)
└── 拥有所有权限，跳过权限检查

系统管理员
├── 用户管理（组权限）
├── 角色管理（组权限）
├── 权限管理（组权限）
└── 系统配置（组权限）

普通管理员
├── 用户管理（组权限）
│   └── 删除用户（deny，覆盖）
└── 内容管理（组权限）

只读用户
└── 所有列表/详情接口（allow）
    └── 所有创建/更新/删除接口（deny）
```

### 12.3 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 403 无权限 | 未分配角色 | 检查用户角色分配 |
| 403 无权限 | 权限未激活 | 检查权限 status=1 |
| 403 无权限 | 路径不匹配 | 检查 resource_pattern |
| 权限继承失效 | group_key 不一致 | 确保组权限和子权限 group_key 相同 |
| 覆盖不生效 | priority 设置错误 | 确保覆盖权限的 priority 更高 |

---

## 十三、附录

### 13.1 数据模型定义

```python
# AdminPermission 模型
class AdminPermission(Base):
    __tablename__ = "admin_permissions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    resource_pattern = Column(String(255), nullable=False)
    method = Column(String(10), default="POST")
    group_key = Column(String(100))
    group_name = Column(String(100))
    is_group = Column(Boolean, default=False)
    description = Column(Text)
    status = Column(Integer, default=1)

# AdminRolePermission 模型
class AdminRolePermission(Base):
    __tablename__ = "admin_role_permissions"
    
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, nullable=False)
    permission_id = Column(Integer, nullable=False)
    effect = Column(String(10), default="allow")
    priority = Column(Integer, default=0)

# AdminUserPermissionOverride 模型
class AdminUserPermissionOverride(Base):
    __tablename__ = "admin_user_permission_overrides"
    
    id = Column(Integer, primary_key=True)
    admin_user_id = Column(Integer, nullable=False)
    permission_id = Column(Integer, nullable=False)
    effect = Column(Enum(EffectType), nullable=False)
```

### 13.2 相关文件清单

| 文件路径 | 说明 |
|----------|------|
| `app/models/admin_permission.py` | 权限数据模型 |
| `app/models/admin_role_permission.py` | 角色权限关联模型 |
| `app/models/admin_user_permission_override.py` | 用户权限覆盖模型 |
| `app/schemas/admin_permission.py` | 权限 Schema 定义 |
| `app/services/admin_rbac_service.py` | RBAC 核心服务 |
| `app/services/admin_permission_service.py` | 权限服务 |
| `app/middleware/auth.py` | 认证中间件 |
| `app/api/admin/permissions.py` | 权限 API 接口 |
| `app/api/admin/roles.py` | 角色 API 接口 |
| `script/sync_permissions_from_openapi.py` | 权限同步脚本 |

---

*文档版本: 1.0*
*最后更新: 2026-01-27*
