"""
管理员角色数据库模型
"""
from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class AdminRole(Base):
    """管理员角色表"""
    __tablename__ = "admin_roles"
    
    id = Column(Integer, primary_key=True, index=True, comment="角色ID")
    name = Column(String(50), unique=True, nullable=False, comment="角色名称")
    remark = Column(Text, comment="备注")
    status = Column(Integer, default=1, comment="状态：1=启用，0=禁用")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<AdminRole(id={self.id}, name={self.name})>"

