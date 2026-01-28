# Design Document: RBAC 权限系统重构

## Overview

本设计文档描述 RBAC 权限系统的重构方案，核心目标是：
1. 统一权限计算逻辑，提供两个核心方法：`get_role_permissions_detail` 和 `get_user_permissions_detail`
2. 为每个权限提供来源追踪，支持详细的 403 错误信息
3. 减少代码冗余，统一中间件、角色管理、用户管理模块的权限计算逻辑

## Architecture

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           重构后的 RBAC 权限架构                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────────────┐
                              │     Permission Calculator    │
                              │     (核心权限计算器)          │
                              ├─────────────────────────────┤
                              │ + get_role_permissions_detail│
                              │ + get_user_permissions_detail│
                              │ + check_permission           │
                              └──────────────┬──────────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────────────┐
              │                              │                              │
              ▼                              ▼                              ▼
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│    AuthMiddleware       │  │   Roles API             │  │   AdminUsers API        │
│    (认证中间件)          │  │   (角色管理接口)         │  │   (用户管理接口)         │
├─────────────────────────┤  ├─────────────────────────┤  ├─────────────────────────┤
│ 调用 check_permission   │  │ 调用 get_role_          │  │ 调用 get_user_          │
│ 返回详细 403 信息        │  │ permissions_detail      │  │ permissions_detail      │
└─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
```

### 权限计算流程

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           角色权限计算流程                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

输入: role_id
      │
      ▼
┌─────────────────────────────────┐
│ 1. 获取角色的所有权限关联        │
│    AdminRolePermission          │
│    (permission_id, effect,      │
│     priority)                   │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ 2. 获取所有权限详情              │
│    AdminPermission              │
│    区分组权限和子权限            │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ 3. 处理组权限                    │
│    - 获取角色拥有的组权限        │
│    - 记录 effect 和来源         │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ 4. 处理子权限继承                │
│    - 匹配 group_key             │
│    - 继承组权限的 effect        │
│    - 标记 is_inherited=True     │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ 5. 处理子权限覆盖                │
│    - 角色直接拥有的子权限        │
│    - 覆盖继承的 effect          │
│    - 标记 is_overridden=True    │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ 6. 按 group_key 分组返回        │
│    每个权限包含来源信息          │
└─────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           用户权限计算流程                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

输入: user_id
      │
      ▼
┌─────────────────────────────────┐
│ 1. 获取用户的所有角色            │
│    AdminUserRole                │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ 2. 对每个角色调用                │
│    get_role_permissions_detail  │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ 3. 合并多角色权限                │
│    冲突时 allow 优先于 deny     │
│    记录来源角色                  │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ 4. 获取用户权限覆盖              │
│    AdminUserPermissionOverride  │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ 5. 应用用户覆盖                  │
│    覆盖优先级最高                │
│    更新来源为"用户权限覆盖"      │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ 6. 按 group_key 分组返回        │
│    每个权限包含最终来源信息      │
└─────────────────────────────────┘
```

## Components and Interfaces

### 1. 数据结构定义 (app/schemas/admin_permission.py)

```python
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel


class SourceType(str, Enum):
    """权限来源类型"""
    GROUP_PERMISSION = "group_permission"      # 组权限
    SINGLE_PERMISSION = "single_permission"    # 子权限
    USER_OVERRIDE = "user_override"            # 用户覆盖
    NO_PERMISSION = "no_permission"            # 无权限配置


class PermissionSource(BaseModel):
    """权限来源"""
    type: SourceType                           # 来源类型
    role_id: Optional[int] = None              # 角色ID
    role_name: Optional[str] = None            # 角色名称
    permission_id: Optional[int] = None        # 权限ID
    permission_name: Optional[str] = None      # 权限名称
    
    def get_description(self, effect: str) -> str:
        """生成人类可读的描述"""
        effect_text = "允许" if effect == "allow" else "拒绝"
        
        if self.type == SourceType.USER_OVERRIDE:
            return f"{effect_text}于用户权限覆盖"
        elif self.type == SourceType.NO_PERMISSION:
            return "拒绝于无权限配置"
        elif self.type == SourceType.GROUP_PERMISSION:
            return f"{effect_text}于角色[{self.role_name}]的组权限[{self.permission_name}]"
        elif self.type == SourceType.SINGLE_PERMISSION:
            return f"{effect_text}于角色[{self.role_name}]的子权限[{self.permission_name}]"
        return f"{effect_text}于未知来源"


class PermissionDetailItem(BaseModel):
    """权限详情项"""
    id: int
    name: str
    resource_pattern: str
    method: str
    group_key: Optional[str] = None
    group_name: Optional[str] = None
    effect: str                                # allow/deny
    source: PermissionSource                   # 权限来源
    source_description: str                    # 来源描述文本
    is_inherited: bool = False                 # 是否从组权限继承
    is_overridden: bool = False                # 是否被覆盖


class PermissionGroupDetail(BaseModel):
    """权限分组详情"""
    group_key: str
    group_name: str
    group_permission: Optional[PermissionDetailItem] = None  # 组权限
    children: List[PermissionDetailItem] = []                # 子权限列表


class RolePermissionsDetailResponse(BaseModel):
    """角色权限详情响应"""
    role_id: int
    role_name: str
    groups: List[PermissionGroupDetail]


class UserPermissionsDetailResponse(BaseModel):
    """用户权限详情响应"""
    user_id: int
    username: str
    groups: List[PermissionGroupDetail]


class PermissionCheckResult(BaseModel):
    """权限检查结果"""
    allowed: bool                              # 是否允许
    effect: str                                # allow/deny
    source: PermissionSource                   # 权限来源
    deny_reason: Optional[str] = None          # 拒绝原因描述
```

