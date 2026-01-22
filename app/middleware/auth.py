"""
认证中间件
处理JWT token验证和用户身份识别，以及API权限验证
"""
import time
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.security import decode_token
from app.core.logger import app_logger


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件
    验证JWT token并将用户信息注入到request.state
    同时验证用户是否有访问该API的权限
    """
    
    # 不需要认证的路径
    EXCLUDE_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/admin/auth/login",
        "/api/admin/auth/register",
    ]
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        """
        # 检查是否需要认证
        if self._should_skip_auth(request.url.path):
            return await call_next(request)
        
        # 获取token
        token = self._get_token_from_header(request)
        
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"code": 401, "message": "未提供认证令牌", "data": None}
            )
        
        # 验证token
        payload = decode_token(token)
        
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"code": 401, "message": "无效的认证令牌", "data": None}
            )
        
        # 检查token类型
        if payload.get("type") != "access":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"code": 401, "message": "令牌类型错误", "data": None}
            )
        
        # 将用户信息注入到request.state
        user_id = payload.get("user_id")
        username = payload.get("username")
        is_superuser = payload.get("is_superuser", False)
        
        request.state.user_id = user_id
        request.state.username = username
        request.state.is_superuser = is_superuser
        
        # 超级管理员跳过权限验证
        if not is_superuser:
            # 验证API权限
            has_permission = await self._check_api_permission(request, user_id)
            
            if not has_permission:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"code": 403, "message": "无权访问该接口", "data": None}
                )
        
        # 继续处理请求
        response = await call_next(request)
        
        return response
    
    def _should_skip_auth(self, path: str) -> bool:
        """
        判断是否跳过认证
        """
        for exclude_path in self.EXCLUDE_PATHS:
            if path.startswith(exclude_path):
                return True
        return False
    
    def _get_token_from_header(self, request: Request) -> Optional[str]:
        """
        从请求头获取token
        """
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            return None
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
            return token
        except ValueError:
            return None
    
    async def _check_api_permission(self, request: Request, user_id: int) -> bool:
        """
        检查用户是否有访问该API的权限
        支持通配符匹配，如 /api/admin/users/detail/* 可以匹配 /api/admin/users/detail/123
        """
        from app.core.database import SessionLocal
        from app.services.admin_rbac_service import AdminRBACService
        import fnmatch
        
        # 获取请求路径
        api_path = request.url.path
        app_logger.info("权限中间件：api路径为：" + api_path)
        
        # 创建数据库会话
        db = SessionLocal()
        try:
            # 获取用户的所有权限
            user_permissions = AdminRBACService.get_user_permissions(db, user_id)
            
            # 检查是否有该API的权限（支持通配符匹配）
            for permission_path in user_permissions:
                # 精确匹配
                if api_path == permission_path:
                    return True
                # 通配符匹配（将 * 转换为 fnmatch 格式）
                if '*' in permission_path:
                    # 将权限路径中的 * 转换为 fnmatch 的通配符格式
                    pattern = permission_path.replace('*', '*')
                    if fnmatch.fnmatch(api_path, pattern):
                        return True
            
            return False
        except Exception as e:
            app_logger.error(f"检查API权限时出错: {str(e)}")
            return False
        finally:
            db.close()


