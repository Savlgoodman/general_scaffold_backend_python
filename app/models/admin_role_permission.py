"""
管理员角色权限关联表
"""
from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.core.database import Base


class AdminRolePermission(Base):
    """管理员角色权限关联表 - 支持allow/deny和优先级"""
    __tablename__ = "admin_role_permissions"
    
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    role_id = Column(Integer, nullable=False, index=True, comment="角色ID")
    permission_id = Column(Integer, nullable=False, index=True, comment="权限ID")
    effect = Column(String(10), nullable=False, default="allow", comment="效果：allow=允许，deny=拒绝")
    priority = Column(Integer, nullable=False, default=0, comment="优先级，数值越大优先级越高")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<AdminRolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id}, effect={self.effect})>"







