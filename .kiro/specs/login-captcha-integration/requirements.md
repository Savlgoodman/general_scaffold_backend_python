# Requirements Document

## Introduction

本文档定义了登录验证码集成功能的需求。该功能将集成 easy-captcha-python 库，为管理员登录接口添加图形验证码验证，并重构 Redis 键名管理系统，实现统一的键名规范和配置管理。

## Glossary

- **Captcha_Service**: 验证码服务，负责生成和验证图形验证码
- **Redis_Key_Manager**: Redis 键名管理器，提供统一的键名生成和管理功能
- **Auth_API**: 认证接口模块，处理登录、注册等认证相关请求
- **SpecCaptcha**: easy-captcha-python 库提供的 PNG 类型验证码生成器
- **Captcha_Key**: 验证码的唯一标识符，用于在 Redis 中存储和检索验证码
- **Captcha_Code**: 验证码的文本内容，用户需要输入此内容进行验证
- **Base64_Image**: Base64 编码的图片数据，用于前后端分离项目传输图片

## Requirements

### Requirement 1: Redis 键名规范管理

**User Story:** 作为开发者，我想要有一个统一的 Redis 键名管理系统，以便规范化键名格式并避免键名冲突。

#### Acceptance Criteria

1. THE Redis_Key_Manager SHALL 提供枚举或类来定义所有 Redis 键名模式
2. THE Redis_Key_Manager SHALL 支持验证码键名格式 "admin:captcha:{key}"
3. THE Redis_Key_Manager SHALL 支持参数化键名生成，允许动态插入变量
4. THE Redis_Key_Manager SHALL 提供方法生成完整的 Redis 键名
5. THE Redis_Key_Manager SHALL 支持配置键名前缀，便于不同环境隔离
6. THE Redis_Key_Manager SHALL 提供键名过期时间的统一配置
7. WHEN 生成键名时 THEN THE Redis_Key_Manager SHALL 确保键名格式符合规范

### Requirement 2: 验证码生成接口

**User Story:** 作为前端开发者，我想要获取验证码图片和对应的 key，以便在登录表单中展示验证码。

#### Acceptance Criteria

1. WHEN 请求生成验证码 THEN THE Auth_API SHALL 创建一个 SpecCaptcha 实例
2. THE Captcha_Service SHALL 生成宽度 130px、高度 48px、长度 5 位的验证码
3. WHEN 生成验证码 THEN THE Captcha_Service SHALL 生成唯一的 captcha_key（使用 UUID）
4. WHEN 生成验证码 THEN THE Captcha_Service SHALL 将验证码文本存储到 Redis
5. THE Captcha_Service SHALL 使用 Redis_Key_Manager 生成标准化的键名
6. THE Captcha_Service SHALL 设置验证码在 Redis 中的过期时间为 5 分钟
7. WHEN 存储验证码 THEN THE Captcha_Service SHALL 将验证码文本转换为小写存储
8. THE Auth_API SHALL 返回 captcha_key 和 Base64 编码的验证码图片
9. THE Auth_API SHALL 使用 SpecCaptcha 的 to_base64() 方法生成 Base64 图片数据
10. WHEN 返回响应 THEN THE Auth_API SHALL 使用统一的 Response 格式

### Requirement 3: 登录验证码校验

**User Story:** 作为管理员，我想要在登录时输入验证码，以便增强账户安全性。

#### Acceptance Criteria

1. WHEN 用户提交登录请求 THEN THE Auth_API SHALL 要求提供 captcha_key 和 captcha_code 参数
2. THE Auth_API SHALL 在验证用户名密码之前先验证验证码
3. WHEN 验证验证码 THEN THE Captcha_Service SHALL 使用 captcha_key 从 Redis 获取存储的验证码
4. WHEN 验证验证码 THEN THE Captcha_Service SHALL 将用户输入的 captcha_code 转换为小写进行比较
5. IF captcha_key 不存在或已过期 THEN THE Auth_API SHALL 返回错误 "验证码已过期或不存在"
6. IF captcha_code 不匹配 THEN THE Auth_API SHALL 返回错误 "验证码错误"
7. WHEN 验证码验证成功 THEN THE Captcha_Service SHALL 立即从 Redis 删除该验证码（防止重复使用）
8. WHEN 验证码验证失败 THEN THE Captcha_Service SHALL 保留验证码在 Redis 中（允许重试直到过期）
9. WHEN 验证码验证成功 THEN THE Auth_API SHALL 继续执行用户名密码验证
10. THE Auth_API SHALL 在验证码错误时返回 400 状态码

### Requirement 4: 验证码配置管理

**User Story:** 作为系统管理员，我想要能够配置验证码的参数，以便根据需求调整验证码的复杂度和有效期。

#### Acceptance Criteria

1. THE System SHALL 在配置文件中支持验证码宽度配置（默认 130）
2. THE System SHALL 在配置文件中支持验证码高度配置（默认 48）
3. THE System SHALL 在配置文件中支持验证码长度配置（默认 5）
4. THE System SHALL 在配置文件中支持验证码过期时间配置（默认 300 秒）
5. THE Captcha_Service SHALL 从配置文件读取验证码参数
6. WHEN 配置文件中不存在验证码配置 THEN THE Captcha_Service SHALL 使用默认值

### Requirement 5: 错误处理和日志记录

**User Story:** 作为开发者，我想要详细的错误日志，以便排查验证码相关的问题。

#### Acceptance Criteria

1. WHEN Redis 连接失败 THEN THE Captcha_Service SHALL 记录错误日志并返回友好的错误信息
2. WHEN 验证码生成失败 THEN THE Captcha_Service SHALL 记录错误日志并返回 500 状态码
3. WHEN 验证码验证失败 THEN THE Captcha_Service SHALL 记录警告日志包含失败原因
4. THE Captcha_Service SHALL 使用 app_logger 记录所有验证码操作
5. THE Captcha_Service SHALL 记录验证码生成、验证成功、验证失败的统计信息

### Requirement 6: 接口规范遵循

**User Story:** 作为开发者，我需要遵循项目的接口开发规范，以保持代码的一致性和可维护性。

#### Acceptance Criteria

1. THE Auth_API SHALL 仅使用 GET 和 POST 方法
2. THE Auth_API SHALL 使用 GET 方法获取验证码
3. THE Auth_API SHALL 使用 POST 方法进行登录验证
4. THE Auth_API SHALL 使用统一的 Response 响应格式
5. THE Auth_API SHALL 在 tags 中使用英文描述
6. THE Auth_API SHALL 将业务逻辑委托给 Captcha_Service
7. THE Captcha_Service SHALL 处理所有验证码生成、存储和验证逻辑
8. THE Auth_API SHALL 保持代码简洁，仅包含参数处理、服务调用和响应返回

### Requirement 7: 向后兼容性

**User Story:** 作为系统维护者，我想要确保新功能不会破坏现有的 Redis 使用，以便平滑过渡到新的键名管理系统。

#### Acceptance Criteria

1. WHEN 引入 Redis_Key_Manager THEN THE System SHALL 保持现有 Redis 功能正常工作
2. THE Redis_Key_Manager SHALL 不影响现有的 Redis 连接和操作
3. THE System SHALL 逐步迁移现有 Redis 键名到新的规范格式
4. THE Redis_Key_Manager SHALL 提供清晰的文档说明键名规范和使用方法
