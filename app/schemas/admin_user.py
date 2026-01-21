"""
管理员用户相关的Pydantic模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class AdminUserBase(BaseModel):
    """管理员用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    is_active: bool = Field(True, description="是否激活")
    is_superuser: bool = Field(False, description="是否超级管理员")
    remark: Optional[str] = Field(None, description="备注")


class AdminUserCreate(AdminUserBase):
    """创建管理员用户"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    role_ids: List[int] = Field(default_factory=list, description="角色ID列表")


class AdminUserUpdate(BaseModel):
    """更新管理员用户"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_superuser: Optional[bool] = Field(None, description="是否超级管理员")
    remark: Optional[str] = Field(None, description="备注")


class AdminUserResponse(BaseModel):
    """管理员用户响应模型"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CurrentAdminUser(BaseModel):
    """当前登录管理员用户信息"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class AdminUserPasswordChange(BaseModel):
    """修改密码"""
    old_password: str = Field(..., min_length=6, max_length=50, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class AdminUserAssignRoles(BaseModel):
    """用户分配角色"""
    role_ids: List[int] = Field(..., description="角色ID列表")


class AdminUserLogin(BaseModel):
    """管理员用户登录"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
