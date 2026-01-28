"""
管理员权限数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Index, UniqueConstraint
from app.core.database import Base


class AdminPermission(Base):
    """管理员权限表（API权限）- 支持通配符和分组"""
    __tablename__ = "admin_permissions"
    
    # 复合唯一约束：同一资源模式+方法组合唯一
    __table_args__ = (
        UniqueConstraint('resource_pattern', 'method', name='uq_permission_resource_method'),
    )
    
    id = Column(Integer, primary_key=True, index=True, comment="权限ID")
    name = Column(String(100), nullable=False, comment="权限名称")
    resource_pattern = Column(String(255), nullable=False, index=True, comment="资源模式，支持通配符")
    method = Column(String(10), nullable=False, default="POST", comment="HTTP方法")
    group_key = Column(String(100), index=True, comment="分组标识")
    group_name = Column(String(100), comment="分组名称")
    is_group = Column(Boolean, default=False, comment="是否是组权限")
    description = Column(Text, comment="描述")
    status = Column(Integer, default=1, comment="状态：1=启用，0=禁用")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<AdminPermission(id={self.id}, name={self.name}, resource_pattern={self.resource_pattern}, method={self.method})>"

