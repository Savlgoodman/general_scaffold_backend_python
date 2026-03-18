"""
通知公告服务层
处理公告的 CRUD 和状态流转（草稿→已发布→已撤回）
"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, case

from app.models.admin_notice import AdminNotice
from app.schemas.admin_notice import AdminNoticeCreate, AdminNoticeUpdate, AdminNoticeQuery


class AdminNoticeService:
    """通知公告服务"""

    @staticmethod
    def create(
        db: Session,
        data: AdminNoticeCreate,
        publisher_id: int,
        publisher_name: str
    ) -> AdminNotice:
        """创建公告（默认草稿状态）"""
        notice = AdminNotice(
            **data.model_dump(),
            status="draft",
            publisher_id=publisher_id,
            publisher_name=publisher_name,
        )
        db.add(notice)
        db.commit()
        db.refresh(notice)
        return notice

    @staticmethod
    def get_by_id(db: Session, notice_id: int) -> Optional[AdminNotice]:
        """根据ID获取公告"""
        return db.query(AdminNotice).filter(
            AdminNotice.id == notice_id,
            AdminNotice.is_deleted == False
        ).first()

    @staticmethod
    def update(db: Session, notice_id: int, data: AdminNoticeUpdate) -> Optional[AdminNotice]:
        """
        更新公告信息。仅草稿状态可修改内容字段。
        已发布/已撤回的公告只能修改 is_top 和 sort_order。
        """
        notice = AdminNoticeService.get_by_id(db, notice_id)
        if not notice:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if notice.status != "draft":
            # 非草稿只允许改置顶和排序
            allowed = {"is_top", "sort_order"}
            update_data = {k: v for k, v in update_data.items() if k in allowed}

        for key, value in update_data.items():
            setattr(notice, key, value)

        notice.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notice)
        return notice

    @staticmethod
    def delete(db: Session, notice_id: int) -> bool:
        """软删除公告"""
        notice = AdminNoticeService.get_by_id(db, notice_id)
        if not notice:
            return False
        notice.is_deleted = True
        notice.updated_at = datetime.now(timezone.utc)
        db.commit()
        return True

    @staticmethod
    def publish(db: Session, notice_id: int) -> Optional[AdminNotice]:
        """
        发布公告：draft → published
        """
        notice = AdminNoticeService.get_by_id(db, notice_id)
        if not notice:
            return None
        if notice.status != "draft":
            raise ValueError(f"只有草稿状态的公告可以发布，当前状态: {notice.status}")

        notice.status = "published"
        notice.publish_time = datetime.now(timezone.utc)
        notice.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notice)
        return notice

    @staticmethod
    def revoke(db: Session, notice_id: int) -> Optional[AdminNotice]:
        """
        撤回公告：published → revoked
        """
        notice = AdminNoticeService.get_by_id(db, notice_id)
        if not notice:
            return None
        if notice.status != "published":
            raise ValueError(f"只有已发布的公告可以撤回，当前状态: {notice.status}")

        notice.status = "revoked"
        notice.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notice)
        return notice

    @staticmethod
    def get_list(
        db: Session,
        query_params: AdminNoticeQuery
    ) -> tuple[List[AdminNotice], int]:
        """
        获取公告列表（管理端，包含所有状态）
        排序：置顶优先 → sort_order 降序 → 创建时间降序
        """
        query = db.query(AdminNotice).filter(AdminNotice.is_deleted == False)

        conditions = []

        if query_params.title:
            conditions.append(AdminNotice.title.like(f"%{query_params.title}%"))

        if query_params.notice_type:
            conditions.append(AdminNotice.notice_type == query_params.notice_type)

        if query_params.status:
            conditions.append(AdminNotice.status == query_params.status)

        if query_params.publisher_name:
            conditions.append(AdminNotice.publisher_name.like(f"%{query_params.publisher_name}%"))

        if query_params.start_time:
            conditions.append(AdminNotice.created_at >= query_params.start_time)

        if query_params.end_time:
            conditions.append(AdminNotice.created_at <= query_params.end_time)

        if conditions:
            query = query.filter(and_(*conditions))

        total = query.count()

        skip = (query_params.page - 1) * query_params.page_size
        notices = query.order_by(
            AdminNotice.is_top.desc(),
            AdminNotice.sort_order.desc(),
            AdminNotice.created_at.desc()
        ).offset(skip).limit(query_params.page_size).all()

        return notices, total

    @staticmethod
    def get_published_list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        notice_type: Optional[str] = None,
    ) -> tuple[List[AdminNotice], int]:
        """
        获取已发布的公告列表（前端展示用，仅返回 published 状态）
        排序：置顶优先 → sort_order 降序 → 发布时间降序
        """
        query = db.query(AdminNotice).filter(
            AdminNotice.is_deleted == False,
            AdminNotice.status == "published"
        )

        if notice_type:
            query = query.filter(AdminNotice.notice_type == notice_type)

        total = query.count()

        skip = (page - 1) * page_size
        notices = query.order_by(
            AdminNotice.is_top.desc(),
            AdminNotice.sort_order.desc(),
            AdminNotice.publish_time.desc()
        ).offset(skip).limit(page_size).all()

        return notices, total
