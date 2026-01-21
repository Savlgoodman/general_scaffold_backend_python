"""
管理员登录响应相关的Pydantic模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.admin_menu import AdminMenuTreeNode


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    is_superuser: bool = Field(..., description="是否超级管理员")
    menus: List[AdminMenuTreeNode] = Field(default_factory=list, description="菜单权限树")

