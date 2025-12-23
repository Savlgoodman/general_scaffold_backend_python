"""
API日志相关的Pydantic Schema
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# API日志基础Schema
class APILogBase(BaseModel):
    """API日志基础信息"""
    method: str = Field(..., description="请求方法")
    path: str = Field(..., description="请求路径")
    query_params: Optional[str] = Field(None, description="查询参数")
    request_body: Optional[str] = Field(None, description="请求体")
    status_code: Optional[int] = Field(None, description="响应状态码")
    response_body: Optional[str] = Field(None, description="响应体")
    duration: Optional[float] = Field(None, description="响应时长(秒)")
    user_id: Optional[int] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="User Agent")


# API日志创建Schema
class APILogCreate(APILogBase):
    """创建API日志"""
    pass


# API日志响应Schema
class APILogResponse(APILogBase):
    """API日志响应"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# API日志列表响应Schema
class APILogListResponse(BaseModel):
    """API日志列表响应"""
    total: int
    items: list[APILogResponse]


# API日志查询参数Schema
class APILogQuery(BaseModel):
    """API日志查询参数"""
    method: Optional[str] = Field(None, description="请求方法")
    path: Optional[str] = Field(None, description="请求路径(模糊查询)")
    user_id: Optional[int] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名(模糊查询)")
    status_code: Optional[int] = Field(None, description="响应状态码")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


