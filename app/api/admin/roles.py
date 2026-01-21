"""
管理员角色管理API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.admin_role import (
    AdminRoleCreate, AdminRoleUpdate, AdminRoleResponse,
    AdminRoleAssignPermissions, AdminRoleAssignMenus
)
from app.schemas.common import Response, PageResponse
from app.services.admin_role_service import AdminRoleService
from app.utils.dependencies import get_current_superuser
from app.utils.query_params import clean_query_params

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/list", response_model=Response[PageResponse[AdminRoleResponse]], summary="获取角色列表")
def get_roles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: AdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    获取角色列表（需要超级管理员权限）
    
    必传参数：
    - page: 页码
    - page_size: 每页数量
    
    可选查询条件：
    - keyword: 搜索关键词（角色名称）
    - status: 状态（1=启用，0=禁用）
    """
    params = clean_query_params(
        keyword=keyword,
        status=(status, int)
    )
    
    skip = (page - 1) * page_size
    roles, total = AdminRoleService.get_list(db, skip, page_size, params['keyword'], params['status'])
    
    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AdminRoleResponse.model_validate(role) for role in roles]
        )
    )


@router.get("/detail/{role_id}", response_model=Response[AdminRoleResponse], summary="获取角色详情")
def get_role(
    role_id: int,
    current_user: AdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    获取指定角色详情（需要超级管理员权限）
    """
    role = AdminRoleService.get_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    return Response(
        code=200,
        message="获取成功",
        data=AdminRoleResponse.model_validate(role)
    )


@router.post("/create", response_model=Response[AdminRoleResponse], summary="创建角色")
def create_role(
    role_in: AdminRoleCreate,
    current_user: AdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    创建角色（需要超级管理员权限）
    """
    try:
        role = AdminRoleService.create(db, role_in)
        return Response(
            code=200,
            message="创建成功",
            data=AdminRoleResponse.model_validate(role)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/update/{role_id}", response_model=Response[AdminRoleResponse], summary="更新角色")
def update_role(
    role_id: int,
    role_in: AdminRoleUpdate,
    current_user: AdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    更新角色信息（需要超级管理员权限）
    """
    try:
        role = AdminRoleService.update(db, role_id, role_in)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return Response(
            code=200,
            message="更新成功",
            data=AdminRoleResponse.model_validate(role)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/delete/{role_id}", response_model=Response, summary="删除角色")
def delete_role(
    role_id: int,
    current_user: AdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    删除角色（需要超级管理员权限）
    """
    success = AdminRoleService.delete(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    return Response(
        code=200,
        message="删除成功",
        data=None
    )


@router.post("/assign-permissions/{role_id}", response_model=Response, summary="为角色分配权限")
def assign_permissions(
    role_id: int,
    data: AdminRoleAssignPermissions,
    current_user: AdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    为角色分配权限（需要超级管理员权限）
    """
    success = AdminRoleService.assign_permissions(db, role_id, data.permission_ids)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    return Response(
        code=200,
        message="分配权限成功",
        data=None
    )


@router.post("/assign-menus/{role_id}", response_model=Response, summary="为角色分配菜单")
def assign_menus(
    role_id: int,
    data: AdminRoleAssignMenus,
    current_user: AdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    为角色分配菜单（需要超级管理员权限）
    """
    success = AdminRoleService.assign_menus(db, role_id, data.menu_ids)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    return Response(
        code=200,
        message="分配菜单成功",
        data=None
    )


@router.get("/permissions/{role_id}", response_model=Response[list[int]], summary="获取角色的权限列表")
def get_role_permissions(
    role_id: int,
    current_user: AdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    获取角色的权限ID列表（需要超级管理员权限）
    """
    permission_ids = AdminRoleService.get_role_permissions(db, role_id)
    
    return Response(
        code=200,
        message="获取成功",
        data=permission_ids
    )


@router.get("/menus/{role_id}", response_model=Response[list[int]], summary="获取角色的菜单列表")
def get_role_menus(
    role_id: int,
    current_user: AdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    获取角色的菜单ID列表（需要超级管理员权限）
    """
    menu_ids = AdminRoleService.get_role_menus(db, role_id)
    
    return Response(
        code=200,
        message="获取成功",
        data=menu_ids
    )







