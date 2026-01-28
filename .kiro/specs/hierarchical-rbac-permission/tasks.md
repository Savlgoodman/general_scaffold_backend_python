# Implementation Plan: Hierarchical RBAC Permission System

## Overview

本实现计划将层级化RBAC权限系统的设计转换为可执行的开发任务。实现将分为以下几个阶段：数据模型更新、服务层增强、API接口开发、中间件实现、工具脚本开发、数据迁移和测试。每个任务都引用了具体的需求，确保可追溯性。

## Tasks

- [x] 1. 更新数据模型以支持通配符和分组
  - [x] 1.1 修改 AdminPermission 模型添加新字段
    - 添加 resource_pattern 字段（替代 api_path）
    - 添加 method 字段
    - 添加 group_key 和 group_name 字段
    - 添加 is_group 布尔字段
    - 添加 description 字段（替代 remark）
    - 为 resource_pattern 添加唯一索引
    - 为 group_key 添加普通索引
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [x] 1.2 修改 AdminRolePermission 模型添加 effect 和 priority
    - 添加 effect 字段（VARCHAR(10)，默认"allow"）
    - 添加 priority 字段（INTEGER，默认0）
    - 添加唯一约束 (role_id, permission_id)
    - _Requirements: 2.1, 2.2_
  
  - [x] 1.3 更新 database.py 确保新模型被注册
    - 验证 init_db() 函数包含更新后的模型
    - _Requirements: 1.1, 2.1_

- [ ]* 1.4 为数据模型编写属性测试
  - [ ]* 1.4.1 测试 Property 1: Wildcard Pattern Storage and Retrieval
    - **Property 1: Wildcard Pattern Storage and Retrieval**
    - **Validates: Requirements 1.1, 1.2**
  
  - [ ]* 1.4.2 测试 Property 2: Permission Data Integrity
    - **Property 2: Permission Data Integrity**
    - **Validates: Requirements 1.3, 1.4**

- [x] 2. 更新 Pydantic Schemas
  - [x] 2.1 更新 AdminPermissionCreate schema
    - 将 api_path 改为 resource_pattern
    - 添加 method, group_key, group_name, is_group 字段
    - 将 remark 改为 description
    - _Requirements: 1.1, 1.3, 1.4_
  
  - [x] 2.2 更新 AdminPermissionUpdate schema
    - 同步 Create schema 的字段更改
    - 所有字段设为 Optional
    - _Requirements: 1.1_
  
  - [x] 2.3 更新 AdminPermissionResponse schema
    - 添加所有新字段到响应模型
    - 保持 from_attributes=True 配置
    - _Requirements: 1.1, 9.7_
  
  - [x] 2.4 创建新的 schema 类型
    - 创建 PermissionAssignment schema (permission_id, effect, priority)
    - 创建 PermissionWithEffect schema
    - 创建 PermissionGroup schema
    - 创建 RolePermissionsGroupedResponse schema
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 3. 实现通配符模式匹配功能
  - [x] 3.1 在 AdminPermissionService 中添加 match_pattern 方法
    - 使用 fnmatch 模块实现通配符匹配
    - 支持 * 和 ** 通配符
    - 处理精确匹配和模式匹配
    - _Requirements: 6.3, 9.2_

- [ ]* 3.2 为模式匹配编写属性测试
  - [ ]* 3.2.1 测试 Property 21: Pattern Matching Correctness
    - **Property 21: Pattern Matching Correctness**
    - **Validates: Requirements 6.3**

- [x] 4. 增强 AdminPermissionService
  - [x] 4.1 更新 get_by_api_path 方法支持双重查询
    - 支持精确匹配 resource_pattern
    - 支持通配符模式匹配
    - 保持向后兼容性
    - _Requirements: 9.2_
  
  - [x] 4.2 添加 get_by_resource_pattern 方法
    - 根据 resource_pattern 精确查询
    - _Requirements: 1.1_
  
  - [x] 4.3 更新 get_list 方法支持新的过滤条件
    - 添加 group_key 过滤参数
    - 添加 is_group 过滤参数
    - 保持现有的 keyword 和 status 过滤
    - _Requirements: 7.2, 7.3, 7.4_
  
  - [x] 4.4 添加 get_grouped_permissions 方法
    - 按 group_key 分组返回权限
    - 返回 Dict[str, List[AdminPermission]]
    - _Requirements: 4.1_
  
  - [x] 4.5 更新 create 方法
    - 检查 resource_pattern 唯一性（替代 api_path）
    - 自动检测通配符并设置 is_group
    - _Requirements: 1.1, 1.2_
  
  - [x] 4.6 更新 update 方法
    - 支持更新新字段
    - 检查 resource_pattern 唯一性
    - _Requirements: 1.1_

