"""
系统异常日志服务层
处理异常日志的查询、统计和清理等业务逻辑
"""
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.app_error_log import AppErrorLog
from app.schemas.app_error_log import AppErrorLogQuery, AppErrorLogCreate


class AppErrorLogService:
    """系统异常日志服务"""

    @staticmethod
    def get_by_id(db: Session, log_id: int) -> Optional[AppErrorLog]:
        """根据ID获取异常日志"""
        return db.query(AppErrorLog).filter(
            AppErrorLog.id == log_id,
            AppErrorLog.is_deleted == False
        ).first()

    @staticmethod
    def get_list(
        db: Session,
        query_params: AppErrorLogQuery
    ) -> tuple[List[AppErrorLog], int]:
        """
        获取异常日志列表（分页 + 多条件筛选）

        Returns:
            (日志列表, 总数)
        """
        query = db.query(AppErrorLog).filter(AppErrorLog.is_deleted == False)

        conditions = []

        if query_params.level:
            conditions.append(AppErrorLog.level == query_params.level)

        if query_params.keyword:
            conditions.append(AppErrorLog.message.like(f"%{query_params.keyword}%"))

        if query_params.request_path:
            conditions.append(AppErrorLog.request_path.like(f"%{query_params.request_path}%"))

        if query_params.user_id:
            conditions.append(AppErrorLog.user_id == query_params.user_id)

        if query_params.start_time:
            conditions.append(AppErrorLog.created_at >= query_params.start_time)

        if query_params.end_time:
            conditions.append(AppErrorLog.created_at <= query_params.end_time)

        if conditions:
            query = query.filter(and_(*conditions))

        total = query.count()

        skip = (query_params.page - 1) * query_params.page_size
        logs = query.order_by(AppErrorLog.created_at.desc()).offset(skip).limit(query_params.page_size).all()

        return logs, total

    @staticmethod
    def create(db: Session, log_data: AppErrorLogCreate) -> AppErrorLog:
        """创建异常日志记录"""
        log = AppErrorLog(**log_data.model_dump())
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

        count = db.query(AppErrorLog).filter(
            AppErrorLog.created_at < cutoff_date,
            AppErrorLog.is_deleted == False
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
        query = db.query(AppErrorLog).filter(AppErrorLog.is_deleted == False)

        if start_time:
            query = query.filter(AppErrorLog.created_at >= start_time)

        if end_time:
            query = query.filter(AppErrorLog.created_at <= end_time)

        total = query.count()
        warning_count = query.filter(AppErrorLog.level == "WARNING").count()
        error_count = query.filter(AppErrorLog.level == "ERROR").count()
        critical_count = query.filter(AppErrorLog.level == "CRITICAL").count()

        return {
            "total": total,
            "warning_count": warning_count,
            "error_count": error_count,
            "critical_count": critical_count,
        }
