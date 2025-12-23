"""
API日志管理API
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.api_log import APILogResponse, APILogQuery
from app.schemas.common import Response, PageResponse
from app.services.api_log_service import APILogService
from app.utils.dependencies import get_current_user, get_current_superuser
from app.utils.query_params import clean_query_params

router = APIRouter(prefix="/logs", tags=["API logs"])


@router.get("/list", response_model=Response[PageResponse[APILogResponse]], summary="获取API日志列表")
def get_api_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    method: Optional[str] = Query(None, description="请求方法"),
    path: Optional[str] = Query(None, description="请求路径"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    username: Optional[str] = Query(None, description="用户名"),
    status_code: Optional[str] = Query(None, description="响应状态码"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    获取API日志列表（需要管理员权限）
    
    必传参数：
    - page: 页码
    - page_size: 每页数量
    
    可选查询条件：
    - method: 请求方法
    - path: 请求路径（模糊查询）
    - user_id: 用户ID
    - username: 用户名（模糊查询）
    - status_code: 响应状态码
    - start_time: 开始时间
    - end_time: 结束时间
    """
    params = clean_query_params(
        method=method,
        path=path,
        user_id=(user_id, int),
        username=username,
        status_code=(status_code, int),
        start_time=(start_time, datetime),
        end_time=(end_time, datetime)
    )
    
    query_params = APILogQuery(
        page=page,
        page_size=page_size,
        **params
    )
    
    logs, total = APILogService.get_list(db, query_params)
    
    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[APILogResponse.model_validate(log) for log in logs]
        )
    )


@router.get("/detail/{log_id}", response_model=Response[APILogResponse], summary="获取API日志详情")
def get_api_log(
    log_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    获取指定API日志详情（需要管理员权限）
    """
    log = APILogService.get_by_id(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日志不存在"
        )
    
    return Response(
        code=200,
        message="获取成功",
        data=APILogResponse.model_validate(log)
    )


@router.get("/my", response_model=Response[PageResponse[APILogResponse]], summary="获取我的API日志")
def get_my_api_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的API日志
    """
    query_params = APILogQuery(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    
    logs, total = APILogService.get_list(db, query_params)
    
    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[APILogResponse.model_validate(log) for log in logs]
        )
    )


@router.get("/statistics", response_model=Response, summary="获取日志统计")
def get_log_statistics(
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    获取API日志统计信息（需要管理员权限）
    
    返回：
    - 总请求数
    - 各状态码统计
    - 平均响应时长
    """
    params = clean_query_params(
        start_time=(start_time, datetime),
        end_time=(end_time, datetime)
    )
    
    stats = APILogService.get_statistics(db, params['start_time'], params['end_time'])
    
    return Response(
        code=200,
        message="获取成功",
        data=stats
    )


@router.post("/cleanup", response_model=Response, summary="清理旧日志")
def cleanup_old_logs(
    days: int = Query(30, ge=1, le=365, description="保留最近多少天的日志"),
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    清理旧日志（需要管理员权限）
    
    删除指定天数之前的日志
    """
    count = APILogService.delete_old_logs(db, days)
    
    return Response(
        code=200,
        message=f"清理成功，删除了 {count} 条日志",
        data={"deleted_count": count}
    )
