"""
登录日志服务层
处理登录日志的记录、查询和统计
"""
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.admin_login_log import AdminLoginLog
from app.schemas.admin_login_log import AdminLoginLogQuery, AdminLoginLogCreate


class AdminLoginLogService:
    """登录日志服务"""

    @staticmethod
    def create(db: Session, log_data: AdminLoginLogCreate) -> AdminLoginLog:
        """记录一条登录日志"""
        log = AdminLoginLog(**log_data.model_dump())
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_by_id(db: Session, log_id: int) -> Optional[AdminLoginLog]:
        """根据ID获取登录日志"""
        return db.query(AdminLoginLog).filter(
            AdminLoginLog.id == log_id,
            AdminLoginLog.is_deleted == False
        ).first()

    @staticmethod
    def get_list(
        db: Session,
        query_params: AdminLoginLogQuery
    ) -> tuple[List[AdminLoginLog], int]:
        """
        获取登录日志列表（分页 + 多条件筛选）

        Returns:
            (日志列表, 总数)
        """
        query = db.query(AdminLoginLog).filter(AdminLoginLog.is_deleted == False)

        conditions = []

        if query_params.username:
            conditions.append(AdminLoginLog.username.like(f"%{query_params.username}%"))

        if query_params.success is not None:
            conditions.append(AdminLoginLog.success == query_params.success)

        if query_params.ip_address:
            conditions.append(AdminLoginLog.ip_address.like(f"%{query_params.ip_address}%"))

        if query_params.start_time:
            conditions.append(AdminLoginLog.created_at >= query_params.start_time)

        if query_params.end_time:
            conditions.append(AdminLoginLog.created_at <= query_params.end_time)

        if conditions:
            query = query.filter(and_(*conditions))

        total = query.count()

        skip = (query_params.page - 1) * query_params.page_size
        logs = query.order_by(AdminLoginLog.created_at.desc()).offset(skip).limit(query_params.page_size).all()

        return logs, total

    @staticmethod
    def get_statistics(
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> dict:
        """获取登录日志统计信息"""
        query = db.query(AdminLoginLog).filter(AdminLoginLog.is_deleted == False)

        if start_time:
            query = query.filter(AdminLoginLog.created_at >= start_time)
        if end_time:
            query = query.filter(AdminLoginLog.created_at <= end_time)

        total = query.count()
        success_count = query.filter(AdminLoginLog.success == True).count()
        failure_count = query.filter(AdminLoginLog.success == False).count()

        return {
            "total": total,
            "success_count": success_count,
            "failure_count": failure_count,
        }

    @staticmethod
    def delete_old_logs(db: Session, days: int = 90) -> int:
        """逻辑删除旧登录日志"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        count = db.query(AdminLoginLog).filter(
            AdminLoginLog.created_at < cutoff_date,
            AdminLoginLog.is_deleted == False
        ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)})
        db.commit()
        return count
