"""
系统异常日志管理 API
提供系统运行中产生的 WARNING/ERROR/CRITICAL 级别异常日志的查询、统计和清理功能。
用于管理后台的"系统异常日志"页面，帮助运维人员快速定位和排查系统问题。
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.app_error_log import AppErrorLogResponse, AppErrorLogQuery, AppErrorLogStatistics
from app.schemas.common import Response, PageResponse
from app.services.app_error_log_service import AppErrorLogService
from app.utils.dependencies import get_current_admin_user
from app.utils.query_params import clean_query_params

router = APIRouter(prefix="/error-logs", tags=["系统异常日志"])


@router.get(
    "/list",
    response_model=Response[PageResponse[AppErrorLogResponse]],
    summary="获取系统异常日志列表",
    description="分页查询系统异常日志，支持按日志级别、关键词、请求路径、用户ID、时间范围等多条件筛选。"
                "用于管理后台的异常日志列表页面，帮助运维人员排查系统问题。"
)
def get_error_logs(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    level: Optional[str] = Query(None, description="日志级别筛选，可选值：WARNING / ERROR / CRITICAL"),
    keyword: Optional[str] = Query(None, description="按日志消息内容模糊搜索"),
    request_path: Optional[str] = Query(None, description="按请求路径模糊搜索，如 /api/admin/users"),
    user_id: Optional[str] = Query(None, description="按触发异常的用户ID精确筛选"),
    start_time: Optional[str] = Query(None, description="起始时间，格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="结束时间，格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    params = clean_query_params(
        level=level,
        keyword=keyword,
        request_path=request_path,
        user_id=(user_id, int),
        start_time=(start_time, datetime),
        end_time=(end_time, datetime)
    )

    query_params = AppErrorLogQuery(
        page=page,
        page_size=page_size,
        **params
    )

    logs, total = AppErrorLogService.get_list(db, query_params)

    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AppErrorLogResponse.model_validate(log) for log in logs]
        )
    )


@router.get(
    "/detail/{log_id}",
    response_model=Response[AppErrorLogResponse],
    summary="获取异常日志详情",
    description="根据日志ID获取单条异常日志的完整信息，包括完整的异常堆栈。"
                "用于点击列表中某���日志后查��详情。"
)
def get_error_log(
    log_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    log = AppErrorLogService.get_by_id(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日志不存在"
        )

    return Response(
        code=200,
        message="获取成功",
        data=AppErrorLogResponse.model_validate(log)
    )


@router.get(
    "/statistics",
    response_model=Response[AppErrorLogStatistics],
    summary="获取异常日志统计",
    description="获取系统异常日志的统计概览，包括各级别（WARNING/ERROR/CRITICAL）的日志数量。"
                "用于管理后台仪表盘展示异常趋势，支持按时间范围筛选。"
)
def get_error_log_statistics(
    start_time: Optional[str] = Query(None, description="统计起始时间，格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="统计结束时间，格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    params = clean_query_params(
        start_time=(start_time, datetime),
        end_time=(end_time, datetime)
    )

    stats = AppErrorLogService.get_statistics(db, params.get('start_time'), params.get('end_time'))

    return Response(
        code=200,
        message="获取成功",
        data=stats
    )


@router.post(
    "/cleanup",
    response_model=Response,
    summary="清理旧异常日志",
    description="逻辑删除指定天数之前的异常日志，用于定期清理历史日志、释放数据库空间。"
                "默认清理30天前的日志，最长可清理365天前的日志。此操作为软删除，不会物理删除数据。"
)
def cleanup_old_error_logs(
    days: int = Query(30, ge=1, le=365, description="保留最近多少天的日志，超出的将被逻辑删除"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    count = AppErrorLogService.delete_old_logs(db, days)

    return Response(
        code=200,
        message=f"清理成功，删除了 {count} 条异常日志",
        data={"deleted_count": count}
    )
