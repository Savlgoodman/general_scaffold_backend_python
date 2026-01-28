# Requirements Document

## Introduction

本文档定义了层级化RBAC权限系统的需求。该系统旨在提供灵活的API权限管理能力，支持通配符模式的权限分组、细粒度的权限控制（allow/deny机制）、以及从OpenAPI规范自动同步权限的能力。系统将为管理员提供直观的分组视图，同时支持对特定API进行例外控制。

## Glossary

- **Permission_System**: 权限管理系统，负责管理API权限和角色权限关联
- **Resource_Pattern**: 资源模式，支持通配符的API路径表达式，如 `/system/logs/*`
- **Permission_Group**: 权限组，具有相同group_key的权限集合
- **Effect**: 权限效果，表示允许（allow）或拒绝（deny）访问
- **Priority**: 优先级，用于解决权限冲突，数值越大优先级越高
- **OpenAPI_Spec**: FastAPI自动生成的OpenAPI规范文档
- **Permission_Checker**: 权限检查器，负责在运行时验证用户是否有权限访问特定API

## Requirements

### Requirement 1: 权限模型支持通配符和分组

**User Story:** 作为系统管理员，我希望能够使用通配符模式来批量管理API权限，这样我可以快速为角色分配整个模块的权限而不需要逐个选择。

#### Acceptance Criteria

1. THE Permission_System SHALL support resource patterns with wildcards such as `/system/logs/*`
2. WHEN a permission is created with a wildcard pattern, THE Permission_System SHALL mark it as a group permission
3. THE Permission_System SHALL store group_key for organizing permissions into logical groups
4. THE Permission_System SHALL store group_name for displaying human-readable group names
5. WHEN querying permissions, THE Permission_System SHALL return both group permissions and individual permissions

### Requirement 2: 支持Allow/Deny机制和优先级

**User Story:** 作为系统管理员，我希望能够为角色分配整个模块的权限，同时禁止访问其中的某些敏感API，这样我可以实现灵活的权限控制。

#### Acceptance Criteria

1. WHEN associating a permission with a role, THE Permission_System SHALL support specifying effect as either "allow" or "deny"
2. WHEN associating a permission with a role, THE Permission_System SHALL support specifying a priority value
3. WHEN checking permissions, THE Permission_System SHALL evaluate all matching rules and apply the highest priority rule
4. IF multiple rules have the same priority, THEN THE Permission_System SHALL prioritize "deny" over "allow"
5. THE Permission_System SHALL set default priority to 0 for "allow" rules and recommend 100+ for "deny" rules

### Requirement 3: 从OpenAPI自动同步权限

**User Story:** 作为开发人员，我希望系统能够自动从FastAPI的路由定义中同步API权限，这样我不需要手动维护权限表，减少人为错误。

#### Acceptance Criteria

1. THE Permission_System SHALL provide a script to extract API routes from FastAPI application
2. WHEN the sync script runs, THE Permission_System SHALL read all registered routes from the FastAPI app
3. WHEN processing routes, THE Permission_System SHALL extract path, method, tags, and summary information
4. WHEN a new route is found, THE Permission_System SHALL create a new permission record in the database
5. WHEN an existing route is found, THE Permission_System SHALL update its metadata if changed
6. THE Permission_System SHALL automatically generate group_key from route tags or path prefixes
7. THE Permission_System SHALL create group permissions (with wildcards) for each unique group_key
8. WHEN the sync completes, THE Permission_System SHALL output a summary of added, updated, and unchanged permissions

### Requirement 4: 权限分组展示和管理

**User Story:** 作为系统管理员，我希望在前端界面中以分组的方式查看和管理角色权限，这样我可以清晰地了解每个角色在各个模块的权限情况。

#### Acceptance Criteria

1. WHEN querying role permissions for display, THE Permission_System SHALL return permissions organized by groups
2. WHEN a role has a group permission, THE Permission_System SHALL include all child permissions in the response
3. WHEN a child permission has an explicit deny rule, THE Permission_System SHALL mark it as overridden
4. THE Permission_System SHALL indicate whether each permission is inherited from group or explicitly set
5. WHEN displaying permissions, THE Permission_System SHALL show group permissions with their child permissions in a hierarchical structure

### Requirement 5: 角色权限分配接口

**User Story:** 作为系统管理员，我希望能够通过API为角色分配权限，包括分配整个权限组或排除特定权限，这样我可以灵活地配置角色权限。

#### Acceptance Criteria

1. THE Permission_System SHALL provide an API to assign permissions to a role
2. WHEN assigning a group permission, THE Permission_System SHALL create an "allow" rule with default priority
3. WHEN excluding a specific permission from a group, THE Permission_System SHALL create a "deny" rule with higher priority
4. WHEN removing a permission assignment, THE Permission_System SHALL delete the corresponding role-permission association
5. THE Permission_System SHALL validate that permission_id exists before creating associations
6. THE Permission_System SHALL prevent duplicate role-permission associations with the same effect
7. THE Permission_System SHALL provide an API to batch assign multiple permissions to a role
8. THE Permission_System SHALL provide an API to query role permissions with grouping information

### Requirement 5.1: 角色权限查询接口增强

**User Story:** 作为系统管理员，我希望查询角色权限时能够看到分组信息和继承关系，这样我可以清楚地了解权限的来源和覆盖情况。

#### Acceptance Criteria

1. WHEN querying role permissions, THE Permission_System SHALL return permissions grouped by group_key
2. WHEN a role has a group permission, THE Permission_System SHALL include all child permissions in the response
3. WHEN a child permission has an explicit deny rule, THE Permission_System SHALL mark it as overridden
4. THE Permission_System SHALL indicate whether each permission is inherited from group or explicitly set
5. THE Permission_System SHALL calculate and return the effective permission status for each API

### Requirement 6: 运行时权限检查

**User Story:** 作为系统，我需要在每个API请求时检查用户是否有权限访问该API，这样可以确保安全性和访问控制。

#### Acceptance Criteria

1. WHEN an API request is received, THE Permission_Checker SHALL extract the request path and method
2. THE Permission_Checker SHALL retrieve all permissions associated with the user's roles
3. THE Permission_Checker SHALL match the request path against all resource patterns (both exact and wildcard)
4. WHEN multiple rules match, THE Permission_Checker SHALL sort them by priority in descending order
5. THE Permission_Checker SHALL apply the highest priority rule to determine access
6. IF no rules match, THEN THE Permission_Checker SHALL deny access by default
7. WHEN access is denied, THE Permission_Checker SHALL return a 403 Forbidden response with a clear error message

### Requirement 7: 权限查询和列表接口

**User Story:** 作为系统管理员，我希望能够查询和浏览所有可用的权限，包括按分组筛选，这样我可以了解系统中有哪些权限可以分配。

#### Acceptance Criteria

1. THE Permission_System SHALL provide an API to list all permissions with pagination
2. WHEN listing permissions, THE Permission_System SHALL support filtering by group_key
3. WHEN listing permissions, THE Permission_System SHALL support filtering by is_group flag
4. WHEN listing permissions, THE Permission_System SHALL support filtering by status
5. THE Permission_System SHALL return permissions with their group information
6. THE Permission_System SHALL provide an API to get permission details by ID

### Requirement 8: 数据迁移和向后兼容

**User Story:** 作为开发人员，我需要将现有的权限数据迁移到新的表结构，这样可以保留历史数据并平滑过渡。

#### Acceptance Criteria

1. THE Permission_System SHALL provide a migration script to convert existing admin_permissions data
2. WHEN migrating, THE Permission_System SHALL convert api_path to resource_pattern
3. WHEN migrating, THE Permission_System SHALL generate group_key from api_path prefixes
4. WHEN migrating, THE Permission_System SHALL set is_group to False for all existing permissions
5. WHEN migrating existing role-permission associations, THE Permission_System SHALL set effect to "allow" and priority to 0
6. THE Permission_System SHALL preserve all existing permission IDs and associations during migration

### Requirement 9: 现有接口适配和兼容

**User Story:** 作为开发人员，我需要确保新的权限系统能够与现有的所有接口和服务兼容，这样可以避免破坏现有功能。

#### Acceptance Criteria

1. THE Permission_System SHALL maintain compatibility with existing AdminPermissionService methods
2. WHEN existing services call get_by_api_path, THE Permission_System SHALL support both exact match and pattern match
3. THE Permission_System SHALL update AdminRBACService to support the new effect and priority fields
4. WHEN checking permissions, THE Permission_System SHALL evaluate both legacy api_path and new resource_pattern
5. THE Permission_System SHALL provide adapter methods to convert between old and new data structures
6. THE Permission_System SHALL ensure all existing API endpoints continue to work without modification
7. THE Permission_System SHALL update response schemas to include new fields while maintaining backward compatibility
8. WHEN frontend requests permission data, THE Permission_System SHALL return data in a format that supports both old and new UI implementations
