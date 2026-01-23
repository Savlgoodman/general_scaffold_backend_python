# Implementation Plan: System Basic Config

## Overview

本实施计划将系统基本信息管理功能分解为一系列增量式的开发任务。实施顺序遵循从底层到上层的原则：首先创建数据库模型，然后实现 Service 层业务逻辑，最后添加 API 接口。每个主要功能完成后都包含相应的测试任务。

## Tasks

- [x] 1. 创建数据库模型和 Schema 定义
  - 创建 `app/models/admin_system_config.py` 文件
  - 定义 `AdminSystemConfig` 模型，包含 id, config_key, config_value, description 字段
  - 在 config_key 字段上添加唯一索引
  - 在 `app/core/database.py` 的 `init_db()` 函数中导入新模型
  - 在 `app/schemas/system_info.py` 中添加 Schema 定义：`SystemConfigResponse`, `SystemConfigUpdateRequest`, `SystemConfigItem`, `SystemConfigBatchResponse`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ]* 1.1 编写数据库模型单元测试
  - 测试模型字段存在性
  - 测试 config_key 唯一约束
  - 测试继承自 Base 的字段（created_at, updated_at, is_deleted）
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 2. 实现 Service 层业务逻辑
  - [x] 2.1 在 `app/services/system_info_service.py` 中添加 DEFAULT_CONFIGS 常量
    - 定义默认配置：site_name, version, last_update_date
    - _Requirements: 1.5_

  - [x] 2.2 实现 get_system_config 方法
    - 查询数据库获取所有未删除的配置项
    - 如果数据库为空，返回 DEFAULT_CONFIGS
    - 将结果转换为字典格式 {config_key: config_value}
    - 添加异常处理和日志记录
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 5.5_

  - [x] 2.3 实现 update_system_config 方法
    - 接收配置项列表作为参数
    - 对每个配置项，检查是否存在（通过 config_key 查询）
    - 如果存在则更新 config_value 和 description
    - 如果不存在则创建新记录
    - 提交数据库事务
    - 返回更新后的所有配置（调用 get_system_config）
    - 添加异常处理和日志记录
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 5.1, 5.5_

- [ ]* 2.4 编写 Service 层单元测试
  - 测试空数据库返回默认配置
  - 测试更新已存在配置项
  - 测试创建新配置项
  - 测试批量更新多个配置项
  - 测试数据库异常处理
  - _Requirements: 1.5, 2.2, 2.3, 2.4, 5.1_


- [x] 3. 实现 API 接口
  - [x] 3.1 在 `app/api/admin/system_info.py` 中添加 GET /config 接口
    - 定义路由：`@router.get("/config")`
    - 添加管理员认证依赖：`get_current_admin_user`
    - 添加数据库会话依赖：`get_db`
    - 调用 `SystemInfoService.get_system_config(db)`
    - 返回 `Response[SystemConfigBatchResponse]` 格式
    - 添加接口文档说明（summary 和 docstring）
    - _Requirements: 1.1, 1.6, 4.1, 4.3, 4.7_

  - [x] 3.2 在 `app/api/admin/system_info.py` 中添加 POST /config 接口
    - 定义路由：`@router.post("/config")`
    - 添加管理员认证依赖：`get_current_admin_user`
    - 添加数据库会话依赖：`get_db`
    - 接收 `SystemConfigUpdateRequest` 请求体
    - 验证 config_key 不为空（Pydantic 自动验证）
    - 调用 `SystemInfoService.update_system_config(db, request.configs)`
    - 返回 `Response[SystemConfigBatchResponse]` 格式
    - 添加接口文档说明（summary 和 docstring）
    - _Requirements: 2.1, 2.6, 2.7, 4.2, 4.3, 4.7_

- [ ]* 3.3 编写 API 层单元测试
  - 测试 GET /config 接口正常流程
  - 测试 POST /config 接口正常流程
  - 测试未认证访问返回 401
  - 测试无效参数返回 400
  - 测试响应格式符合 Response 模型
  - _Requirements: 1.6, 2.6, 4.3, 5.2, 5.3_

- [x] 4. Checkpoint - 基本功能验证
  - 确保所有测试通过
  - 手动测试 API 接口（使用 Swagger UI 或 Postman）
  - 验证数据库表已正确创建
  - 如有问题，请向用户反馈

- [ ]* 5. 编写属性测试
  - [ ]* 5.1 编写属性测试：配置获取返回键值对格式
    - **Property 1: 配置获取返回键值对格式**
    - **Validates: Requirements 1.1**
    - 使用 Hypothesis 生成随机配置数据
    - 验证返回结果是字典类型
    - 验证所有键值对格式正确

  - [ ]* 5.2 编写属性测试：默认配置完整性
    - **Property 2: 默认配置完整性**
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
    - 在空数据库上调用 get_system_config
    - 验证返回包含 site_name, version, last_update_date

  - [ ]* 5.3 编写属性测试：更新操作的幂等性
    - **Property 3: 更新操作的幂等性**
    - **Validates: Requirements 2.2**
    - 生成随机配置项
    - 连续更新两次相同的值
    - 验证第二次结果与第一次相同（忽略 updated_at）

  - [ ]* 5.4 编写属性测试：创建新配置的正确性
    - **Property 4: 创建新配置的正确性**
    - **Validates: Requirements 2.3**
    - 生成随机的不存在的配置键
    - 执行更新操作
    - 验证配置项已创建且值正确

  - [ ]* 5.5 编写属性测试：批量更新的原子性
    - **Property 5: 批量更新的原子性**
    - **Validates: Requirements 2.4, 2.5**
    - 生成随机数量（1-20）的配置项列表
    - 执行批量更新
    - 验证所有配置项都已更新

  - [ ]* 5.6 编写属性测试：响应格式一致性
    - **Property 6: 响应格式一致性**
    - **Validates: Requirements 4.3**
    - 对各种 API 调用（成功和失败）
    - 验证响应包含 code, message, data 字段

  - [ ]* 5.7 编写属性测试：配置键唯一性约束
    - **Property 7: 配置键唯一性约束**
    - **Validates: Requirements 3.2, 3.6**
    - 创建配置项后尝试创建相同键的配置
    - 验证不会创建重复记录

- [x] 6. 最终检查点
  - 确保所有测试（单元测试和属性测试）通过
  - 验证代码符合项目规范（仅使用 GET/POST、统一响应格式等）
  - 检查日志记录是否完整
  - 如有问题，请向用户反馈

## Notes

- 任务标记 `*` 的为可选任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号，便于追溯
- 检查点任务确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证具体示例和边缘情况
