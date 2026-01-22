"""
管理员菜单管理API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.admin_menu import (
    AdminMenuCreate, AdminMenuUpdate, AdminMenuResponse, AdminMenuTreeNode
)
from app.schemas.common import Response, PageResponse
from app.services.admin_menu_service import AdminMenuService
from app.utils.dependencies import get_current_admin_user
from app.utils.query_params import clean_query_params

router = APIRouter(prefix="/menus", tags=["menus"])


@router.get("/list", response_model=Response[PageResponse[AdminMenuResponse]], summary="获取菜单列表")
def get_menus(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态"),
    parent_id: Optional[str] = Query(None, description="父菜单ID"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取菜单列表（需要超级管理员权限）
    
    必传参数：
    - page: 页码
    - page_size: 每页数量
    
    可选查询条件：
    - keyword: 搜索关键词（菜单名称、路径）
    - status: 状态（1=启用，0=禁用）
    - parent_id: 父菜单ID
    """
    params = clean_query_params(
        keyword=keyword,
        status=(status, int),
        parent_id=(parent_id, int)
    )
    
    skip = (page - 1) * page_size
    menus, total = AdminMenuService.get_list(
        db, skip, page_size, params['keyword'], params['status'], params['parent_id']
    )
    
    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AdminMenuResponse.model_validate(menu) for menu in menus]
        )
    )


@router.get("/tree", response_model=Response[list[AdminMenuTreeNode]], summary="获取菜单树")
def get_menu_tree(
    status: Optional[str] = Query(None, description="状态"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取菜单树（需要超级管理员权限）
    
    可选查询条件：
    - status: 状态（1=启用，0=禁用）
    """
    params = clean_query_params(status=(status, int))
    
    tree = AdminMenuService.get_menu_tree(db, params['status'])
    
    return Response(
        code=200,
        message="获取成功",
        data=tree
    )


@router.get("/detail/{menu_id}", response_model=Response[AdminMenuResponse], summary="获取菜单详情")
def get_menu(
    menu_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    获取指定菜单详情（需要超级管理员权限）
    """
    menu = AdminMenuService.get_by_id(db, menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="菜单不存在"
        )
    
    return Response(
        code=200,
        message="获取成功",
        data=AdminMenuResponse.model_validate(menu)
    )


@router.post("/create", response_model=Response[AdminMenuResponse], summary="创建菜单")
def create_menu(
    menu_in: AdminMenuCreate,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    创建菜单（需要超级管理员权限）
    """
    try:
        menu = AdminMenuService.create(db, menu_in)
        return Response(
            code=200,
            message="创建成功",
            data=AdminMenuResponse.model_validate(menu)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/update/{menu_id}", response_model=Response[AdminMenuResponse], summary="更新菜单")
def update_menu(
    menu_id: int,
    menu_in: AdminMenuUpdate,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    更新菜单信息（需要超级管理员权限）
    """
    try:
        menu = AdminMenuService.update(db, menu_id, menu_in)
        if not menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="菜单不存在"
            )
        return Response(
            code=200,
            message="更新成功",
            data=AdminMenuResponse.model_validate(menu)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/delete/{menu_id}", response_model=Response, summary="删除菜单")
def delete_menu(
    menu_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    删除菜单（需要超级管理员权限）
    """
    try:
        success = AdminMenuService.delete(db, menu_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="菜单不存在"
            )
        
        return Response(
            code=200,
            message="删除成功",
            data=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )







