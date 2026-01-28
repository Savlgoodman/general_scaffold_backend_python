"""
管理员权限管理API
"""
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.admin_permission import (
    AdminPermissionCreate, AdminPermissionUpdate, AdminPermissionResponse
)
from app.schemas.common import Response, PageResponse
from app.services.admin_permission_service import AdminPermissionService
from app.utils.dependencies import get_current_admin_user
from app.utils.query_params import clean_query_params

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("/list", response_model=Response[PageResponse[AdminPermissionResponse]], summary="获取权限列表")
def get_permissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=10000, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态"),
    group_key: Optional[str] = Query(None, description="分组标识"),
    is_group: Optional[str] = Query(None, description="是否组权限"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取权限列表（需要超级管理员权限）
    
    必传参数：
    - page: 页码
    - page_size: 每页数量
    
    可选查询条件：
    - keyword: 搜索关键词（权限名称、资源模式）
    - status: 状态（1=启用，0=禁用）
    - group_key: 分组标识
    - is_group: 是否组权限（true/false）
    """
    params = clean_query_params(
        keyword=keyword,
        status=(status, int),
        group_key=group_key,
        is_group=(is_group, bool)
    )
    
    skip = (page - 1) * page_size
    permissions, total = AdminPermissionService.get_list(
        db, skip, page_size, 
        params['keyword'], 
        params['status'],
        params['group_key'],
        params['is_group']
    )
    
    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AdminPermissionResponse.model_validate(permission) for permission in permissions]
        )
    )


@router.get("/detail/{permission_id}", response_model=Response[AdminPermissionResponse], summary="获取权限详情")
def get_permission(
    permission_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取指定权限详情（需要超级管理员权限）
    """
    permission = AdminPermissionService.get_by_id(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    return Response(
        code=200,
        message="获取成功",
        data=AdminPermissionResponse.model_validate(permission)
    )


@router.post("/create", response_model=Response[AdminPermissionResponse], summary="创建权限")
def create_permission(
    permission_in: AdminPermissionCreate,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    创建权限（需要超级管理员权限）
    """
    try:
        permission = AdminPermissionService.create(db, permission_in)
        return Response(
            code=200,
            message="创建成功",
            data=AdminPermissionResponse.model_validate(permission)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/update/{permission_id}", response_model=Response[AdminPermissionResponse], summary="更新权限")
def update_permission(
    permission_id: int,
    permission_in: AdminPermissionUpdate,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    更新权限信息（需要超级管理员权限）
    """
    try:
        permission = AdminPermissionService.update(db, permission_id, permission_in)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        return Response(
            code=200,
            message="更新成功",
            data=AdminPermissionResponse.model_validate(permission)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/delete/{permission_id}", response_model=Response, summary="删除权限")
def delete_permission(
    permission_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    删除权限（需要超级管理员权限）
    """
    success = AdminPermissionService.delete(db, permission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    return Response(
        code=200,
        message="删除成功",
        data=None
    )


@router.get("/groups", response_model=Response[Dict[str, List[AdminPermissionResponse]]], summary="获取分组权限列表")
def get_grouped_permissions(
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取按分组组织的权限列表（需要超级管理员权限）
    
    返回按 group_key 分组的权限字典
    """
    grouped = AdminPermissionService.get_grouped_permissions(db)
    
    # 转换为响应格式
    result = {}
    for group_key, permissions in grouped.items():
        result[group_key] = [AdminPermissionResponse.model_validate(p) for p in permissions]
    
    return Response(
        code=200,
        message="获取成功",
        data=result
    )







