"""
系统信息API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.system_info import (
    SystemResourcesResponse, NetworkStatsResponse,
    RedisStatusResponse, RedisKeyValueResponse,
    FailedLoginStatsResponse
)
from app.schemas.common import Response, PageResponse
from app.services.system_info_service import SystemInfoService
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/system_info", tags=["system info"])


@router.get("/resources", response_model=Response[SystemResourcesResponse], summary="获取系统资源使用情况")
def get_system_resources(
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """
    获取系统资源使用情况（CPU和内存）（需要管理员权限）
    """
    resources = SystemInfoService.get_system_resources()
    
    return Response(
        code=200,
        message="获取成功",
        data=SystemResourcesResponse(**resources)
    )


@router.get("/network", response_model=Response[NetworkStatsResponse], summary="获取网络统计信息")
def get_network_stats(
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """
    获取网络统计信息（需要管理员权限）
    """
    stats = SystemInfoService.get_network_stats()
    
    return Response(
        code=200,
        message="获取成功",
        data=NetworkStatsResponse(**stats)
    )


@router.get("/redis/status", response_model=Response[RedisStatusResponse], summary="获取Redis状态")
def get_redis_status(
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """
    获取Redis连接状态和基本信息（需要管理员权限）
    """
    redis_status = SystemInfoService.get_redis_status()
    
    return Response(
        code=200,
        message="获取成功",
        data=RedisStatusResponse(**redis_status)
    )


@router.get("/redis/keys", response_model=Response[PageResponse[RedisKeyValueResponse]], summary="查询Redis键值对")
def get_redis_keys(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    pattern: Optional[str] = Query(None, description="键名模式"),
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """
    分页查询Redis键值对，支持模式匹配（需要管理员权限）
    
    必传参数：
    - page: 页码
    - page_size: 每页数量
    
    可选查询条件：
    - pattern: 键名模式（支持Redis模式如 "user:*"）
    """
    # 检查Redis连接
    redis_status = SystemInfoService.get_redis_status()
    if not redis_status.get("connected"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis服务不可用"
        )
    
    skip = (page - 1) * page_size
    keys, total = SystemInfoService.get_redis_keys(skip, page_size, pattern)
    
    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[RedisKeyValueResponse(**k) for k in keys]
        )
    )


@router.get("/failed-logins", response_model=Response[FailedLoginStatsResponse], summary="获取今日失败登录统计")
def get_failed_login_stats(
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    统计今日失败的登录尝试次数（需要管理员权限）
    """
    stats = SystemInfoService.get_failed_login_stats(db)
    
    return Response(
        code=200,
        message="获取成功",
        data=FailedLoginStatsResponse(**stats)
    )
