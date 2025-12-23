"""
认证中间件
处理JWT token验证和用户身份识别
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
        request.state.user_id = payload.get("user_id")
        request.state.username = payload.get("username")
        request.state.is_superuser = payload.get("is_superuser", False)
        
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


