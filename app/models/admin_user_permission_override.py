"""
管理员用户权限覆盖表
"""
from sqlalchemy import Column, Integer, String, Enum as SQLEnum
import enum
from app.core.database import Base


class EffectType(str, enum.Enum):
    """权限效果类型"""
    ALLOW = "ALLOW"  # 允许
    DENY = "DENY"    # 拒绝


class AdminUserPermissionOverride(Base):
    """管理员用户权限覆盖表"""
    __tablename__ = "admin_user_permission_overrides"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    admin_user_id = Column(Integer, nullable=False, index=True, comment="管理员用户ID")
    permission_id = Column(Integer, nullable=False, index=True, comment="权限ID")
    effect = Column(SQLEnum(EffectType), nullable=False, comment="效果：ALLOW=允许，DENY=拒绝")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<AdminUserPermissionOverride(id={self.id}, admin_user_id={self.admin_user_id}, permission_id={self.permission_id}, effect={self.effect})>"







