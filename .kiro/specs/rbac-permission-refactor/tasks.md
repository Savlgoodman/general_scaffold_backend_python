# Implementation Plan: RBAC 权限系统重构

## Overview

本实现计划将 RBAC 权限系统重构为统一的权限计算架构，提供权限来源追踪和详细的 403 错误信息。

## Tasks

- [x] 1. 新增权限相关的 Schema 定义
  - [x] 1.1 在 app/schemas/admin_permission.py 中新增 SourceType 枚举
    - 定义 GROUP_PERMISSION、SINGLE_PERMISSION、USER_OVERRIDE、NO_PERMISSION 四种类型
    - _Requirements: 1.1_

  - [x] 1.2 新增 PermissionSource 模型
    - 包含 type、role_id、role_name、permission_id、permission_name 字段
    - 实现 get_description 方法，生成人类可读的描述
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.3 新增 PermissionDetailItem 模型
    - 包含权限详情字段和来源信息
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 1.4 新增 PermissionGroupDetail 模型
    - 包含 group_key、group_name、group_permission、children
    - _Requirements: 3.5, 4.5_

  - [x] 1.5 新增 RolePermissionsDetailResponse 和 UserPermissionsDetailResponse 模型
    - _Requirements: 7.2, 8.2_

  - [x] 1.6 新增 PermissionCheckResult 模型
    - 包含 allowed、effect、source、deny_reason 字段
    - _Requirements: 5.2, 5.3, 5.4, 5.5_

- [x] 2. 实现核心权限计算方法
  - [x] 2.1 实现 get_role_permissions_detail 方法
    - 获取角色的所有权限关联
    - 处理组权限和子权限继承
    - 处理子权限覆盖
    - 按 group_key 分组返回
    - 为每个权限生成来源信息
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 2.2 编写 get_role_permissions_detail 的单元测试
    - 测试只有组权限的情况
    - 测试组权限 + 子权限覆盖的情况
    - **Property 2: 角色组权限继承正确性**
    - **Property 3: 角色子权限覆盖正确性**
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.6**

  - [x] 2.3 实现 get_user_permissions_detail 方法
    - 获取用户的所有角色
    - 调用 get_role_permissions_detail 获取每个角色的权限
    - 合并多角色权限（allow 优先于 deny）
    - 应用用户权限覆盖
    - 按 group_key 分组返回
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 2.4 编写 get_user_permissions_detail 的单元测试
    - 测试单角色用户
    - 测试多角色用户权限合并
    - 测试用户权限覆盖
    - **Property 5: 多角色权限合并 - Allow 优先**
    - **Property 6: 用户权限覆盖优先级**
    - **Validates: Requirements 4.3, 4.4**

  - [x] 2.5 实现 check_permission 方法
    - 调用 get_user_permissions_detail 获取用户权限
    - 匹配请求路径（支持通配符）
    - 返回 PermissionCheckResult 对象
    - 当拒绝时生成 deny_reason
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 2.6 编写 check_permission 的单元测试
    - 测试允许访问的情况
    - 测试各种拒绝原因
    - **Property 7: 权限检查结果完整性**
    - **Validates: Requirements 5.1, 5.6**

- [x] 3. Checkpoint - 核心方法测试通过
  - 确保所有单元测试通过，ask the user if questions arise.

- [x] 4. 新增 API 接口
  - [x] 4.1 在 app/api/admin/roles.py 中新增角色权限详情接口
    - GET /api/admin/roles/{role_id}/permissions-detail
    - 调用 get_role_permissions_detail 方法
    - 返回 RolePermissionsDetailResponse
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 4.2 在 app/api/admin/admin_users.py 中新增用户权限详情接口
    - GET /api/admin/admin-users/{user_id}/permissions-detail
    - 调用 get_user_permissions_detail 方法
    - 返回 UserPermissionsDetailResponse
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 5. 重构认证中间件
  - [x] 5.1 修改 app/middleware/auth.py 使用新的 check_permission 方法
    - 替换原有的 _check_api_permission 方法
    - 使用 PermissionCheckResult 获取详细信息
    - _Requirements: 9.3, 9.4_

  - [x] 5.2 修改 403 响应格式
    - 在 data 中包含 path、method、deny_reason 字段
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 6. Checkpoint - API 和中间件测试
  - 确保新接口正常工作，403 响应格式正确，ask the user if questions arise.

- [x] 7. 代码清理和优化
  - [x] 7.1 标记或移除旧的冗余方法
    - 检查 AdminRBACService 中的旧方法
    - 保留向后兼容的方法，添加废弃注释
    - _Requirements: 9.5_

  - [x] 7.2 更新相关文档
    - 更新 docs/RBAC-SYSTEM-ARCHITECTURE.md
    - 添加新方法的使用说明

- [x] 8. Final Checkpoint - 完整测试
  - 确保所有测试通过，功能正常，ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
