"""
用户相关的Pydantic Schema
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# 用户基础Schema
class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar: Optional[str] = Field(None, description="头像URL")
    is_active: bool = Field(True, description="是否激活")
    remark: Optional[str] = Field(None, description="备注")


# 用户创建Schema
class UserCreate(UserBase):
    """创建用户"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    is_superuser: bool = Field(False, description="是否超级管理员")


# 用户更新Schema
class UserUpdate(BaseModel):
    """更新用户"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar: Optional[str] = Field(None, description="头像URL")
    is_active: Optional[bool] = Field(None, description="是否激活")
    remark: Optional[str] = Field(None, description="备注")


# 用户密码修改Schema
class UserPasswordChange(BaseModel):
    """修改密码"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


# 用户响应Schema
class UserResponse(UserBase):
    """用户响应"""
    id: int
    is_superuser: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 用户列表响应Schema
class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    items: list[UserResponse]


# 登录Schema
class UserLogin(BaseModel):
    """用户登录"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


# Token响应Schema
class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# 当前用户信息Schema
class CurrentUser(UserResponse):
    """当前登录用户信息"""
    pass


