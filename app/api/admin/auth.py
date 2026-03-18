"""
认证相关API
包括登录、注册、刷新token等
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.logger import app_logger
from app.schemas.admin_user import AdminUserLogin, TokenResponse, AdminUserCreate, AdminUserResponse
from app.schemas.admin_auth import LoginResponse
from app.schemas.captcha import CaptchaResponse, LoginWithCaptcha
from app.schemas.common import Response
from app.services.admin_user_service import AdminUserService
from app.services.admin_rbac_service import AdminRBACService
from app.services.admin_menu_service import AdminMenuService
from app.services.captcha_service import CaptchaService
from app.services.admin_login_log_service import AdminLoginLogService
from app.schemas.admin_login_log import AdminLoginLogCreate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/captcha", response_model=Response[CaptchaResponse], summary="获取验证码")
def get_captcha():
    """
    获取验证码
    
    返回验证码的唯一标识和Base64编码的图片数据
    """
    try:
        captcha_key, captcha_image = CaptchaService.generate_captcha()
        
        return Response(
            code=200,
            message="获取验证码成功",
            data=CaptchaResponse(
                captcha_key=captcha_key,
                captcha_image=captcha_image
            )
        )
    except Exception as e:
        app_logger.error(f"获取验证码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取验证码失败"
        )


@router.post("/login", response_model=Response[LoginResponse], summary="管理员用户登录")
def login(
    user_in: LoginWithCaptcha,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    管理员用户登录（带验证码验证）

    - **username**: 用户名
    - **password**: 密码
    - **captcha_key**: 验证码键
    - **captcha_code**: 验证码

    返回数据包含：
    - access_token: 访问令牌
    - refresh_token: 刷新令牌
    - menus: 用户菜单权限树（超级管理员返回所有激活菜单）
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "")

    # 1. 验证验证码
    if not CaptchaService.verify_captcha(user_in.captcha_key, user_in.captcha_code):
        # 记录登录失败日志
        AdminLoginLogService.create(db, AdminLoginLogCreate(
            username=user_in.username, success=False,
            failure_reason="验证码错误或已过期",
            ip_address=ip_address, user_agent=user_agent,
        ))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期",
        )

    # 2. 验证���理员用户
    user = AdminUserService.authenticate(db, user_in.username, user_in.password)

    if not user:
        # 记录登录失败日志
        AdminLoginLogService.create(db, AdminLoginLogCreate(
            username=user_in.username, success=False,
            failure_reason="用户名或密码错误",
            ip_address=ip_address, user_agent=user_agent,
        ))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 记录登录成功日志
    AdminLoginLogService.create(db, AdminLoginLogCreate(
        user_id=user.id, username=user.username, success=True,
        ip_address=ip_address, user_agent=user_agent,
    ))

    # 生成token
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "is_superuser": user.is_superuser,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # 获取用户菜单权限
    if user.is_superuser:
        # 超级管理员获取所有激活的菜单
        menus = AdminMenuService.get_menu_tree(db, status=1)
    else:
        # 普通用户获取角色对应的菜单
        menus = AdminRBACService.get_user_menus(db, user.id)

    return Response(
        code=200,
        message="登录成功",
        data=LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_id=user.id,
            username=user.username,
            is_superuser=user.is_superuser,
            menus=menus
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
