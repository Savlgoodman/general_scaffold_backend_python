"""
用户管理API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserPasswordChange, CurrentUser
)
from app.schemas.common import Response, PageResponse
from app.services.user_service import UserService
from app.utils.dependencies import get_current_user, get_current_superuser

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=Response[CurrentUser], summary="获取当前用户信息")
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的信息
    """
    return Response(
        code=200,
        message="获取成功",
        data=CurrentUser.model_validate(current_user)
    )


@router.put("/me", response_model=Response[UserResponse], summary="更新当前用户信息")
def update_current_user_info(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前登录用户的信息
    """
    try:
        user = UserService.update(db, current_user.id, user_in)
        return Response(
            code=200,
            message="更新成功",
            data=UserResponse.model_validate(user)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/me/change-password", response_model=Response, summary="修改密码")
def change_password(
    password_in: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改当前用户密码
    """
    try:
        UserService.change_password(
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


@router.get("", response_model=Response[PageResponse[UserResponse]], summary="获取用户列表")
def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    获取用户列表（需要管理员权限）
    
    必传参数：
    - page: 页码
    - page_size: 每页数量
    
    可选查询条件：
    - keyword: 搜索关键词（用户名、邮箱、全名）
    - is_active: 是否激活
    """
    skip = (page - 1) * page_size
    users, total = UserService.get_list(db, skip, page_size, keyword, is_active)
    
    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[UserResponse.model_validate(user) for user in users]
        )
    )


@router.get("/{user_id}", response_model=Response[UserResponse], summary="获取用户详情")
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    获取指定用户详情（需要管理员权限）
    """
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return Response(
        code=200,
        message="获取成功",
        data=UserResponse.model_validate(user)
    )


@router.post("", response_model=Response[UserResponse], summary="创建用户")
def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    创建用户（需要管理员权限）
    """
    try:
        user = UserService.create(db, user_in)
        return Response(
            code=200,
            message="创建成功",
            data=UserResponse.model_validate(user)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{user_id}", response_model=Response[UserResponse], summary="更新用户")
def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    更新用户信息（需要管理员权限）
    """
    try:
        user = UserService.update(db, user_id, user_in)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return Response(
            code=200,
            message="更新成功",
            data=UserResponse.model_validate(user)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}", response_model=Response, summary="删除用户")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    删除用户（需要管理员权限）
    """
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    success = UserService.delete(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return Response(
        code=200,
        message="删除成功",
        data=None
    )


