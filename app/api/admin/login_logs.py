"""
登录日志管理 API
提供管理员用户登录行为记录的查询、统计和清理功能。
用于管理后台的"登录日志"页面，帮助管理员监控账户安全和登录异常。
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.admin_login_log import AdminLoginLogResponse, AdminLoginLogQuery, AdminLoginLogStatistics
from app.schemas.common import Response, PageResponse
from app.services.admin_login_log_service import AdminLoginLogService
from app.utils.dependencies import get_current_admin_user
from app.utils.query_params import clean_query_params

router = APIRouter(prefix="/login-logs", tags=["Login Logs"])


@router.get(
    "/list",
    response_model=Response[PageResponse[AdminLoginLogResponse]],
    summary="Get login log list",
    description="Paginated query of admin login logs with filtering by username, login result, IP, and time range. "
                "Used for the login log management page to monitor account security."
)
def get_login_logs(
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page, max 100"),
    username: Optional[str] = Query(None, description="Filter by username (fuzzy match)"),
    success: Optional[str] = Query(None, description="Filter by login result: true=success only, false=failure only"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address (fuzzy match)"),
    start_time: Optional[str] = Query(None, description="Start time, format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="End time, format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    params = clean_query_params(
        username=username,
        success=(success, bool),
        ip_address=ip_address,
        start_time=(start_time, datetime),
        end_time=(end_time, datetime)
    )

    query_params = AdminLoginLogQuery(
        page=page,
        page_size=page_size,
        **params
    )

    logs, total = AdminLoginLogService.get_list(db, query_params)

    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AdminLoginLogResponse.model_validate(log) for log in logs]
        )
    )


@router.get(
    "/detail/{log_id}",
    response_model=Response[AdminLoginLogResponse],
    summary="Get login log detail",
    description="Get full details of a single login log entry by ID."
)
def get_login_log(
    log_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    log = AdminLoginLogService.get_by_id(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日志不存在"
        )

    return Response(
        code=200,
        message="获取成功",
        data=AdminLoginLogResponse.model_validate(log)
    )


@router.get(
    "/statistics",
    response_model=Response[AdminLoginLogStatistics],
    summary="Get login log statistics",
    description="Get login log statistics overview including total login count, success count, and failure count. "
                "Used for dashboard to show login trends. Supports filtering by time range."
)
def get_login_log_statistics(
    start_time: Optional[str] = Query(None, description="Start time, format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="End time, format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    params = clean_query_params(
        start_time=(start_time, datetime),
        end_time=(end_time, datetime)
    )

    stats = AdminLoginLogService.get_statistics(db, params.get('start_time'), params.get('end_time'))

    return Response(
        code=200,
        message="获取成功",
        data=stats
    )


@router.post(
    "/cleanup",
    response_model=Response,
    summary="Clean up old login logs",
    description="Soft-delete login logs older than the specified number of days. "
                "Default is 90 days. This is a soft delete and data can be recovered."
)
def cleanup_old_login_logs(
    days: int = Query(90, ge=1, le=365, description="Keep logs from the last N days, older ones will be soft-deleted"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    count = AdminLoginLogService.delete_old_logs(db, days)

    return Response(
        code=200,
        message=f"清理成功，删除了 {count} 条登录日志",
        data={"deleted_count": count}
    )