- [ ]* 4.7 为 AdminPermissionService 编写属性测试
  - [ ]* 4.7.1 测试 Property 3: Mixed Permission Query Completeness
    - **Property 3: Mixed Permission Query Completeness**
    - **Validates: Requirements 1.5**
  
  - [ ]* 4.7.2 测试 Property 22: Query Filter Correctness
    - **Property 22: Query Filter Correctness**
    - **Validates: Requirements 7.2, 7.3, 7.4**
  
  - [ ]* 4.7.3 测试 Property 23: Query Response Completeness
    - **Property 23: Query Response Completeness**
    - **Validates: Requirements 7.5**

- [x] 5. Checkpoint - 确保数据模型和基础服务测试通过
  - 确保所有测试通过，询问用户是否有问题

- [x] 6. 增强 AdminRBACService 支持 effect 和 priority
  - [x] 6.1 更新 get_user_permissions 方法
    - 返回权限时包含 effect 和 priority 信息
    - 创建新方法 get_user_permissions_with_effect
    - _Requirements: 2.1, 2.2_
  
  - [x] 6.2 重写 check_user_permission 方法实现优先级逻辑
    - 获取用户所有角色的权限
    - 匹配请求路径（支持通配符）
    - 收集所有匹配的规则（effect + priority）
    - 按 priority 降序排序
    - 应用最高优先级规则
    - 默认拒绝（无匹配规则时）
    - _Requirements: 2.3, 2.4, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [x] 6.3 添加 get_role_permissions_grouped 方法
    - 查询角色的所有权限
    - 按 group_key 分组
    - 包含 effect, priority, is_inherited, is_overridden 信息
    - 返回 RolePermissionsGroupedResponse 格式
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1.1, 5.1.2, 5.1.3, 5.1.4_
  
  - [x] 6.4 添加 assign_role_permissions 方法
    - 接受 List[PermissionAssignment]
    - 批量创建角色-权限关联
    - 验证 permission_id 存在性
    - 防止重复关联
    - 设置默认 effect 和 priority
    - _Requirements: 5.1, 5.2, 5.5, 5.6_
  
  - [x] 6.5 添加 remove_role_permissions 方法
    - 接受 permission_ids 列表
    - 逻辑删除角色-权限关联
    - _Requirements: 5.4_
  
  - [x] 6.6 添加 calculate_effective_permission 方法
    - 计算特定 API 路径的有效权限
    - 考虑所有匹配规则和优先级
    - _Requirements: 5.1.5_

- [ ]* 6.7 为 AdminRBACService 编写属性测试
  - [ ]* 6.7.1 测试 Property 4: Effect Value Validation
    - **Property 4: Effect Value Validation**
    - **Validates: Requirements 2.1**
  
  - [ ]* 6.7.2 测试 Property 5: Priority-Based Rule Selection
    - **Property 5: Priority-Based Rule Selection**
    - **Validates: Requirements 2.3, 6.4, 6.5**
  
  - [ ]* 6.7.3 测试 Property 6: Default Priority Assignment
    - **Property 6: Default Priority Assignment**
    - **Validates: Requirements 2.5**
  
  - [ ]* 6.7.4 测试 Property 13: Override Flag Accuracy
    - **Property 13: Override Flag Accuracy**
    - **Validates: Requirements 4.3, 5.1.3**
  
  - [ ]* 6.7.5 测试 Property 14: Inheritance Flag Accuracy
    - **Property 14: Inheritance Flag Accuracy**
    - **Validates: Requirements 4.4, 5.1.4**
  
  - [ ]* 6.7.6 测试 Property 15: Effective Permission Calculation
    - **Property 15: Effective Permission Calculation**
    - **Validates: Requirements 5.1.5**

- [x] 7. 更新权限管理 API 接口
  - [x] 7.1 更新 GET /permissions/list 接口
    - 添加 group_key 查询参数
    - 添加 is_group 查询参数
    - 更新响应使用新的 schema
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [x] 7.2 更新 GET /permissions/detail/{id} 接口
    - 更新响应使用新的 schema
    - _Requirements: 7.6_
  
  - [x] 7.3 更新 POST /permissions/create 接口
    - 使用更新后的 AdminPermissionCreate schema
    - _Requirements: 1.1_
  
  - [x] 7.4 更新 POST /permissions/update/{id} 接口
    - 使用更新后的 AdminPermissionUpdate schema
    - _Requirements: 1.1_
  
  - [x] 7.5 添加 GET /permissions/groups 接口
    - 返回按分组组织的权限列表
    - 调用 AdminPermissionService.get_grouped_permissions
    - _Requirements: 4.1_

