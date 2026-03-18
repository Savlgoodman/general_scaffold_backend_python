"""
系统异常日志相关的 Pydantic Schema
用于请求参数校验和响应数据序列化，前端通过 OpenAPI 自动生成对接代码
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AdminErrorLogBase(BaseModel):
    """系统异常日志基础信息"""
    level: str = Field(..., description="日志级别，可选值：WARNING / ERROR / CRITICAL")
    message: str = Field(..., description="日志消息内容，描述异常概况")
    traceback: Optional[str] = Field(None, description="完整的异常堆栈信息，用于定位问题")
    request_method: Optional[str] = Field(None, description="触发异常的请求方法，如 GET / POST / PUT / DELETE")
    request_path: Optional[str] = Field(None, description="触发异常的请求路径，如 /api/admin/users/list")
    user_id: Optional[int] = Field(None, description="触发异常的用户ID，未登录时为空")
    username: Optional[str] = Field(None, description="触发异常的用户名，未登录时为空")
    ip_address: Optional[str] = Field(None, description="客户端IP地址")


class AdminErrorLogCreate(AdminErrorLogBase):
    """创建系统异常日志（内部使用，由 loguru sink 自动调用）"""
    pass


class AdminErrorLogResponse(AdminErrorLogBase):
    """系统异常日志响应，包含完整日志信息"""
    id: int = Field(..., description="日志记录ID")
    created_at: datetime = Field(..., description="日志记录时间")

    class Config:
        from_attributes = True


class AdminErrorLogQuery(BaseModel):
    """系统异常日志查询参数，支持多条件筛选和分页"""
    level: Optional[str] = Field(None, description="按日志级别筛选，可选值：WARNING / ERROR / CRITICAL")
    keyword: Optional[str] = Field(None, description="按日志消息内容模糊搜索")
    request_path: Optional[str] = Field(None, description="按请求路径模糊搜索")
    user_id: Optional[int] = Field(None, description="按用户ID精确筛选")
    start_time: Optional[datetime] = Field(None, description="起始时间，ISO 8601 格式，如 2026-01-01T00:00:00")
    end_time: Optional[datetime] = Field(None, description="结束时间，ISO 8601 格式，如 2026-12-31T23:59:59")
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(20, ge=1, le=100, description="每页数量，最大100")


class AdminErrorLogStatistics(BaseModel):
    """系统异常日志统计信息，用于仪表盘展示"""
    total: int = Field(..., description="日志总数")
    warning_count: int = Field(..., description="WARNING 级别日志数量")
    error_count: int = Field(..., description="ERROR 级别日志数量")
    critical_count: int = Field(..., description="CRITICAL 级别日志数量")
