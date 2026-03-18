"""
登录日志数据库模型
记录管理员用户每次登录行为，包括成功和失败的登录尝试
"""
from sqlalchemy import Column, Integer, String, Text, Boolean
from app.core.database import Base


class AdminLoginLog(Base):
    """管理员登录日志表"""
    __tablename__ = "admin_login_logs"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")

    # 用户信息
    user_id = Column(Integer, index=True, comment="用户ID，登录失败时可能为空")
    username = Column(String(50), nullable=False, index=True, comment="登录用户名")

    # 登录结果
    success = Column(Boolean, nullable=False, index=True, comment="登录是否成功")
    failure_reason = Column(String(200), comment="登录失败原因，如：密码错误、验证码错误、账户被禁用")

    # 客户端信息
    ip_address = Column(String(50), comment="客户端IP地址")
    user_agent = Column(String(500), comment="浏览器User-Agent")

    # created_at, updated_at, is_deleted 由 Base 自动提供

    def __repr__(self):
        return f"<AdminLoginLog(id={self.id}, username={self.username}, success={self.success})>"
