"""
管理员用户菜单覆盖相关的Pydantic模型
"""
from typing import List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.admin_user_menu_override import MenuEffectType


class AdminUserMenuOverrideBase(BaseModel):
    """用户菜单覆盖基础模型"""
    admin_user_id: int = Field(..., description="管理员用户ID")
    menu_id: int = Field(..., description="菜单ID")
    effect: MenuEffectType = Field(..., description="效果：ALLOW=允许，DENY=拒绝")


class AdminUserMenuOverrideCreate(AdminUserMenuOverrideBase):
    """创建用户菜单覆盖"""
    pass


class AdminUserMenuOverrideResponse(AdminUserMenuOverrideBase):
    """用户菜单覆盖响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AdminUserMenuOverrideBatch(BaseModel):
    """批量设置用户菜单覆盖"""
    menu_id: int = Field(..., description="菜单ID")
    effect: MenuEffectType = Field(..., description="效果：ALLOW=允许，DENY=拒绝")


class AdminUserMenuOverrideBatchCreate(BaseModel):
    """批量创建用户菜单覆盖"""
    overrides: List[AdminUserMenuOverrideBatch] = Field(..., description="菜单覆盖列表")







