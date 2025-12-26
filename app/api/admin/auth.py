"""
认证相关API
包括登录、注册、刷新token等
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.schemas.admin_user import AdminUserLogin, TokenResponse, AdminUserCreate, AdminUserResponse
from app.schemas.common import Response
from app.services.admin_user_service import AdminUserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Response[TokenResponse], summary="管理员用户登录")
def login(
    user_in: AdminUserLogin,
    db: Session = Depends(get_db)
):
    """
    管理员用户登录
    
    - **username**: 用户名
    - **password**: 密码
    """
    # 验证管理员用户
    user = AdminUserService.authenticate(db, user_in.username, user_in.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    
    # 生成token
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "is_superuser": user.is_superuser,
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return Response(
        code=200,
        message="登录成功",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    )


@router.post("/register", response_model=Response[AdminUserResponse], summary="管理员用户注册")
def register(
    user_in: AdminUserCreate,
    db: Session = Depends(get_db)
):
    """
    管理员用户注册
    
    - **username**: 用户名
    - **email**: 邮箱
    - **password**: 密码
    """
    try:
        # 注册时不允许设置为超级管理员
        user_in.is_superuser = False
        
        user = AdminUserService.create(db, user_in)
        
        return Response(
            code=200,
            message="注册成功",
            data=AdminUserResponse.model_validate(user)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/refresh", response_model=Response[TokenResponse], summary="刷新Token")
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    使用refresh token刷新access token
    
    - **refresh_token**: 刷新令牌
    """
    # 解码refresh token
    payload = decode_token(refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
        )
    
    # 验证管理员用户是否存在
    user_id = payload.get("user_id")
    user = AdminUserService.get_by_id(db, user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    
    # 生成新的token
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "is_superuser": user.is_superuser,
    }
    
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return Response(
        code=200,
        message="刷新成功",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )
    )


