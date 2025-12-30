"""
API日志服务层
处理API日志相关的业务逻辑
"""
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.api_log import APILog
from app.schemas.api_log import APILogQuery


class APILogService:
    """API日志服务"""
    
    @staticmethod
    def get_by_id(db: Session, log_id: int) -> Optional[APILog]:
        """
        根据ID获取日志
        """
        return db.query(APILog).filter(
            APILog.id == log_id,
            APILog.is_deleted == False
        ).first()
    
    @staticmethod
    def get_list(
        db: Session,
        query_params: APILogQuery
    ) -> tuple[List[APILog], int]:
        """
        获取日志列表
        
        Returns:
            (日志列表, 总数)
        """
        query = db.query(APILog).filter(APILog.is_deleted == False)
        
        # 构建查询条件
        conditions = []
        
        if query_params.method:
            conditions.append(APILog.method == query_params.method)
        
        if query_params.path:
            conditions.append(APILog.path.like(f"%{query_params.path}%"))
        
        if query_params.user_id:
            conditions.append(APILog.user_id == query_params.user_id)
        
        if query_params.username:
            conditions.append(APILog.username.like(f"%{query_params.username}%"))
        
        if query_params.status_code:
            conditions.append(APILog.status_code == query_params.status_code)
        
        if query_params.start_time:
            conditions.append(APILog.created_at >= query_params.start_time)
        
        if query_params.end_time:
            conditions.append(APILog.created_at <= query_params.end_time)
        
        # 应用条件
        if conditions:
            query = query.filter(and_(*conditions))
        
        # 获取总数
        total = query.count()
        
        # 分页
        skip = (query_params.page - 1) * query_params.page_size
        logs = query.order_by(APILog.created_at.desc()).offset(skip).limit(query_params.page_size).all()
        
        return logs, total
    
    @staticmethod
    def delete_old_logs(db: Session, days: int = 30) -> int:
        """
        逻辑删除旧日志
        
        Args:
            days: 保留最近多少天的日志
            
        Returns:
            删除的日志数量
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # 逻辑删除
        count = db.query(APILog).filter(
            APILog.created_at < cutoff_date,
            APILog.is_deleted == False
        ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)})
        db.commit()
        
        return count
    
    @staticmethod
    def get_statistics(
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> dict:
        """
        获取统计信息
        """
        query = db.query(APILog).filter(APILog.is_deleted == False)
        
        if start_time:
            query = query.filter(APILog.created_at >= start_time)
        
        if end_time:
            query = query.filter(APILog.created_at <= end_time)
        
        total = query.count()
        
        # 按状态码统计
        status_stats = {}
        for status_code in [200, 400, 401, 403, 404, 500]:
            count = query.filter(APILog.status_code == status_code).count()
            status_stats[status_code] = count
        
        # 平均响应时长
        avg_duration_query = db.query(func.avg(APILog.duration)).filter(APILog.is_deleted == False)
        if start_time:
            avg_duration_query = avg_duration_query.filter(APILog.created_at >= start_time)
        if end_time:
            avg_duration_query = avg_duration_query.filter(APILog.created_at <= end_time)
        
        avg_duration = avg_duration_query.scalar() or 0
        
        return {
            "total": total,
            "status_stats": status_stats,
            "avg_duration": round(avg_duration, 3)
        }


