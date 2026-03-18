"""
系统异常日志服务层
处理异常日志的查询、统计和清理等业务逻辑
"""
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.app_error_log import AdminErrorLog
from app.schemas.app_error_log import AdminErrorLogQuery, AdminErrorLogCreate


class AdminErrorLogService:
    """系统异常日志服务"""

    @staticmethod
    def get_by_id(db: Session, log_id: int) -> Optional[AdminErrorLog]:
        """根据ID获取异常日志"""
        return db.query(AdminErrorLog).filter(
            AdminErrorLog.id == log_id,
            AdminErrorLog.is_deleted == False
        ).first()

    @staticmethod
    def get_list(
        db: Session,
        query_params: AdminErrorLogQuery
    ) -> tuple[List[AdminErrorLog], int]:
        """
        获取异常日志列表（分页 + 多条件筛选）

        Returns:
            (日志列表, 总数)
        """
        query = db.query(AdminErrorLog).filter(AdminErrorLog.is_deleted == False)

        conditions = []

        if query_params.level:
            conditions.append(AdminErrorLog.level == query_params.level)

        if query_params.keyword:
            conditions.append(AdminErrorLog.message.like(f"%{query_params.keyword}%"))

        if query_params.request_path:
            conditions.append(AdminErrorLog.request_path.like(f"%{query_params.request_path}%"))

        if query_params.user_id:
            conditions.append(AdminErrorLog.user_id == query_params.user_id)

        if query_params.start_time:
            conditions.append(AdminErrorLog.created_at >= query_params.start_time)

        if query_params.end_time:
            conditions.append(AdminErrorLog.created_at <= query_params.end_time)

        if conditions:
            query = query.filter(and_(*conditions))

        total = query.count()

        skip = (query_params.page - 1) * query_params.page_size
        logs = query.order_by(AdminErrorLog.created_at.desc()).offset(skip).limit(query_params.page_size).all()

        return logs, total

    @staticmethod
    def create(db: Session, log_data: AdminErrorLogCreate) -> AdminErrorLog:
        """创建异常日志记录"""
        log = AdminErrorLog(**log_data.model_dump())
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def delete_old_logs(db: Session, days: int = 30) -> int:
        """
        逻辑删除旧异常日志

        Args:
            days: 保留最近多少天的日志

        Returns:
            删除的日志数量
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        count = db.query(AdminErrorLog).filter(
            AdminErrorLog.created_at < cutoff_date,
            AdminErrorLog.is_deleted == False
        ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)})
        db.commit()

        return count

    @staticmethod
    def get_statistics(
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> dict:
        """获取异常日志统计信息"""
        query = db.query(AdminErrorLog).filter(AdminErrorLog.is_deleted == False)

        if start_time:
            query = query.filter(AdminErrorLog.created_at >= start_time)

        if end_time:
            query = query.filter(AdminErrorLog.created_at <= end_time)

        total = query.count()
        warning_count = query.filter(AdminErrorLog.level == "WARNING").count()
        error_count = query.filter(AdminErrorLog.level == "ERROR").count()
        critical_count = query.filter(AdminErrorLog.level == "CRITICAL").count()

        return {
            "total": total,
            "warning_count": warning_count,
            "error_count": error_count,
            "critical_count": critical_count,
        }
