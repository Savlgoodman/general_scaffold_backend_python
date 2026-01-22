"""
系统信息相关的Pydantic模型
"""
from typing import Optional
from pydantic import BaseModel, Field


class SystemResourcesResponse(BaseModel):
    """系统资源响应"""
    cpu_percent: float = Field(..., description="CPU使用率(%)")
    memory_total: int = Field(..., description="总内存(bytes)")
    memory_used: int = Field(..., description="已用内存(bytes)")
    memory_available: int = Field(..., description="可用内存(bytes)")
    memory_percent: float = Field(..., description="内存使用率(%)")


class NetworkStatsResponse(BaseModel):
    """网络统计响应"""
    bytes_sent: int = Field(..., description="发送字节数")
    bytes_recv: int = Field(..., description="接收字节数")
    packets_sent: int = Field(..., description="发送数据包数")
    packets_recv: int = Field(..., description="接收数据包数")


class RedisStatusResponse(BaseModel):
    """Redis状态响应"""
    connected: bool = Field(..., description="是否连接")
    db_size: Optional[int] = Field(None, description="数据库大小(键数量)")
    used_memory: Optional[int] = Field(None, description="已用内存(bytes)")
    used_memory_human: Optional[str] = Field(None, description="已用内存(人类可读)")
    error_message: Optional[str] = Field(None, description="错误信息")


class RedisKeyValueResponse(BaseModel):
    """Redis键值对响应"""
    key: str = Field(..., description="键名")
    type: str = Field(..., description="值类型")
    value: str = Field(..., description="值内容")
    ttl: Optional[int] = Field(None, description="过期时间(秒)，-1表示永不过期")


class FailedLoginStatsResponse(BaseModel):
    """失败登录统计响应"""
    total_count: int = Field(..., description="今日失败登录总数")
