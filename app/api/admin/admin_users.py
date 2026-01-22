"""
管理员用户管理API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.admin_user import (
    AdminUserCreate, AdminUserUpdate, AdminUserResponse, AdminUserPasswordChange, 
    CurrentAdminUser, AdminUserAssignRoles
)
from app.schemas.admin_user_permission_override import (
    AdminUserPermissionOverrideResponse, AdminUserPermissionOverrideBatchCreate
)
from app.schemas.admin_user_menu_override import (
    AdminUserMenuOverrideResponse, AdminUserMenuOverrideBatchCreate
)
from app.schemas.common import Response, PageResponse
from app.services.admin_user_service import AdminUserService
from app.services.admin_rbac_service import AdminRBACService
from app.utils.dependencies import get_current_admin_user, get_current_admin_user
from app.utils.query_params import clean_query_params

router = APIRouter(prefix="/admin_users", tags=["admin users"])


@router.get("/me", response_model=Response[CurrentAdminUser], summary="获取当前管理员用户信息")
def get_current_admin_user_info(
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """
    获取当前登录管理员用户的信息
    """
    return Response(
        code=200,
        message="获取成功",
        data=CurrentAdminUser.model_validate(current_user)
    )


@router.post("/me/update", response_model=Response[AdminUserResponse], summary="更新当前管理员用户信息")
def update_current_admin_user_info(
    user_in: AdminUserUpdate,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    更新当前登录管理员用户的信息
    """
    try:
        user = AdminUserService.update(db, current_user.id, user_in)
        return Response(
            code=200,
            message="更新成功",
            data=AdminUserResponse.model_validate(user)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/me/change-password", response_model=Response, summary="修改密码")
def change_password(
    password_in: AdminUserPasswordChange,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    修改当前管理员用户密码
    """
    try:
        AdminUserService.change_password(
            db,
            current_user.id,
            password_in.old_password,
            password_in.new_password
        )
        return Response(
            code=200,
            message="密码修改成功",
            data=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/list", response_model=Response[PageResponse[AdminUserResponse]], summary="获取管理员用户列表")
def get_admin_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[str] = Query(None, description="是否激活"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取管理员用户列表（需要管理员权限）
    
    必传参数：
    - page: 页码
    - page_size: 每页数量
    
    可选查询条件：
    - keyword: 搜索关键词（用户名、邮箱、全名）
    - is_active: 是否激活（true/false）
    """
    params = clean_query_params(
        keyword=keyword,
        is_active=(is_active, bool)
    )
    
    skip = (page - 1) * page_size
    users, total = AdminUserService.get_list(db, skip, page_size, params['keyword'], params['is_active'])
    
    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AdminUserResponse.model_validate(user) for user in users]
        )
    )


@router.get("/detail/{user_id}", response_model=Response[AdminUserResponse], summary="获取管理员用户详情")
def get_admin_user(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取指定管理员用户详情（需要管理员权限）
    """
    user = AdminUserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )
    
    return Response(
        code=200,
        message="获取成功",
        data=AdminUserResponse.model_validate(user)
    )


@router.post("/create", response_model=Response[AdminUserResponse], summary="创建管理员用户")
def create_admin_user(
    user_in: AdminUserCreate,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    创建管理员用户（需要管理员权限）
    """
    try:
        user = AdminUserService.create(db, user_in)
        return Response(
            code=200,
            message="创建成功",
            data=AdminUserResponse.model_validate(user)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/update/{user_id}", response_model=Response[AdminUserResponse], summary="更新管理员用户")
def update_admin_user(
    user_id: int,
    user_in: AdminUserUpdate,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    更新管理员用户信息（需要管理员权限）
    """
    try:
        user = AdminUserService.update(db, user_id, user_in)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="管理员用户不存在"
            )
        return Response(
            code=200,
            message="更新成功",
            data=AdminUserResponse.model_validate(user)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/delete/{user_id}", response_model=Response, summary="删除管理员用户")
def delete_admin_user(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    删除管理员用户（需要管理员权限）
    """
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    success = AdminUserService.delete(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )
    
    return Response(
        code=200,
        message="删除成功",
        data=None
    )


@router.post("/assign-roles/{user_id}", response_model=Response, summary="为用户分配角色")
def assign_roles(
    user_id: int,
    data: AdminUserAssignRoles,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    为用户分配角色（需要超级管理员权限）
    """
    # 检查用户是否存在
    user = AdminUserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )
    
    AdminRBACService.assign_user_roles(db, user_id, data.role_ids)
    
    return Response(
        code=200,
        message="分配角色成功",
        data=None
    )


@router.get("/roles/{user_id}", response_model=Response[list[int]], summary="获取用户的角色列表")
def get_user_roles(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的角色ID列表（需要超级管理员权限）
    """
    role_ids = AdminRBACService.get_user_roles(db, user_id)
    
    return Response(
        code=200,
        message="获取成功",
        data=role_ids
    )


@router.post("/permission-overrides/{user_id}", response_model=Response, summary="批量设置用户权限覆盖")
def set_permission_overrides(
    user_id: int,
    data: AdminUserPermissionOverrideBatchCreate,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    批量设置用户权限覆盖（需要超级管理员权限）
    """
    # 检查用户是否存在
    user = AdminUserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )
    
    for override in data.overrides:
        AdminRBACService.set_user_permission_overrides(
            db, user_id, override.permission_id, override.effect
        )
    
    return Response(
        code=200,
        message="设置权限覆盖成功",
        data=None
    )


@router.get("/permission-overrides/{user_id}", response_model=Response[list[AdminUserPermissionOverrideResponse]], summary="获取用户权限覆盖列表")
def get_permission_overrides(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取用户权限覆盖列表（需要超级管理员权限）
    """
    overrides = AdminRBACService.get_user_permission_overrides(db, user_id)
    
    return Response(
        code=200,
        message="获取成功",
        data=[AdminUserPermissionOverrideResponse.model_validate(o) for o in overrides]
    )


@router.post("/menu-overrides/{user_id}", response_model=Response, summary="批量设置用户菜单覆盖")
def set_menu_overrides(
    user_id: int,
    data: AdminUserMenuOverrideBatchCreate,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    批量设置用户菜单覆盖（需要超级管理员权限）
    """
    # 检查用户是否存在
    user = AdminUserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )
    
    for override in data.overrides:
        AdminRBACService.set_user_menu_overrides(
            db, user_id, override.menu_id, override.effect
        )
    
    return Response(
        code=200,
        message="设置菜单覆盖成功",
        data=None
    )


@router.get("/menu-overrides/{user_id}", response_model=Response[list[AdminUserMenuOverrideResponse]], summary="获取用户菜单覆盖列表")
def get_menu_overrides(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取用户菜单覆盖列表（需要超级管理员权限）
    """
    overrides = AdminRBACService.get_user_menu_overrides(db, user_id)
    
    return Response(
        code=200,
        message="获取成功",
        data=[AdminUserMenuOverrideResponse.model_validate(o) for o in overrides]
    )
