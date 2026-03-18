"""
操作审计日志管理 API
提供管理员对系统资源的关键操作（增删改）记录的查询和清理功能。
用于管理后台的"操作审计日志"页面，帮助管理员追溯操作历史和安全审计。
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.admin_operation_log import AdminOperationLogResponse, AdminOperationLogQuery
from app.schemas.common import Response, PageResponse
from app.services.admin_operation_log_service import AdminOperationLogService
from app.utils.dependencies import get_current_admin_user
from app.utils.query_params import clean_query_params

router = APIRouter(prefix="/operation-logs", tags=["Operation Logs"])


@router.get(
    "/list",
    response_model=Response[PageResponse[AdminOperationLogResponse]],
    summary="Get operation audit log list",
    description="Paginated query of operation audit logs with filtering by operator, action type, "
                "resource type, and time range. Used for the operation audit page to trace system changes."
)
def get_operation_logs(
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page, max 100"),
    user_id: Optional[str] = Query(None, description="Filter by operator user ID"),
    username: Optional[str] = Query(None, description="Filter by operator username (fuzzy match)"),
    action: Optional[str] = Query(None, description="Filter by action type: CREATE / UPDATE / DELETE"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type: user / role / permission / menu"),
    start_time: Optional[str] = Query(None, description="Start time, format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="End time, format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    params = clean_query_params(
        user_id=(user_id, int),
        username=username,
        action=action,
        resource_type=resource_type,
        start_time=(start_time, datetime),
        end_time=(end_time, datetime)
    )

    query_params = AdminOperationLogQuery(
        page=page,
        page_size=page_size,
        **params
    )

    logs, total = AdminOperationLogService.get_list(db, query_params)

    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AdminOperationLogResponse.model_validate(log) for log in logs]
        )
    )


@router.get(
    "/detail/{log_id}",
    response_model=Response[AdminOperationLogResponse],
    summary="Get operation audit log detail",
    description="Get full details of a single operation log entry by ID, "
                "including before/after data for change tracking."
)
def get_operation_log(
    log_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    log = AdminOperationLogService.get_by_id(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日志不存在"
        )

    return Response(
        code=200,
        message="获取成功",
        data=AdminOperationLogResponse.model_validate(log)
    )


@router.post(
    "/cleanup",
    response_model=Response,
    summary="Clean up old operation logs",
    description="Soft-delete operation logs older than the specified number of days. "
                "Default is 180 days. This is a soft delete and data can be recovered."
)
def cleanup_old_operation_logs(
    days: int = Query(180, ge=1, le=730, description="Keep logs from the last N days, older ones will be soft-deleted"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    count = AdminOperationLogService.delete_old_logs(db, days)

    return Response(
        code=200,
        message=f"清理成功，删除了 {count} 条操作日志",
        data={"deleted_count": count}
    )
