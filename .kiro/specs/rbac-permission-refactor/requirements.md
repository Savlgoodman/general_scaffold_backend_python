# Requirements Document

## Introduction

本需求文档描述 RBAC 权限系统的重构方案，目标是统一权限计算逻辑，提供权限来源追踪，并优化 403 错误信息的详细程度。重构后的系统将提供两个核心方法：获取角色详细权限和获取用户详细权限，这两个方法将被中间件、角色权限管理、用户权限管理等模块复用。

## Glossary

- **Permission_Calculator**: 权限计算器，负责计算角色或用户的最终权限
- **Permission_Source**: 权限来源，描述权限是从哪里获得或被拒绝的
- **Permission_Result**: 单个权限的计算结果，包含权限信息和来源
- **Permission_Check_Result**: 权限检查结果，用于中间件验证
- **Group_Permission**: 组权限，is_group=True 的权限，使用通配符模式
- **Single_Permission**: 子权限/单个权限，is_group=False 的具体 API 权限
- **User_Override**: 用户权限覆盖，优先级最高的权限设置
- **Role_Permission**: 角色权限，通过角色分配的权限

## Requirements

### Requirement 1: 权限来源数据结构

**User Story:** As a 系统管理员, I want 查看权限的来源信息, so that 我能了解某个权限是从哪里获得或被拒绝的。

#### Acceptance Criteria

1. THE Permission_Source SHALL 包含来源类型字段，支持以下值：group_permission（组权限）、single_permission（子权限）、user_override（用户覆盖）、no_permission（无权限配置）
2. THE Permission_Source SHALL 包含角色ID和角色名称字段（当来源是角色权限时）
3. THE Permission_Source SHALL 包含权限ID和权限名称字段
4. THE Permission_Source SHALL 提供人类可读的描述方法，生成如"允许于角色[管理员]的组权限[用户管理]"的描述文本


### Requirement 2: 权限结果数据结构

**User Story:** As a 开发者, I want 获取权限的完整计算结果, so that 我能在 API 响应中展示详细的权限信息。

#### Acceptance Criteria

1. THE Permission_Result SHALL 包含权限ID、权限名称、资源模式、HTTP方法、分组标识
2. THE Permission_Result SHALL 包含最终效果字段（allow/deny）
3. THE Permission_Result SHALL 包含 Permission_Source 对象，描述权限来源
4. THE Permission_Result SHALL 包含 is_inherited 字段，标识是否从组权限继承
5. THE Permission_Result SHALL 包含 is_overridden 字段，标识是否被子权限或用户覆盖

### Requirement 3: 角色权限详情计算

**User Story:** As a 系统管理员, I want 查看角色的完整权限详情（按分组展示）, so that 我能了解该角色拥有哪些权限及其来源。

#### Acceptance Criteria

1. WHEN 调用获取角色权限详情方法时 THEN Permission_Calculator SHALL 首先获取角色的所有组权限
2. WHEN 角色拥有某个组权限时 THEN Permission_Calculator SHALL 将该组下所有子权限标记为继承（is_inherited=True），效果继承自组权限
3. WHEN 角色同时拥有组权限和该组下的子权限时 THEN Permission_Calculator SHALL 使用子权限的效果覆盖组权限的效果
4. WHEN 子权限的效果与组权限不同时 THEN Permission_Calculator SHALL 将子权限标记为被覆盖（is_overridden=True）
5. THE Permission_Calculator SHALL 按 group_key 分组返回所有权限，每个分组包含组权限和子权限列表
6. THE Permission_Calculator SHALL 为每个权限提供来源信息，格式为"允许/拒绝于角色[角色名]的组权限/子权限[权限名]"

### Requirement 4: 用户权限详情计算

**User Story:** As a 系统管理员, I want 查看用户的完整权限详情（按分组展示）, so that 我能了解该用户最终拥有哪些权限及其来源。

#### Acceptance Criteria

1. WHEN 调用获取用户权限详情方法时 THEN Permission_Calculator SHALL 首先获取用户的所有角色
2. WHEN 用户拥有多个角色时 THEN Permission_Calculator SHALL 合并所有角色的权限
3. WHEN 同一权限在多个角色中存在且效果冲突时 THEN Permission_Calculator SHALL 以 allow 为最高优先级（allow 优先于 deny）
4. WHEN 用户有权限覆盖记录时 THEN Permission_Calculator SHALL 应用用户覆盖，覆盖优先级高于角色权限
5. THE Permission_Calculator SHALL 按 group_key 分组返回所有权限
6. THE Permission_Calculator SHALL 为每个权限提供来源信息，包括：
   - "允许于角色[角色名]的组权限[权限名]"
   - "允许于角色[角色名]的子权限[权限名]"
   - "允许于用户权限覆盖"
   - "拒绝于角色[角色名]的组权限[权限名]"
   - "拒绝于角色[角色名]的子权限[权限名]"
   - "拒绝于用户权限覆盖"
   - "拒绝于无权限配置"

