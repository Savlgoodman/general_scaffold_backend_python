"""
操作审计日志相关的 Pydantic Schema
用于请求参数校验和响应数据序列化，前端通过 OpenAPI 自动生成对接代码
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AdminOperationLogCreate(BaseModel):
    """创建操作审计日志（内部使用）"""
    user_id: int = Field(..., description="操作人用户ID")
    username: str = Field(..., description="操作人用户名")
    action: str = Field(..., description="操作类型: CREATE/UPDATE/DELETE")
    resource_type: str = Field(..., description="操作对象类型，如: user/role/permission/menu")
    resource_id: Optional[int] = Field(None, description="操作对象ID")
    description: Optional[str] = Field(None, description="操作描述")
    before_data: Optional[str] = Field(None, description="变更前数据（JSON格式）")
    after_data: Optional[str] = Field(None, description="变更后数据（JSON格式）")
    request_method: Optional[str] = Field(None, description="请求方法")
    request_path: Optional[str] = Field(None, description="请求路径")
    ip_address: Optional[str] = Field(None, description="客户端IP地址")


class AdminOperationLogResponse(BaseModel):
    """操作审计日志响应，包含单条操作记录的完整信息"""
    id: int = Field(..., description="日志记录ID")
    user_id: int = Field(..., description="操作人用户ID")
    username: str = Field(..., description="操作人用户名")
    action: str = Field(..., description="操作类型: CREATE/UPDATE/DELETE")
    resource_type: str = Field(..., description="操作对象类型，如: user/role/permission/menu")
    resource_id: Optional[int] = Field(None, description="操作对象ID")
    description: Optional[str] = Field(None, description="操作描述，如: 删除用户张三")
    before_data: Optional[str] = Field(None, description="变更前数据（JSON格式），可用于数据回溯")
    after_data: Optional[str] = Field(None, description="变更后数据（JSON格式），可用于数据回溯")
    request_method: Optional[str] = Field(None, description="触发操作的请求方法")
    request_path: Optional[str] = Field(None, description="触发操作的请求路径")
    ip_address: Optional[str] = Field(None, description="客户端IP地址")
    created_at: datetime = Field(..., description="操作时间")

    class Config:
        from_attributes = True


class AdminOperationLogQuery(BaseModel):
    """操作审计日志查询参数，支持多条件筛选和分页"""
    user_id: Optional[int] = Field(None, description="按操作人用户ID精确筛选")
    username: Optional[str] = Field(None, description="按操作人用户名模糊搜索")
    action: Optional[str] = Field(None, description="按操作类型筛选，可选值: CREATE/UPDATE/DELETE")
    resource_type: Optional[str] = Field(None, description="按操作对象类型筛选，如: user/role/permission/menu")
    start_time: Optional[datetime] = Field(None, description="起始时间，ISO 8601 格式")
    end_time: Optional[datetime] = Field(None, description="结束时间，ISO 8601 格式")
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(20, ge=1, le=100, description="每页数量，最大100")
