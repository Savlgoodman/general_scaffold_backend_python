"""
管理员角色管理API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.admin_role import (
    AdminRoleCreate, AdminRoleUpdate, AdminRoleResponse,
    AdminRoleAssignPermissions, AdminRoleAssignMenus
)
from app.schemas.admin_permission import (
    PermissionAssignment, RolePermissionsGroupedResponse,
    RoleGroupPermissionsResponse, NonGroupPermissionItem,
    RolePermissionsDetailResponse
)
from app.schemas.common import Response, PageResponse
from app.services.admin_role_service import AdminRoleService
from app.services.admin_rbac_service import AdminRBACService
from app.utils.dependencies import get_current_admin_user
from app.utils.query_params import clean_query_params
from app.utils.operation_log import log_operation

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/list", response_model=Response[PageResponse[AdminRoleResponse]], summary="获取角色列表")
def get_roles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=10000, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: AdminUser = Depends(get_current_admin_user),
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
    current_user: AdminUser = Depends(get_current_admin_user),
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
    request: Request,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    创建角色（需要超级管理员权限）
    """
    try:
        role = AdminRoleService.create(db, role_in)
        log_operation(
            db, request=request, action="CREATE", resource_type="role",
            resource_id=role.id, description=f"创建角色 {role.name}",
        )
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
    current_user: AdminUser = Depends(get_current_admin_user),
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
    request: Request,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    删除角色（需要超级管理员权限）
    """
    role = AdminRoleService.get_by_id(db, role_id)
    success = AdminRoleService.delete(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )

    log_operation(
        db, request=request, action="DELETE", resource_type="role",
        resource_id=role_id,
        description=f"删除角色 {role.name if role else role_id}",
    )

    return Response(
        code=200,
        message="删除成功",
        data=None
    )


@router.post("/assign-permissions/{role_id}", response_model=Response, summary="为角色分配组权限")
def assign_permissions(
    role_id: int,
    data: AdminRoleAssignPermissions,
    request: Request,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    为角色分配组权限（只能分配 is_group=True 的权限）

    组权限会自动继承到所有匹配的子权限
    """
    try:
        success = AdminRoleService.assign_group_permissions(db, role_id, data.permission_ids)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )

        role = AdminRoleService.get_by_id(db, role_id)
        log_operation(
            db, request=request, action="UPDATE", resource_type="role",
            resource_id=role_id,
            description=f"为角色 {role.name if role else role_id} 分配组权限",
            after_data={"permission_ids": data.permission_ids},
        )

        return Response(
            code=200,
            message="分配组权限成功",
            data=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/assign-menus/{role_id}", response_model=Response, summary="为角色分配菜单")
def assign_menus(
    role_id: int,
    data: AdminRoleAssignMenus,
    current_user: AdminUser = Depends(get_current_admin_user),
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


@router.get("/permissions/{role_id}", response_model=Response[PageResponse[NonGroupPermissionItem]], summary="获取角色的非组权限列表")
def get_role_permissions(
    role_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=10000, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    granted: Optional[str] = Query(None, description="授权状态：granted=已授权，not_granted=未授权，不传=全部"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取角色的非组权限列表（分页）
    
    返回所有非组权限，已授权的会标记 is_granted=True
    
    筛选参数：
    - keyword: 搜索权限名称或资源模式
    - granted: 授权状态筛选
    """
    # 检查角色是否存在
    role = AdminRoleService.get_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    params = clean_query_params(
        keyword=keyword,
        granted=granted
    )
    
    skip = (page - 1) * page_size
    items, total = AdminRBACService.get_role_non_group_permissions(
        db, role_id, skip, page_size, 
        keyword=params['keyword'], 
        granted=params['granted']
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


@router.get("/menus/{role_id}", response_model=Response[list[int]], summary="获取角色的菜单列表")
def get_role_menus(
    role_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
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


@router.get("/permissions-grouped/{role_id}", response_model=Response[RoleGroupPermissionsResponse], summary="获取角色的组权限列表")
def get_role_permissions_grouped(
    role_id: int,
    granted: Optional[str] = Query(None, description="授权状态：granted=已授权，not_granted=未授权，不传=全部"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取所有组权限列表，已授权的会标记 is_granted=True
    
    筛选参数：
    - granted: 授权状态筛选
    """
    # 检查角色是否存在
    role = AdminRoleService.get_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    params = clean_query_params(granted=granted)
    
    result = AdminRBACService.get_role_group_permissions(db, role_id, granted=params['granted'])
    
    return Response(
        code=200,
        message="获取成功",
        data=result
    )


@router.post("/permissions-assign/{role_id}", response_model=Response, summary="为角色分配具体权限（支持effect和priority）")
def assign_role_permissions_with_effect(
    role_id: int,
    assignments: List[PermissionAssignment],
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    为角色分配具体权限（只能分配 is_group=False 的非组权限）
    
    支持设置 effect 和 priority，用于细粒度权限控制：
    - effect: allow（允许）或 deny（拒绝）
    - priority: 优先级，数值越大优先级越高
    
    请求体示例：
    ```json
    [
        {"permission_id": 1, "effect": "allow", "priority": 0},
        {"permission_id": 2, "effect": "deny", "priority": 100}
    ]
    ```
    """
    # 检查角色是否存在
    role = AdminRoleService.get_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    try:
        AdminRBACService.assign_non_group_permissions(db, role_id, assignments)
        return Response(
            code=200,
            message="分配权限成功",
            data=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/permissions-remove/{role_id}", response_model=Response, summary="移除角色的权限")
def remove_role_permissions(
    role_id: int,
    permission_ids: List[int],
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    移除角色的权限
    
    请求体示例：
    ```json
    [1, 2, 3]
    ```
    """
    # 检查角色是否存在
    role = AdminRoleService.get_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    AdminRBACService.remove_role_permissions(db, role_id, permission_ids)
    
    return Response(
        code=200,
        message="移除权限成功",
        data=None
    )


@router.get("/permissions-detail/{role_id}", response_model=Response[RolePermissionsDetailResponse], summary="获取角色权限详情")
def get_role_permissions_detail(
    role_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取角色的完整权限详情（按分组展示）
    
    返回按 group_key 分组的权限列表，每个分组包含：
    - group_key: 分组标识
    - group_name: 分组名称
    - group_permission: 组权限（如果有）
    - children: 子权限列表
    
    每个权限项包含：
    - id, name, resource_pattern, method
    - effect: allow/deny
    - source: 权限来源信息
    - source_description: 来源描述文本
    - is_inherited: 是否从组权限继承
    - is_overridden: 是否被覆盖
    """
    try:
        result = AdminRBACService.get_role_permissions_detail(db, role_id)
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







