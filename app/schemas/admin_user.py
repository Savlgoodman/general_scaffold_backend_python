"""
管理员用户相关的Pydantic Schema
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# 管理员用户基础Schema
class AdminUserBase(BaseModel):
    """管理员用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar: Optional[str] = Field(None, description="头像URL")
    is_active: bool = Field(True, description="是否激活")
    remark: Optional[str] = Field(None, description="备注")


# 管理员用户创建Schema
class AdminUserCreate(AdminUserBase):
    """创建管理员用户"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    is_superuser: bool = Field(False, description="是否超级管理员")


# 管理员用户更新Schema
class AdminUserUpdate(BaseModel):
    """更新管理员用户"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar: Optional[str] = Field(None, description="头像URL")
    is_active: Optional[bool] = Field(None, description="是否激活")
    remark: Optional[str] = Field(None, description="备注")


# 管理员用户密码修改Schema
class AdminUserPasswordChange(BaseModel):
    """修改密码"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


# 管理员用户响应Schema
class AdminUserResponse(AdminUserBase):
    """管理员用户响应"""
    id: int
    is_superuser: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 管理员用户列表响应Schema
class AdminUserListResponse(BaseModel):
    """管理员用户列表响应"""
    total: int
    items: list[AdminUserResponse]


# 管理员登录Schema
class AdminUserLogin(BaseModel):
    """管理员用户登录"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


# Token响应Schema
class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# 当前管理员用户信息Schema
class CurrentAdminUser(AdminUserResponse):
    """当前登录管理员用户信息"""
    pass


