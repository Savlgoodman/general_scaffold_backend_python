"""
操作审计日志工具函数
提供便捷的操作日志记录方法，供关键业务接口调用
"""
from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session

from app.services.admin_operation_log_service import AdminOperationLogService


def log_operation(
    db: Session,
    *,
    request: Request,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    description: Optional[str] = None,
    before_data: Optional[dict] = None,
    after_data: Optional[dict] = None,
):
    """
    记录操作审计日志的便捷函数。

    Args:
        db: 数据库会话
        request: FastAPI Request 对象，自动提取 user_id/username/ip/method/path
        action: 操作类型，如 CREATE / UPDATE / DELETE
        resource_type: 操作对象类型，如 user / role / permission / menu
        resource_id: 操作对象ID
        description: 操作描述
        before_data: 变更前数据 (dict, 自动序列化为 JSON)
        after_data: 变更后数据 (dict, 自动序列化为 JSON)
    """
    user_id = getattr(request.state, "user_id", None)
    username = getattr(request.state, "username", None) or "unknown"

    AdminOperationLogService.record(
        db,
        user_id=user_id or 0,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        before_data=before_data,
        after_data=after_data,
        request_method=request.method,
        request_path=str(request.url.path),
        ip_address=request.client.host if request.client else None,
    )
