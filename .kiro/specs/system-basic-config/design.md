# Design Document

## Overview

系统基本信息管理功能提供了一个灵活的键值对存储机制，用于管理系统级别的配置信息。该功能采用标准的三层架构设计：API 层、Service 层和 Model 层，遵循项目现有的开发规范和最佳实践。

核心设计理念：
- 使用键值对模式存储配置，支持灵活扩展
- 提供默认值机制，确保系统在配置缺失时仍能正常运行
- 支持批量更新操作，提高管理效率
- 遵循项目的 RESTful API 规范和代码风格

## Architecture

系统采用分层架构设计：

```
┌─────────────────────────────────────┐
│   API Layer (system_info.py)       │  ← 接口层：参数验证、权限控制、响应格式化
├─────────────────────────────────────┤
│   Service Layer (service.py)       │  ← 业务层：业务逻辑、数据处理、默认值管理
├─────────────────────────────────────┤
│   Model Layer (model.py)            │  ← 数据层：ORM 模型定义
├─────────────────────────────────────┤
│   Database (PostgreSQL)             │  ← 持久化存储
└─────────────────────────────────────┘
```

**层次职责：**
- **API Layer**: 处理 HTTP 请求，验证参数，调用 Service，格式化响应
- **Service Layer**: 实现业务逻辑，处理数据库操作，管理默认配置
- **Model Layer**: 定义数据结构，映射数据库表
- **Database**: 持久化存储配置数据


## Components and Interfaces

### 1. Database Model (app/models/admin_system_config.py)

**AdminSystemConfig 模型**

```python
class AdminSystemConfig(Base):
    __tablename__ = "admin_system_config"
    
    id: Integer (Primary Key)
    config_key: String(100) (Unique, Indexed, Not Null)
    config_value: Text (Nullable)
    description: String(255) (Nullable)
    # created_at, updated_at, is_deleted 由 Base 基类提供
```

**字段说明：**
- `id`: 主键，自增
- `config_key`: 配置键，唯一索引，用于标识配置项（如 "site_name", "version"）
- `config_value`: 配置值，使用 Text 类型支持长文本
- `description`: 配置项描述，便于管理员理解配置用途

### 2. Schema Definitions (app/schemas/system_info.py)

**SystemConfigResponse**
```python
class SystemConfigResponse(BaseModel):
    config_key: str
    config_value: str
    description: Optional[str]
```

**SystemConfigUpdateRequest**
```python
class SystemConfigUpdateRequest(BaseModel):
    configs: List[SystemConfigItem]

class SystemConfigItem(BaseModel):
    config_key: str
    config_value: str
    description: Optional[str] = None
```

**SystemConfigBatchResponse**
```python
class SystemConfigBatchResponse(BaseModel):
    configs: Dict[str, str]  # key-value pairs
```

### 3. Service Layer (app/services/system_info_service.py)

在现有的 `SystemInfoService` 类中添加以下方法：

**get_system_config(db: Session) -> Dict[str, str]**
- 功能：获取所有系统配置项
- 返回：配置键值对字典
- 默认值：如果数据库为空，返回预定义的默认配置

**update_system_config(db: Session, configs: List[Dict]) -> Dict[str, str]**
- 功能：批量更新或创建配置项
- 参数：配置项列表
- 逻辑：对每个配置项，如果存在则更新，不存在则创建
- 返回：更新后的所有配置

**DEFAULT_CONFIGS 常量**
```python
DEFAULT_CONFIGS = {
    "site_name": "通用后台管理系统",
    "version": "1.0.0",
    "last_update_date": "2024-01-01"
}
```


### 4. API Layer (app/api/admin/system_info.py)

在现有的 router 中添加以下端点：

**GET /api/admin/system_info/config**
- 功能：获取系统基本配置信息
- 权限：需要管理员认证
- 响应：`Response[SystemConfigBatchResponse]`
- 逻辑流程：
  1. 验证管理员身份
  2. 调用 `SystemInfoService.get_system_config(db)`
  3. 返回配置字典

**POST /api/admin/system_info/config**
- 功能：更新系统基本配置信息
- 权限：需要管理员认证
- 请求体：`SystemConfigUpdateRequest`
- 响应：`Response[SystemConfigBatchResponse]`
- 逻辑流程：
  1. 验证管理员身份
  2. 验证请求参数（config_key 不能为空）
  3. 调用 `SystemInfoService.update_system_config(db, configs)`
  4. 返回更新后的配置

## Data Models

### AdminSystemConfig 表结构

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | Integer | Primary Key, Auto Increment | 主键 |
| config_key | String(100) | Unique, Not Null, Indexed | 配置键 |
| config_value | Text | Nullable | 配置值 |
| description | String(255) | Nullable | 配置描述 |
| created_at | DateTime | Not Null, Default Now | 创建时间 |
| updated_at | DateTime | Not Null, Default Now, On Update | 更新时间 |
| is_deleted | Boolean | Not Null, Default False, Indexed | 软删除标记 |

**索引设计：**
- PRIMARY KEY: `id`
- UNIQUE INDEX: `config_key` (用于快速查找和防止重复)
- INDEX: `is_deleted` (由 Base 基类自动创建，用于软删除查询)

