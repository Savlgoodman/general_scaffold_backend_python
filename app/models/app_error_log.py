"""
系统异常日志数据库模型
存储 WARNING/ERROR/CRITICAL 级别的应用日志，供管理后台查询和监控
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.database import Base


class AppErrorLog(Base):
    """系统异常日志表"""
    __tablename__ = "app_error_logs"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")

    # 日志信息
    level = Column(String(20), nullable=False, index=True, comment="日志级别: WARNING/ERROR/CRITICAL")
    message = Column(Text, nullable=False, comment="日志消息")
    traceback = Column(Text, comment="异常堆栈信息")

    # 请求上下文
    request_method = Column(String(10), comment="请求方法")
    request_path = Column(String(500), index=True, comment="请求路径")

    # 用户信息
    user_id = Column(Integer, index=True, comment="触发异常的用户ID")
    username = Column(String(50), comment="触发异常的用户名")

    # 客户端信息
    ip_address = Column(String(50), comment="客户端IP地址")

    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供

    def __repr__(self):
        return f"<AppErrorLog(id={self.id}, level={self.level}, message={self.message[:50] if self.message else ''})>"
