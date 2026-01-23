"""
系统配置数据库模型
"""
from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class AdminSystemConfig(Base):
    """系统配置表"""
    __tablename__ = "admin_system_config"
    
    id = Column(Integer, primary_key=True, index=True, comment="配置ID")
    config_key = Column(String(100), unique=True, index=True, nullable=False, comment="配置键")
    config_value = Column(Text, comment="配置值")
    description = Column(String(255), comment="配置描述")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<AdminSystemConfig(id={self.id}, config_key={self.config_key})>"