- [ ]* 7.6 为权限管理 API 编写集成测试
  - 测试所有端点的正常流程和错误情况
  - _Requirements: 9.6_

- [x] 8. 创建角色权限管理 API 接口
  - [x] 8.1 创建 GET /roles/{role_id}/permissions 接口
    - 返回角色的分组权限信息
    - 调用 AdminRBACService.get_role_permissions_grouped
    - _Requirements: 4.1, 5.8_
  
  - [x] 8.2 创建 POST /roles/{role_id}/permissions/assign 接口
    - 接受 List[PermissionAssignment]
    - 调用 AdminRBACService.assign_role_permissions
    - _Requirements: 5.1, 5.7_
  
  - [x] 8.3 创建 POST /roles/{role_id}/permissions/remove 接口
    - 接受 permission_ids 列表
    - 调用 AdminRBACService.remove_role_permissions
    - _Requirements: 5.4_

- [ ]* 8.4 为角色权限管理 API 编写集成测试
  - 测试权限分配、查询和移除流程
  - _Requirements: 5.1, 5.4_

- [x] 9. Checkpoint - 确保所有 API 接口测试通过
  - 确保所有测试通过，询问用户是否有问题

- [x] 10. 创建 PermissionSyncService
  - [x] 10.1 实现 extract_routes_from_app 方法
    - 遍历 FastAPI app.routes
    - 提取 path, method, tags, summary
    - 返回 List[RouteInfo]
    - _Requirements: 3.2, 3.3_
  
  - [x] 10.2 实现 generate_group_key 方法
    - 从 tags 或 path 前缀生成 group_key
    - 确保一致性（相同输入产生相同输出）
    - _Requirements: 3.6_
  
  - [x] 10.3 实现 create_group_permissions 方法
    - 为每个唯一的 group_key 创建通配符权限
    - 设置 is_group=True
    - _Requirements: 3.7_
  
  - [x] 10.4 实现 sync_permissions 方法
    - 对比现有权限和提取的路由
    - 创建新权限
    - 更新已变更的权限
    - 不删除已存在但未找到的权限
    - 返回同步结果统计
    - _Requirements: 3.4, 3.5, 3.8_

- [ ]* 10.5 为 PermissionSyncService 编写属性测试
  - [ ]* 10.5.1 测试 Property 7: Route Metadata Extraction Completeness
    - **Property 7: Route Metadata Extraction Completeness**
    - **Validates: Requirements 3.3**
  
  - [ ]* 10.5.2 测试 Property 8: Sync Idempotence
    - **Property 8: Sync Idempotence**
    - **Validates: Requirements 3.4, 3.5**
  
  - [ ]* 10.5.3 测试 Property 9: Group Key Generation Consistency
    - **Property 9: Group Key Generation Consistency**
    - **Validates: Requirements 3.6**
  
  - [ ]* 10.5.4 测试 Property 10: Automatic Group Permission Creation
    - **Property 10: Automatic Group Permission Creation**
    - **Validates: Requirements 3.7**

- [x] 11. 创建 OpenAPI 同步脚本
  - [x] 11.1 创建 script/sync_permissions_from_openapi.py
    - 加载 FastAPI 应用
    - 调用 PermissionSyncService.extract_routes_from_app
    - 连接数据库
    - 调用 PermissionSyncService.sync_permissions
    - 输出同步结果（added, updated, unchanged）
    - 处理错误和异常
    - _Requirements: 3.1, 3.8_
  
  - [x] 11.2 添加命令行参数支持
    - --dry-run: 预览模式，不实际修改数据库
    - --verbose: 详细输出
    - _Requirements: 3.1_

- [ ]* 11.3 测试同步脚本
  - 创建测试 FastAPI 应用
  - 运行同步脚本
  - 验证权限被正确创建
  - _Requirements: 3.2, 3.4_

- [x] 12. 实现权限检查中间件
  - [x] 12.1 创建 PermissionCheckMiddleware
    - 提取请求路径和方法
    - 提取用户信息（从 JWT token）
    - 检查白名单路径（如 /auth/login）
    - 调用 AdminRBACService.check_user_permission
    - 允许或拒绝请求（403 Forbidden）
    - 记录访问日志
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  
  - [x] 12.2 在 FastAPI 应用中注册中间件
    - 在 app/core/app.py 中添加中间件
    - 配置白名单路径
    - _Requirements: 6.1_

