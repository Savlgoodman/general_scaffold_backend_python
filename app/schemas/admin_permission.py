"""
管理员权限相关的Pydantic模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AdminPermissionBase(BaseModel):
    """权限基础模型"""
    name: str = Field(..., description="权限名称")
    api_path: str = Field(..., description="API路径")
    remark: Optional[str] = Field(None, description="备注")
    status: int = Field(1, description="状态：1=启用，0=禁用")


class AdminPermissionCreate(AdminPermissionBase):
    """创建权限"""
    pass


class AdminPermissionUpdate(BaseModel):
    """更新权限"""
    name: Optional[str] = Field(None, description="权限名称")
    api_path: Optional[str] = Field(None, description="API路径")
    remark: Optional[str] = Field(None, description="备注")
    status: Optional[int] = Field(None, description="状态：1=启用，0=禁用")


class AdminPermissionResponse(AdminPermissionBase):
    """权限响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)