### 2. 核心服务方法 (app/services/admin_rbac_service.py)

```python
class AdminRBACService:
    """管理员RBAC权限服务"""
    
    @staticmethod
    def get_role_permissions_detail(
        db: Session, 
        role_id: int
    ) -> RolePermissionsDetailResponse:
        """
        获取角色的完整权限详情（按分组）
        
        计算逻辑：
        1. 获取角色的所有权限关联
        2. 处理组权限
        3. 处理子权限继承
        4. 处理子权限覆盖
        5. 按 group_key 分组返回
        """
        pass
    
    @staticmethod
    def get_user_permissions_detail(
        db: Session, 
        user_id: int
    ) -> UserPermissionsDetailResponse:
        """
        获取用户的完整权限详情（按分组）
        
        计算逻辑：
        1. 获取用户的所有角色
        2. 对每个角色获取权限详情
        3. 合并多角色权限（allow 优先）
        4. 应用用户权限覆盖
        5. 按 group_key 分组返回
        """
        pass
    
    @staticmethod
    def check_permission(
        db: Session, 
        user_id: int, 
        api_path: str, 
        method: str = "POST"
    ) -> PermissionCheckResult:
        """
        检查用户是否有某个 API 的权限
        
        返回详细的检查结果，包含来源信息
        """
        pass
```

### 3. API 接口

#### 角色权限详情接口
```
GET /api/admin/roles/{role_id}/permissions-detail

Response:
{
    "code": 200,
    "message": "获取成功",
    "data": {
        "role_id": 1,
        "role_name": "普通管理员",
        "groups": [
            {
                "group_key": "admin_users",
                "group_name": "用户管理",
                "group_permission": {
                    "id": 1,
                    "name": "用户管理",
                    "resource_pattern": "/api/admin/users/**",
                    "method": "*",
                    "effect": "allow",
                    "source": {
                        "type": "group_permission",
                        "role_id": 1,
                        "role_name": "普通管理员",
                        "permission_id": 1,
                        "permission_name": "用户管理"
                    },
                    "source_description": "允许于角色[普通管理员]的组权限[用户管理]",
                    "is_inherited": false,
                    "is_overridden": false
                },
                "children": [
                    {
                        "id": 2,
                        "name": "用户列表",
                        "resource_pattern": "/api/admin/users/list",
                        "method": "GET",
                        "effect": "allow",
                        "source": {...},
                        "source_description": "允许于角色[普通管理员]的组权限[用户管理]",
                        "is_inherited": true,
                        "is_overridden": false
                    },
                    {
                        "id": 5,
                        "name": "删除用户",
                        "resource_pattern": "/api/admin/users/delete/*",
                        "method": "POST",
                        "effect": "deny",
                        "source": {...},
                        "source_description": "拒绝于角色[普通管理员]的子权限[删除用户]",
                        "is_inherited": false,
                        "is_overridden": true
                    }
                ]
            }
        ]
    }
}
```

#### 用户权限详情接口
```
GET /api/admin/admin-users/{user_id}/permissions-detail

Response: 结构同上，增加多角色合并和用户覆盖的来源信息
```

#### 403 响应格式
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

## Data Models

### 现有数据模型（无需修改）

- `AdminPermission` - 权限表
- `AdminRolePermission` - 角色权限关联表
- `AdminUserPermissionOverride` - 用户权限覆盖表
- `AdminUserRole` - 用户角色关联表
- `AdminRole` - 角色表


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: PermissionSource 描述格式正确性

