"""
操作审计日志服务层
处理操作日志的记录、查询
"""
import json
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.admin_operation_log import AdminOperationLog
from app.schemas.admin_operation_log import AdminOperationLogQuery, AdminOperationLogCreate


class AdminOperationLogService:
    """操作审计日志服务"""

    @staticmethod
    def create(db: Session, log_data: AdminOperationLogCreate) -> AdminOperationLog:
        """记录一条操作日志"""
        log = AdminOperationLog(**log_data.model_dump())
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def record(
        db: Session,
        *,
        user_id: int,
        username: str,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        description: Optional[str] = None,
        before_data: Optional[dict] = None,
        after_data: Optional[dict] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AdminOperationLog:
        """
        便捷方法：直接传参记录操作日志，自动将 dict 序列化为 JSON 字符串。
        供业务代码直接调用。
        """
        log = AdminOperationLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            before_data=json.dumps(before_data, ensure_ascii=False, default=str) if before_data else None,
            after_data=json.dumps(after_data, ensure_ascii=False, default=str) if after_data else None,
            request_method=request_method,
            request_path=request_path,
            ip_address=ip_address,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_by_id(db: Session, log_id: int) -> Optional[AdminOperationLog]:
        """根据ID获取操作日志"""
        return db.query(AdminOperationLog).filter(
            AdminOperationLog.id == log_id,
            AdminOperationLog.is_deleted == False
        ).first()

    @staticmethod
    def get_list(
        db: Session,
        query_params: AdminOperationLogQuery
    ) -> tuple[List[AdminOperationLog], int]:
        """
        获取操作日志列表（分页 + 多条件筛选）

        Returns:
            (日志列表, 总数)
        """
        query = db.query(AdminOperationLog).filter(AdminOperationLog.is_deleted == False)

        conditions = []

        if query_params.user_id:
            conditions.append(AdminOperationLog.user_id == query_params.user_id)

        if query_params.username:
            conditions.append(AdminOperationLog.username.like(f"%{query_params.username}%"))

        if query_params.action:
            conditions.append(AdminOperationLog.action == query_params.action)

        if query_params.resource_type:
            conditions.append(AdminOperationLog.resource_type == query_params.resource_type)

        if query_params.start_time:
            conditions.append(AdminOperationLog.created_at >= query_params.start_time)

        if query_params.end_time:
            conditions.append(AdminOperationLog.created_at <= query_params.end_time)

        if conditions:
            query = query.filter(and_(*conditions))

        total = query.count()

        skip = (query_params.page - 1) * query_params.page_size
        logs = query.order_by(AdminOperationLog.created_at.desc()).offset(skip).limit(query_params.page_size).all()

        return logs, total

    @staticmethod
    def delete_old_logs(db: Session, days: int = 180) -> int:
        """逻辑删除旧操作日志"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        count = db.query(AdminOperationLog).filter(
            AdminOperationLog.created_at < cutoff_date,
            AdminOperationLog.is_deleted == False
        ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)})
        db.commit()
        return count
