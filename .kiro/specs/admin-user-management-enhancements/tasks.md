# Implementation Plan: Admin User Management Enhancements

## Overview

本实现计划将管理员用户管理增强功能和系统监控模块分解为可执行的编码任务。实现将分为三个主要部分：
1. Service 层增强（业务逻辑）
2. API 层实现（端点定义）
3. Middleware 修改（用户状态检查）

## Tasks

- [x] 1. 创建系统信息相关的 Schema 定义
  - 创建 `app/schemas/system_info.py` 文件
  - 定义 SystemResourcesResponse、NetworkStatsResponse、RedisStatusResponse、RedisKeyValueResponse、FailedLoginStatsResponse
  - _Requirements: 6.1, 6.2, 7.1, 7.2, 8.1-8.6, 9.1-9.6, 10.1-10.7_

- [ ] 2. 实现 AdminRBACService 的权限和菜单覆盖清除功能
  - [x] 2.1 在 `app/services/admin_rbac_service.py` 中添加 `clear_all_permission_overrides` 方法
    - 实现软删除所有用户的权限覆盖记录
    - _Requirements: 1.1, 1.2_
  
  - [ ]* 2.2 编写属性测试：清除权限覆盖的完整性
    - **Property 1: 清除权限覆盖的完整性**
    - **验证需求：Requirements 1.1, 1.2**
  
  - [x] 2.3 在 `app/services/admin_rbac_service.py` 中添加 `clear_all_menu_overrides` 方法
    - 实现软删除所有用户的菜单覆盖记录
    - _Requirements: 2.1, 2.2_
  
  - [ ]* 2.4 编写属性测试：清除菜单覆盖的完整性
    - **Property 2: 清除菜单覆盖的完整性**
    - **验证需求：Requirements 2.1, 2.2**

- [ ] 3. 实现 AdminRBACService 的完整权限查询功能
  - [x] 3.1 在 `app/services/admin_rbac_service.py` 中添加 `get_user_complete_permissions` 方法
    - 计算用户的完整权限（角色权限并集 + 覆盖）
    - 支持分页和关键词搜索
    - 只返回激活状态的权限
    - _Requirements: 4.1-4.7_
  
  - [ ]* 3.2 编写属性测试：完整权限计算的正确性
    - **Property 4: 完整权限计算的正确性**
    - **验证需求：Requirements 4.2, 4.3, 4.4**
  
  - [ ]* 3.3 编写属性测试：分页一致性
    - **Property 5: 分页一致性**
    - **验证需求：Requirements 4.1, 4.5**

- [ ] 4. 实现 AdminUserService 的用户状态切换功能
  - [x] 4.1 在 `app/services/admin_user_service.py` 中添加 `toggle_status` 方法
    - 实现用户启用/禁用状态切换
    - 更新 is_active 字段和 updated_at 时间戳
    - _Requirements: 5.1, 5.2_
  
  - [ ]* 4.2 编写属性测试：用户状态切换的幂等性
    - **Property 6: 用户状态切换的幂等性**
    - **验证需求：Requirements 5.1, 5.2**
  
  - [ ]* 4.3 编写单元测试：自我禁用保护
    - 测试不能禁用自己的账户的逻辑
    - _Requirements: 5.7_

- [ ] 5. 创建 SystemInfoService 服务
  - [x] 5.1 创建 `app/services/system_info_service.py` 文件
    - 实现 `get_system_resources` 方法（CPU 和内存）
    - 实现 `get_network_stats` 方法（网络统计）
    - 使用 psutil 库获取系统信息
    - _Requirements: 6.1-6.3, 7.1-7.3_
  
  - [ ]* 5.2 编写属性测试：系统资源数据的有效性
    - **Property 9: 系统资源数据的有效性**
    - **验证需求：Requirements 6.1, 6.2**
  
  - [x] 5.3 在 SystemInfoService 中实现 Redis 监控方法
    - 实现 `get_redis_status` 方法（连接状态和基本信息）
    - 实现 `get_redis_keys` 方法（分页查询键值对）
    - 使用 Redis SCAN 命令避免阻塞
    - _Requirements: 8.1-8.7, 9.1-9.7_
  
  - [ ]* 5.4 编写属性测试：Redis 键值查询的模式匹配
    - **Property 10: Redis 键值查询的模式匹配**
    - **验证需求：Requirements 9.2**
  
  - [x] 5.5 在 SystemInfoService 中实现失败登录统计方法
    - 实现 `get_failed_login_stats` 方法
    - 查询 api_logs 表，筛选登录接口的非 200 状态记录
    - 支持时间范围过滤
    - _Requirements: 10.1-10.7_
  
  - [ ]* 5.6 编写属性测试：失败登录统计的准确性
    - **Property 11: 失败登录统计的准确性**
    - **验证需求：Requirements 10.2, 10.3**

