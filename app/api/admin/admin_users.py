"""
管理员用户管理API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
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
from app.schemas.admin_menu import AdminMenuTreeNode
from app.schemas.admin_permission import AdminPermissionResponse, UserPermissionsDetailResponse, UserPermissionOverrideItem
from app.schemas.common import Response, PageResponse
from app.services.admin_user_service import AdminUserService
from app.services.admin_rbac_service import AdminRBACService
from app.utils.dependencies import get_current_admin_user, get_current_admin_user
from app.utils.query_params import clean_query_params
from app.utils.operation_log import log_operation

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
    request: Request,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    创建管理员用户（需要管理员权限）
    """
    try:
        user = AdminUserService.create(db, user_in)
        log_operation(
            db, request=request, action="CREATE", resource_type="user",
            resource_id=user.id, description=f"创建用户 {user.username}",
        )
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
    request: Request,
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

    target_user = AdminUserService.get_by_id(db, user_id)
    success = AdminUserService.delete(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )

    log_operation(
        db, request=request, action="DELETE", resource_type="user",
        resource_id=user_id,
        description=f"删除用户 {target_user.username if target_user else user_id}",
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
    request: Request,
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

    old_role_ids = AdminRBACService.get_user_roles(db, user_id)
    AdminRBACService.assign_user_roles(db, user_id, data.role_ids)
    log_operation(
        db, request=request, action="UPDATE", resource_type="user",
        resource_id=user_id,
        description=f"为用户 {user.username} 分配角色",
        before_data={"role_ids": old_role_ids},
        after_data={"role_ids": data.role_ids},
    )

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


@router.post("/clear-permission-overrides/{user_id}", response_model=Response, summary="清除用户所有权限覆盖")
def clear_permission_overrides(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    清除用户的所有权限覆盖（需要超级管理员权限）
    """
    # 检查用户是否存在
    user = AdminUserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )
    
    AdminRBACService.clear_all_permission_overrides(db, user_id)
    
    return Response(
        code=200,
        message="清除权限覆盖成功",
        data=None
    )


@router.post("/clear-menu-overrides/{user_id}", response_model=Response, summary="清除用户所有菜单覆盖")
def clear_menu_overrides(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    清除用户的所有菜单覆盖（需要超级管理员权限）
    """
    # 检查用户是否存在
    user = AdminUserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )
    
    AdminRBACService.clear_all_menu_overrides(db, user_id)
    
    return Response(
        code=200,
        message="清除菜单覆盖成功",
        data=None
    )


@router.get("/complete-menus/{user_id}", response_model=Response[list[AdminMenuTreeNode]], summary="获取用户完整菜单")
def get_complete_menus(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的完整菜单（角色菜单并集 + 覆盖）（需要超级管理员权限）
    复用登录时返回给前端的菜单表逻辑
    """
    # 检查用户是否存在
    user = AdminUserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )
    
    # 复用 AdminRBACService.get_user_menus 方法
    menus = AdminRBACService.get_user_menus(db, user_id)
    
    return Response(
        code=200,
        message="获取成功",
        data=menus
    )


@router.get("/complete-permissions/{user_id}", response_model=Response[PageResponse[AdminPermissionResponse]], summary="获取用户完整权限列表")
def get_complete_permissions(
    user_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的完整权限列表（角色权限并集 + 覆盖）（需要超级管理员权限）
    
    必传参数：
    - page: 页码
    - page_size: 每页数量
    
    可选查询条件：
    - keyword: 搜索关键词（权限名称、API路径）
    """
    # 检查用户是否存在
    user = AdminUserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )
    
    params = clean_query_params(keyword=keyword)
    
    skip = (page - 1) * page_size
    permissions, total = AdminRBACService.get_user_complete_permissions(
        db, user_id, skip, page_size, params['keyword']
    )
    
    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AdminPermissionResponse.model_validate(p) for p in permissions]
        )
    )


