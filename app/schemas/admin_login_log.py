"""
登录日志相关的 Pydantic Schema
用于请求参数校验和响应数据序列化，前端通过 OpenAPI 自动生成对接代码
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AdminLoginLogCreate(BaseModel):
    """创建登录日志（内部使用）"""
    user_id: Optional[int] = Field(None, description="用户ID，登录失败时可能为空")
    username: str = Field(..., description="登录用户名")
    success: bool = Field(..., description="登录是否成功")
    failure_reason: Optional[str] = Field(None, description="登录失败原因")
    ip_address: Optional[str] = Field(None, description="客户端IP地址")
    user_agent: Optional[str] = Field(None, description="浏览器User-Agent")


class AdminLoginLogResponse(BaseModel):
    """登录日志响应，包含单条登录记录的完整信息"""
    id: int = Field(..., description="日志记录ID")
    user_id: Optional[int] = Field(None, description="用户ID，登录失败时可能为空")
    username: str = Field(..., description="登录用户名")
    success: bool = Field(..., description="登录是否成功：true=成功，false=失败")
    failure_reason: Optional[str] = Field(None, description="登录失败原因，成功时为空")
    ip_address: Optional[str] = Field(None, description="客户端IP地址")
    user_agent: Optional[str] = Field(None, description="浏览器User-Agent")
    created_at: datetime = Field(..., description="登录时间")

    class Config:
        from_attributes = True


class AdminLoginLogQuery(BaseModel):
    """登录日志查询参数，支持多条件筛选和分页"""
    username: Optional[str] = Field(None, description="按用户名模糊搜索")
    success: Optional[bool] = Field(None, description="按登录结果筛选：true=仅成功，false=仅失败")
    ip_address: Optional[str] = Field(None, description="按IP地址模糊搜索")
    start_time: Optional[datetime] = Field(None, description="起始时间，ISO 8601 格式")
    end_time: Optional[datetime] = Field(None, description="结束时间，ISO 8601 格式")
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(20, ge=1, le=100, description="每页数量，最大100")


class AdminLoginLogStatistics(BaseModel):
    """登录日志统计信息，用于仪表盘展示登录趋势"""
    total: int = Field(..., description="登录总次数")
    success_count: int = Field(..., description="登录成功次数")
    failure_count: int = Field(..., description="登录失败次数")
