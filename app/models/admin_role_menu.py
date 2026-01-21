"""
管理员角色菜单关联表
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class AdminRoleMenu(Base):
    """管理员角色菜单关联表"""
    __tablename__ = "admin_role_menus"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    role_id = Column(Integer, nullable=False, index=True, comment="角色ID")
    menu_id = Column(Integer, nullable=False, index=True, comment="菜单ID")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<AdminRoleMenu(id={self.id}, role_id={self.role_id}, menu_id={self.menu_id})>"







