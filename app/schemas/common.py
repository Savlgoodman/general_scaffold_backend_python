"""
通用响应Schema
"""
from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")


class PageResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")
    items: list[T] = Field(..., description="数据列表")


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    detail: Optional[Any] = Field(None, description="错误详情")


