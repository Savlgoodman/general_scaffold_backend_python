"""
管理员角色相关的Pydantic模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AdminRoleBase(BaseModel):
    """角色基础模型"""
    name: str = Field(..., description="角色名称")
    remark: Optional[str] = Field(None, description="备注")
    status: int = Field(1, description="状态：1=启用，0=禁用")


class AdminRoleCreate(AdminRoleBase):
    """创建角色"""
    pass


class AdminRoleUpdate(BaseModel):
    """更新角色"""
    name: Optional[str] = Field(None, description="角色名称")
    remark: Optional[str] = Field(None, description="备注")
    status: Optional[int] = Field(None, description="状态：1=启用，0=禁用")


class AdminRoleResponse(AdminRoleBase):
    """角色响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AdminRoleAssignPermissions(BaseModel):
    """角色分配权限"""
    permission_ids: List[int] = Field(..., description="权限ID列表")


class AdminRoleAssignMenus(BaseModel):
    """角色分配菜单"""
    menu_ids: List[int] = Field(..., description="菜单ID列表")







