"""
数据库连接管理
"""
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.database.url,
    echo=settings.database.echo,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_recycle=settings.database.pool_recycle,
    pool_pre_ping=True,  # 连接池预检查
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
BaseModel = declarative_base()


class Base(BaseModel):
    """
    所有模型的基类
    自动添加通用字段：
    - created_at: 创建时间
    - updated_at: 更新时间
    - is_deleted: 逻辑删除标记
    """
    __abstract__ = True
    
    @declared_attr
    def created_at(cls):
        """创建时间"""
        return Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    
    @declared_attr
    def updated_at(cls):
        """更新时间"""
        return Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
    
    @declared_attr
    def is_deleted(cls):
        """逻辑删除标记"""
        return Column(Boolean, default=False, index=True, comment="是否删除")


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于FastAPI的依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库
    创建所有表
    """
    # 导入所有模型，确保它们被注册到Base.metadata
    from app.models import (  # noqa
        admin_user, 
        api_log,
        admin_role,
        admin_permission,
        admin_menu,
        admin_user_role,
        admin_role_permission,
        admin_role_menu,
        admin_user_permission_override,
        admin_user_menu_override,
        admin_system_config,
        app_error_log,
        admin_login_log,
        admin_operation_log,
    )
    
    Base.metadata.create_all(bind=engine)


