"""
管理员用户权限覆盖相关的Pydantic模型
"""
from typing import List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.admin_user_permission_override import EffectType


class AdminUserPermissionOverrideBase(BaseModel):
    """用户权限覆盖基础模型"""
    admin_user_id: int = Field(..., description="管理员用户ID")
    permission_id: int = Field(..., description="权限ID")
    effect: EffectType = Field(..., description="效果：ALLOW=允许，DENY=拒绝")


class AdminUserPermissionOverrideCreate(AdminUserPermissionOverrideBase):
    """创建用户权限覆盖"""
    pass


class AdminUserPermissionOverrideResponse(AdminUserPermissionOverrideBase):
    """用户权限覆盖响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AdminUserPermissionOverrideBatch(BaseModel):
    """批量设置用户权限覆盖"""
    permission_id: int = Field(..., description="权限ID")
    effect: EffectType = Field(..., description="效果：ALLOW=允许，DENY=拒绝")


class AdminUserPermissionOverrideBatchCreate(BaseModel):
    """批量创建用户权限覆盖"""
    overrides: List[AdminUserPermissionOverrideBatch] = Field(..., description="权限覆盖列表")







