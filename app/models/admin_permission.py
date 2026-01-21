"""
管理员权限数据库模型
"""
from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class AdminPermission(Base):
    """管理员权限表（API权限）"""
    __tablename__ = "admin_permissions"
    
    id = Column(Integer, primary_key=True, index=True, comment="权限ID")
    name = Column(String(100), nullable=False, comment="权限名称")
    api_path = Column(String(255), nullable=False, comment="API路径")
    remark = Column(Text, comment="备注")
    status = Column(Integer, default=1, comment="状态：1=启用，0=禁用")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<AdminPermission(id={self.id}, name={self.name}, api_path={self.api_path})>"