**预定义配置项：**
- `site_name`: 站点名称
- `version`: 系统版本号
- `last_update_date`: 最后更新日期


## Correctness Properties

*属性（Property）是关于系统行为的形式化陈述，它应该在所有有效执行中保持为真。属性是人类可读规范和机器可验证正确性保证之间的桥梁。通过属性测试，我们可以验证系统在各种输入下的正确性。*

### Property 1: 配置获取返回键值对格式
*对于任意*数据库状态，调用获取配置接口应该返回字典格式的键值对数据
**Validates: Requirements 1.1**

### Property 2: 默认配置完整性
*对于任意*空数据库状态，获取配置应该返回包含所有预定义默认配置项（site_name, version, last_update_date）的字典
**Validates: Requirements 1.2, 1.3, 1.4, 1.5**

### Property 3: 更新操作的幂等性
*对于任意*配置项，使用相同的值连续更新两次，第二次更新后的结果应该与第一次相同（除了 updated_at 时间戳）
**Validates: Requirements 2.2**

### Property 4: 创建新配置的正确性
*对于任意*不存在的配置键，执行更新操作后，该配置项应该存在于数据库中，且值与请求中的值相同
**Validates: Requirements 2.3**

### Property 5: 批量更新的原子性
*对于任意*配置项列表，批量更新操作应该更新所有提供的配置项，返回的配置字典应该包含所有更新后的值
**Validates: Requirements 2.4, 2.5**

### Property 6: 响应格式一致性
*对于任意*API 调用（成功或失败），响应应该符合统一的 Response 格式，包含 code、message 和 data 字段
**Validates: Requirements 4.3**

### Property 7: 配置键唯一性约束
*对于任意*已存在的配置键，尝试创建具有相同键的新记录应该失败或更新现有记录，而不是创建重复记录
**Validates: Requirements 3.2, 3.6**


## Error Handling

### API Layer 错误处理

**认证错误 (401)**
- 场景：未提供有效的认证令牌
- 处理：由 `get_current_admin_user` 依赖自动处理
- 响应：HTTP 401 Unauthorized

**参数验证错误 (400)**
- 场景：请求参数不符合 Schema 定义（如 config_key 为空）
- 处理：由 Pydantic 自动验证，FastAPI 自动返回错误
- 响应：HTTP 400 Bad Request，包含详细的验证错误信息

**服务层错误 (500)**
- 场景：数据库操作失败、未预期的异常
- 处理：在 Service 层捕获异常，记录日志，返回错误信息
- 响应：HTTP 500 Internal Server Error

### Service Layer 错误处理

**数据库操作异常**
```python
try:
    # 数据库操作
except Exception as e:
    app_logger.error(f"操作失败: {str(e)}")
    # 返回错误信息或抛出自定义异常
```

**默认值处理**
- 当数据库查询为空时，返回 DEFAULT_CONFIGS
- 确保系统在配置缺失时仍能正常运行

### 日志记录策略

- 所有异常都应该使用 `app_logger.error()` 记录
- 记录内容应包含：操作类型、错误信息、相关参数
- 示例：`app_logger.error(f"更新配置失败 [{config_key}]: {str(e)}")`


## Testing Strategy

### 双重测试方法

本功能将采用单元测试和属性测试相结合的方式，确保全面的测试覆盖：

**单元测试 (Unit Tests)**
- 测试特定的示例和边缘情况
- 验证默认配置项的存在性
- 测试权限控制（未认证访问被拒绝）
- 测试数据库模型结构（字段存在性、约束）
- 测试错误处理（401, 400, 500 状态码）
- 测试唯一索引约束（重复键插入失败）

**属性测试 (Property-Based Tests)**
- 验证通用属性在各种输入下都成立
- 使用随机生成的配置数据测试 API 行为
- 测试批量更新的正确性
- 测试响应格式的一致性
- 最小 100 次迭代以确保充分覆盖

### 测试框架

- **测试框架**: pytest
- **属性测试库**: Hypothesis (Python 的属性测试库)
- **测试文件位置**: `tests/test_system_config.py`

### 属性测试配置

每个属性测试必须：
1. 使用 `@given` 装饰器定义输入生成策略
2. 运行最少 100 次迭代（Hypothesis 默认配置）
3. 使用注释标记对应的设计属性

**标记格式示例**:
```python
# Feature: system-basic-config, Property 1: 配置获取返回键值对格式
@given(...)
def test_config_returns_dict_format(...):
    ...
```

### 测试覆盖目标

- **API 层**: 测试所有端点的正常流程和异常流程
- **Service 层**: 测试业务逻辑、默认值处理、数据库操作
- **Model 层**: 测试模型定义、约束、继承关系
- **集成测试**: 测试完整的请求-响应流程

### 测试数据策略

**单元测试数据**:
- 使用固定的测试数据（如 "test_site", "1.0.0"）
- 测试边缘情况（空字符串、None、超长字符串）

**属性测试数据**:
- 使用 Hypothesis 策略生成随机配置键值对
- 配置键：1-50 字符的字母数字字符串
- 配置值：0-1000 字符的任意字符串
- 批量更新：1-20 个配置项的列表

### 测试隔离

- 每个测试使用独立的数据库事务
- 测试结束后回滚事务，确保数据库清洁
- 使用 pytest fixtures 管理测试数据库会话