- [ ]* 12.3 为权限检查中间件编写集成测试
  - 测试有权限的请求被允许
  - 测试无权限的请求被拒绝
  - 测试白名单路径不受限制
  - _Requirements: 6.1, 6.6, 6.7_

- [x] 13. Checkpoint - 确保同步和中间件功能正常
  - 确保所有测试通过，询问用户是否有问题

- [x] 14. 创建数据迁移脚本
  - [x] 14.1 创建 script/migrate_permissions.py
    - 备份现有数据
    - 读取所有现有 admin_permissions 记录
    - 转换 api_path 到 resource_pattern
    - 从 api_path 生成 group_key
    - 设置 is_group=False
    - 保留原有 ID
    - 更新所有记录
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [x] 14.2 迁移 admin_role_permissions 表
    - 为所有现有关联设置 effect="allow"
    - 为所有现有关联设置 priority=0
    - 保留原有 ID 和关联关系
    - _Requirements: 8.5, 8.6_
  
  - [x] 14.3 添加回滚功能
    - 使用事务确保原子性
    - 提供回滚脚本
    - _Requirements: 8.1_
  
  - [x] 14.4 添加验证功能
    - 迁移后验证数据完整性
    - 检查 ID 是否保留
    - 检查关联关系是否完整
    - _Requirements: 8.6_

- [ ]* 14.5 为数据迁移编写属性测试
  - [ ]* 14.5.1 测试 Property 24: Migration Group Key Generation
    - **Property 24: Migration Group Key Generation**
    - **Validates: Requirements 8.3**
  
  - [ ]* 14.5.2 测试 Property 25: Migration ID Preservation
    - **Property 25: Migration ID Preservation**
    - **Validates: Requirements 8.6**

- [x] 15. 实现向后兼容性适配
  - [x] 15.1 在 AdminPermissionService 中添加适配器方法
    - 添加 get_by_api_path_legacy 方法
    - 支持同时查询 api_path 和 resource_pattern
    - _Requirements: 9.1, 9.2_
  
  - [x] 15.2 更新 AdminRBACService 的权限检查
    - 支持同时评估旧格式和新格式权限
    - 确保现有功能不受影响
    - _Requirements: 9.3, 9.4_

- [ ]* 15.3 为向后兼容性编写属性测试
  - [ ]* 15.3.1 测试 Property 26: Backward Compatible Path Lookup
    - **Property 26: Backward Compatible Path Lookup**
    - **Validates: Requirements 9.2**
  
  - [ ]* 15.3.2 测试 Property 27: Dual Format Permission Check
    - **Property 27: Dual Format Permission Check**
    - **Validates: Requirements 9.4**

- [ ] 16. 编写单元测试
  - [ ] 16.1 为 AdminPermissionService 编写单元测试
    - 测试 CRUD 操作
    - 测试过滤和查询
    - 测试错误情况
    - _Requirements: 1.1, 7.2, 7.3, 7.4_
  
  - [ ] 16.2 为 AdminRBACService 编写单元测试
    - 测试权限检查逻辑
    - 测试优先级排序
    - 测试分组查询
    - 测试权限分配和移除
    - _Requirements: 2.3, 4.1, 5.1, 5.4_
  
  - [ ] 16.3 为 PermissionSyncService 编写单元测试
    - 测试路由提取
    - 测试 group_key 生成
    - 测试同步逻辑
    - _Requirements: 3.2, 3.3, 3.6_
  
  - [ ] 16.4 为通配符匹配编写参数化测试
    - 测试各种通配符模式
    - 测试边界情况
    - _Requirements: 6.3_

- [x] 17. Final Checkpoint - 运行所有测试并验证
  - 运行所有单元测试
  - 运行所有属性测试
  - 运行所有集成测试
  - 确保测试覆盖率达标
  - 询问用户是否有问题或需要调整

- [x] 18. 文档和部署准备
  - [x] 18.1 更新 README 文档
    - 说明新的权限系统特性
    - 提供迁移指南
    - 提供同步脚本使用说明
    - _Requirements: 3.1, 8.1_
  
  - [x] 18.2 创建 API 文档
    - 更新 OpenAPI 文档
    - 添加新接口的示例
    - _Requirements: 5.1, 5.7, 5.8_
  
  - [x] 18.3 准备部署清单
    - 数据库迁移步骤
    - 配置更新说明
    - 回滚计划
    - _Requirements: 8.1_

## Notes

- 标记 `*` 的任务为可选任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求，确保可追溯性
- Checkpoint 任务用于确保增量验证
- 属性测试使用 Hypothesis 框架，每个测试至少运行 100 次迭代
- 单元测试和属性测试是互补的，共同确保系统正确性