*For any* PermissionSource 对象和 effect 值，调用 get_description 方法应返回符合预定义格式的描述文本：
- 当 type 为 USER_OVERRIDE 时，格式为 "{effect_text}于用户权限覆盖"
- 当 type 为 NO_PERMISSION 时，格式为 "拒绝于无权限配置"
- 当 type 为 GROUP_PERMISSION 时，格式为 "{effect_text}于角色[{role_name}]的组权限[{permission_name}]"
- 当 type 为 SINGLE_PERMISSION 时，格式为 "{effect_text}于角色[{role_name}]的子权限[{permission_name}]"

**Validates: Requirements 1.4, 6.5, 6.6, 6.7**

### Property 2: 角色组权限继承正确性

*For any* 角色和该角色拥有的组权限，获取角色权限详情时，该组下所有子权限应满足：
- is_inherited = True
- effect 继承自组权限的 effect
- source.type = GROUP_PERMISSION

**Validates: Requirements 3.2, 3.6**

### Property 3: 角色子权限覆盖正确性

*For any* 角色同时拥有组权限和该组下的子权限时，子权限应满足：
- effect 使用子权限自身的 effect（而非组权限的 effect）
- 当子权限 effect 与组权限不同时，is_overridden = True
- source.type = SINGLE_PERMISSION

**Validates: Requirements 3.3, 3.4**

### Property 4: 权限分组返回正确性

*For any* 角色或用户的权限详情，返回结果应按 group_key 分组，每个分组包含：
- group_key 和 group_name
- group_permission（组权限，可为空）
- children（子权限列表）

**Validates: Requirements 3.5, 4.5, 7.2, 7.3, 8.2, 8.3**

### Property 5: 多角色权限合并 - Allow 优先

*For any* 用户拥有多个角色，且同一权限在不同角色中 effect 冲突时，最终 effect 应为 allow（allow 优先于 deny）

**Validates: Requirements 4.3**

### Property 6: 用户权限覆盖优先级

*For any* 用户有权限覆盖记录时，该权限的最终 effect 应等于覆盖记录的 effect，且 source.type = USER_OVERRIDE

**Validates: Requirements 4.4**

### Property 7: 权限检查结果完整性

*For any* 权限检查调用，返回的 PermissionCheckResult 应包含：
- allowed 布尔值（与 effect 一致）
- effect 为 "allow" 或 "deny"
- source 为有效的 PermissionSource 对象
- 当 allowed = False 时，deny_reason 不为空

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6**

### Property 8: 权限详情项字段完整性

*For any* 权限详情响应中的权限项，应包含以下字段：
- id, name, resource_pattern, method
- effect（"allow" 或 "deny"）
- source（PermissionSource 对象）
- source_description（非空字符串）
- is_inherited, is_overridden（布尔值）

**Validates: Requirements 7.4, 8.4, 8.5**

## Error Handling

### 角色不存在
- 当请求的 role_id 不存在时，返回 404 错误
- 错误信息：`{"code": 404, "message": "角色不存在"}`

### 用户不存在
- 当请求的 user_id 不存在时，返回 404 错误
- 错误信息：`{"code": 404, "message": "管理员用户不存在"}`

### 权限检查失败
- 当用户无权访问 API 时，返回 403 错误
- 错误信息包含详细的拒绝原因

## Testing Strategy

### 单元测试

1. **PermissionSource 测试**
   - 测试各种 SourceType 的 get_description 方法
   - 验证描述格式正确

2. **get_role_permissions_detail 测试**
   - 测试只有组权限的情况
   - 测试只有子权限的情况
   - 测试组权限 + 子权限覆盖的情况
   - 测试无权限的情况

3. **get_user_permissions_detail 测试**
   - 测试单角色用户
   - 测试多角色用户（无冲突）
   - 测试多角色用户（有冲突，验证 allow 优先）
   - 测试用户权限覆盖

4. **check_permission 测试**
   - 测试允许访问的情况
   - 测试拒绝访问的情况（各种拒绝原因）
   - 测试通配符匹配

### 属性测试

使用 Hypothesis 库进行属性测试：
- 测试 Property 1-8 的正确性
- 生成随机的角色、权限、用户数据进行测试

### 集成测试

1. **API 接口测试**
   - 测试 GET /api/admin/roles/{role_id}/permissions-detail
   - 测试 GET /api/admin/admin-users/{user_id}/permissions-detail

2. **中间件测试**
   - 测试 403 响应格式
   - 验证 deny_reason 字段正确
