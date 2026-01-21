"""
管理员菜单数据库模型
"""
from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class AdminMenu(Base):
    """管理员菜单表"""
    __tablename__ = "admin_menus"
    
    id = Column(Integer, primary_key=True, index=True, comment="菜单ID")
    name = Column(String(100), nullable=False, comment="菜单名称")
    path = Column(String(255), nullable=False, comment="菜单路径")
    parent_id = Column(Integer, default=0, index=True, comment="父菜单ID，0表示顶级菜单")
    sort = Column(Integer, default=0, comment="排序号，数字越小越靠前")
    remark = Column(Text, comment="备注")
    status = Column(Integer, default=1, comment="状态：1=启用，0=禁用")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<AdminMenu(id={self.id}, name={self.name}, path={self.path})>"







