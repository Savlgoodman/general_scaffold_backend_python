"""
管理员菜单相关的Pydantic模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AdminMenuBase(BaseModel):
    """菜单基础模型"""
    name: str = Field(..., description="菜单名称")
    path: str = Field(..., description="菜单路径")
    parent_id: int = Field(0, description="父菜单ID，0表示顶级菜单")
    sort: int = Field(0, description="排序号，数字越小越靠前")
    remark: Optional[str] = Field(None, description="备注")
    status: int = Field(1, description="状态：1=启用，0=禁用")


class AdminMenuCreate(AdminMenuBase):
    """创建菜单"""
    pass


class AdminMenuUpdate(BaseModel):
    """更新菜单"""
    name: Optional[str] = Field(None, description="菜单名称")
    path: Optional[str] = Field(None, description="菜单路径")
    parent_id: Optional[int] = Field(None, description="父菜单ID，0表示顶级菜单")
    sort: Optional[int] = Field(None, description="排序号，数字越小越靠前")
    remark: Optional[str] = Field(None, description="备注")
    status: Optional[int] = Field(None, description="状态：1=启用，0=禁用")


class AdminMenuResponse(AdminMenuBase):
    """菜单响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AdminMenuTreeNode(BaseModel):
    """菜单树节点"""
    id: int
    name: str
    path: str
    parent_id: int
    sort: int
    remark: Optional[str] = None
    status: int
    children: List['AdminMenuTreeNode'] = Field(default_factory=list, description="子菜单列表")
    
    model_config = ConfigDict(from_attributes=True)







