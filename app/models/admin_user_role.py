"""
管理员用户角色关联表
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class AdminUserRole(Base):
    """管理员用户角色关联表"""
    __tablename__ = "admin_user_roles"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    admin_user_id = Column(Integer, nullable=False, index=True, comment="管理员用户ID")
    role_id = Column(Integer, nullable=False, index=True, comment="角色ID")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<AdminUserRole(id={self.id}, admin_user_id={self.admin_user_id}, role_id={self.role_id})>"







