"""
管理员角色权限关联表
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class AdminRolePermission(Base):
    """管理员角色权限关联表"""
    __tablename__ = "admin_role_permissions"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    role_id = Column(Integer, nullable=False, index=True, comment="角色ID")
    permission_id = Column(Integer, nullable=False, index=True, comment="权限ID")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<AdminRolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id})>"







