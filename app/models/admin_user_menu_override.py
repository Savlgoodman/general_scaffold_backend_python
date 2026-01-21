"""
管理员用户菜单覆盖表
"""
from sqlalchemy import Column, Integer, String, Enum as SQLEnum
import enum
from app.core.database import Base


class MenuEffectType(str, enum.Enum):
    """菜单权限效果类型"""
    ALLOW = "ALLOW"  # 允许
    DENY = "DENY"    # 拒绝


class AdminUserMenuOverride(Base):
    """管理员用户菜单覆盖表"""
    __tablename__ = "admin_user_menu_overrides"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    admin_user_id = Column(Integer, nullable=False, index=True, comment="管理员用户ID")
    menu_id = Column(Integer, nullable=False, index=True, comment="菜单ID")
    effect = Column(SQLEnum(MenuEffectType), nullable=False, comment="效果：ALLOW=允许，DENY=拒绝")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<AdminUserMenuOverride(id={self.id}, admin_user_id={self.admin_user_id}, menu_id={self.menu_id}, effect={self.effect})>"