### Requirement 5: 权限检查方法重构

**User Story:** As a 系统, I want 使用统一的权限检查方法, so that 中间件和其他模块可以复用相同的逻辑。

#### Acceptance Criteria

1. WHEN 检查用户是否有某个 API 权限时 THEN Permission_Calculator SHALL 返回 Permission_Check_Result 对象
2. THE Permission_Check_Result SHALL 包含 allowed 布尔字段，表示是否允许访问
3. THE Permission_Check_Result SHALL 包含 effect 字段（allow/deny）
4. THE Permission_Check_Result SHALL 包含 Permission_Source 对象，描述权限来源
5. THE Permission_Check_Result SHALL 包含 deny_reason 字段，当拒绝时提供人类可读的拒绝原因
6. WHEN 用户被拒绝访问时 THEN deny_reason SHALL 包含具体的拒绝来源，如"拒绝于角色[普通管理员]的子权限[禁止删除用户]"

### Requirement 6: 403 响应格式优化

**User Story:** As a 前端开发者, I want 在 403 响应中获取详细的拒绝原因, so that 我能向用户展示更有意义的错误信息。

#### Acceptance Criteria

1. WHEN 用户被拒绝访问 API 时 THEN 中间件 SHALL 返回包含详细信息的 403 响应
2. THE 403 响应 SHALL 包含 path 字段，表示被拒绝的 API 路径
3. THE 403 响应 SHALL 包含 method 字段，表示 HTTP 方法
4. THE 403 响应 SHALL 包含 deny_reason 字段，描述具体的拒绝原因
5. IF 拒绝原因是角色权限 THEN deny_reason SHALL 格式为"拒绝于角色[角色名]的组权限/子权限[权限名]"
6. IF 拒绝原因是用户覆盖 THEN deny_reason SHALL 格式为"拒绝于用户权限覆盖"
7. IF 拒绝原因是无权限配置 THEN deny_reason SHALL 格式为"拒绝于无权限配置"

### Requirement 7: 角色权限详情 API 接口

**User Story:** As a 前端开发者, I want 调用 API 获取角色的权限详情, so that 我能在角色管理页面展示权限分配情况。

#### Acceptance Criteria

1. THE System SHALL 提供 GET /api/admin/roles/{role_id}/permissions-detail 接口
2. THE 接口 SHALL 返回按 group_key 分组的权限列表
3. THE 每个分组 SHALL 包含 group_key、group_name、group_permission（组权限）、children（子权限列表）
4. THE 每个权限项 SHALL 包含 id、name、resource_pattern、method、effect、source、is_inherited、is_overridden
5. THE 接口 SHALL 不需要分页，返回完整的权限列表

### Requirement 8: 用户权限详情 API 接口

**User Story:** As a 前端开发者, I want 调用 API 获取用户的权限详情, so that 我能在用户管理页面展示权限分配情况。

#### Acceptance Criteria

1. THE System SHALL 提供 GET /api/admin/admin-users/{user_id}/permissions-detail 接口
2. THE 接口 SHALL 返回按 group_key 分组的权限列表
3. THE 每个分组 SHALL 包含 group_key、group_name、group_permission（组权限）、children（子权限列表）
4. THE 每个权限项 SHALL 包含 id、name、resource_pattern、method、effect、source、is_inherited、is_overridden
5. THE source 字段 SHALL 包含权限来源的详细描述
6. THE 接口 SHALL 不需要分页，返回完整的权限列表

### Requirement 9: 代码复用与统一

**User Story:** As a 开发者, I want 使用统一的权限计算方法, so that 减少代码冗余，方便维护。

#### Acceptance Criteria

1. THE Permission_Calculator SHALL 提供 get_role_permissions_detail 方法，被角色权限管理模块复用
2. THE Permission_Calculator SHALL 提供 get_user_permissions_detail 方法，被用户权限管理模块复用
3. THE Permission_Calculator SHALL 提供 check_permission 方法，被认证中间件复用
4. WHEN 中间件检查权限时 THEN 中间件 SHALL 调用 check_permission 方法而非重复实现逻辑
5. THE 旧的冗余权限计算方法 SHALL 被移除或标记为废弃