- [ ] 6. Checkpoint - 确保所有 Service 层测试通过
  - 确保所有测试通过，如有问题请询问用户

- [ ] 7. 在 admin_users.py 中添加权限和菜单管理端点
  - [x] 7.1 添加清除权限覆盖端点
    - 实现 `clear_permission_overrides` 端点
    - 调用 AdminRBACService.clear_all_permission_overrides
    - 添加用户存在性检查
    - _Requirements: 1.1-1.4_
  
  - [x] 7.2 添加清除菜单覆盖端点
    - 实现 `clear_menu_overrides` 端点
    - 调用 AdminRBACService.clear_all_menu_overrides
    - 添加用户存在性检查
    - _Requirements: 2.1-2.4_
  
  - [x] 7.3 添加查看完整菜单端点
    - 实现 `get_complete_menus` 端点
    - 复用 AdminRBACService.get_user_menus 方法
    - _Requirements: 3.1-3.5_
  
  - [ ]* 7.4 编写属性测试：完整菜单计算的正确性
    - **Property 3: 完整菜单计算的正确性**
    - **验证需求：Requirements 3.1, 3.2, 3.3**
  
  - [x] 7.5 添加查看完整权限端点（分页）
    - 实现 `get_complete_permissions` 端点
    - 调用 AdminRBACService.get_user_complete_permissions
    - 支持分页和关键词搜索参数
    - _Requirements: 4.1-4.7_
  
  - [x] 7.6 添加用户状态切换端点
    - 实现 `toggle_user_status` 端点
    - 调用 AdminUserService.toggle_status
    - 添加自我禁用保护逻辑
    - _Requirements: 5.1-5.7_
  
  - [ ]* 7.7 编写属性测试：自我禁用保护
    - **Property 8: 自我禁用保护**
    - **验证需求：Requirements 5.7**

- [ ] 8. 创建 system_info.py API 模块
  - [x] 8.1 创建 `app/api/admin/system_info.py` 文件
    - 设置 APIRouter，prefix="/system_info", tags=["system info"]
    - 实现 `get_system_resources` 端点
    - 实现 `get_network_stats` 端点
    - _Requirements: 6.1-6.3, 7.1-7.3_
  
  - [x] 8.2 在 system_info.py 中添加 Redis 监控端点
    - 实现 `get_redis_status` 端点
    - 实现 `get_redis_keys` 端点（分页）
    - 添加 Redis 连接失败的错误处理
    - _Requirements: 8.1-8.7, 9.1-9.7_
  
  - [x] 8.3 在 system_info.py 中添加失败登录统计端点
    - 实现 `get_failed_login_stats` 端点
    - 支持时间范围参数
    - 添加日期格式验证
    - _Requirements: 10.1-10.7_
  
  - [ ]* 8.4 编写集成测试：system_info API 端点
    - 测试所有 system_info 端点的集成
    - 使用 TestClient 进行端到端测试

- [ ] 9. 修改认证中间件以支持用户状态检查
  - [x] 9.1 在 `app/middleware/auth.py` 中添加用户状态检查
    - 在 token 验证后查询用户信息
    - 检查 is_active 字段
    - 如果用户被禁用，返回 401 错误
    - _Requirements: 5.3, 5.4_
  
  - [ ]* 9.2 编写属性测试：禁用用户的认证拒绝
    - **Property 7: 禁用用户的认证拒绝**
    - **验证需求：Requirements 5.3, 5.4**

- [x] 10. 在主应用中注册 system_info 路由
  - 在 `app/core/app.py` 中导入并注册 system_info router
  - 确保路由前缀为 `/api/admin/system_info`
  - _Requirements: All system_info requirements_

- [ ] 11. Checkpoint - 确保所有测试通过
  - 运行所有单元测试和属性测试
  - 运行集成测试
  - 确保所有测试通过，如有问题请询问用户

- [x] 12. 更新 requirements.txt
  - 添加 psutil 依赖（如果尚未添加）
  - 添加 hypothesis 依赖用于属性测试（如果尚未添加）

## Notes

- 标记为 `*` 的任务是可选的测试任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求以便追溯
- Checkpoint 任务确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证特定示例和边界情况
- 所有代码应遵循项目的编码规范（参考 projectrules.md）