@router.post("/toggle-status/{user_id}", response_model=Response, summary="调整用户启用状态")
def toggle_user_status(
    user_id: int,
    request: Request,
    is_active: bool = Body(..., embed=True, description="是否启用"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    启用或禁用管理员用户账户（需要超级管理员权限）
    """
    # 不能禁用自己的账户
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己的账户"
        )

    user = AdminUserService.toggle_status(db, user_id, is_active)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )

    status_text = "启用" if is_active else "禁用"
    log_operation(
        db, request=request, action="UPDATE", resource_type="user",
        resource_id=user_id,
        description=f"{status_text}用户 {user.username}",
    )

    return Response(
        code=200,
        message=f"{status_text}用户成功",
        data=None
    )


@router.get("/permissions-detail/{user_id}", response_model=Response[UserPermissionsDetailResponse], summary="获取用户权限详情")
def get_user_permissions_detail(
    user_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的完整权限详情（按分组展示）
    
    返回按 group_key 分组的权限列表，每个分组包含：
    - group_key: 分组标识
    - group_name: 分组名称
    - group_permission: 组权限（如果有）
    - children: 子权限列表
    
    每个权限项包含：
    - id, name, resource_pattern, method
    - effect: allow/deny
    - source: 权限来源信息（包含角色信息或用户覆盖标识）
    - source_description: 来源描述文本
    - is_inherited: 是否从组权限继承
    - is_overridden: 是否被覆盖
    
    权限来源说明：
    - 允许于角色[角色名]的组权限[权限名]
    - 允许于角色[角色名]的子权限[权限名]
    - 允许于用户权限覆盖
    - 拒绝于角色[角色名]的组权限[权限名]
    - 拒绝于角色[角色名]的子权限[权限名]
    - 拒绝于用户权限覆盖
    """
    try:
        result = AdminRBACService.get_user_permissions_detail(db, user_id)
        return Response(
            code=200,
            message="获取成功",
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/permissions-for-override/{user_id}", response_model=Response[PageResponse[UserPermissionOverrideItem]], summary="获取用户权限覆盖管理列表")
def get_permissions_for_override(
    user_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    overridden: Optional[str] = Query(None, description="覆盖状态筛选：overridden=已覆盖, not_overridden=未覆盖"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取用户权限覆盖管理列表（需要超级管理员权限）
    
    用于管理员查看和管理用户的权限覆盖状态。
    返回所有非组权限，标记每个权限的角色授权状态和用户覆盖状态。
    
    必传参数：
    - page: 页码
    - page_size: 每页数量
    
    可选查询条件：
    - keyword: 搜索关键词（权限名称、资源模式）
    - overridden: 覆盖状态筛选（overridden=已覆盖, not_overridden=未覆盖）
    
    返回字段说明：
    - id: 权限ID
    - name: 权限名称
    - resource_pattern: 资源模式
    - method: HTTP方法
    - group_key: 分组标识
    - group_name: 分组名称
    - description: 描述
    
    角色层面状态：
    - role_granted: 角色是否已授权（直接或继承）
    - role_effect: 角色授权效果（allow/deny），未授权时为 null
    - role_source: 角色授权来源描述（如"角色[管理员]的组权限[系统信息]"）
    - is_inherited: 是否从组权限继承
    
    用户覆盖状态：
    - is_overridden: 是否已被用户覆盖
    - override_effect: 用户覆盖效果（allow/deny），未覆盖时为 null
    
    最终状态：
    - final_effect: 最终效果（allow/deny）
    - source_description: 最终来源描述
    """
    # 检查用户是否存在
    user = AdminUserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员用户不存在"
        )
    
    params = clean_query_params(keyword=keyword)
    
    skip = (page - 1) * page_size
    try:
        items, total = AdminRBACService.get_user_permissions_for_override_management(
            db, user_id, skip, page_size, params['keyword'], overridden
        )
        
        return Response(
            code=200,
            message="获取成功",
            data=PageResponse(
                total=total,
                page=page,
                page_size=page_size,
                items=items
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
