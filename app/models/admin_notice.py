"""
通知公告数据库模型
支持系统公告和通知的发布、管理，含状态流转（草稿→已发布→已撤回）
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from app.core.database import Base


class AdminNotice(Base):
    """系统通知公告表"""
    __tablename__ = "admin_notices"

    id = Column(Integer, primary_key=True, index=True, comment="公告ID")

    # 公告内容
    title = Column(String(200), nullable=False, comment="公告标题")
    content = Column(Text, nullable=False, comment="公告内容（支持富文本HTML）")
    notice_type = Column(String(20), nullable=False, index=True, comment="公告类型: notice=通知, announcement=公告")

    # 状态管理
    status = Column(String(20), nullable=False, default="draft", index=True, comment="状态: draft=草稿, published=已发布, revoked=已撤回")
    publish_time = Column(DateTime, comment="发布时间")

    # 发布者信息
    publisher_id = Column(Integer, nullable=False, index=True, comment="发布者用户ID")
    publisher_name = Column(String(50), nullable=False, comment="发布者用户名")

    # 显示控制
    is_top = Column(Boolean, default=False, comment="是否置顶")
    sort_order = Column(Integer, default=0, comment="排序序号，数��越大越靠前")

    # created_at, updated_at, is_deleted 由 Base 自动提供

    def __repr__(self):
        return f"<AdminNotice(id={self.id}, title={self.title}, status={self.status})>"
