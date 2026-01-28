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
        "/api/admin/auth/captcha",
        "/api/admin/system_info/config"
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
        
        # 检查用户是否被禁用
        from app.core.database import SessionLocal
        from app.services.admin_user_service import AdminUserService
        
        db = SessionLocal()
        try:
            user = AdminUserService.get_by_id(db, user_id)
            if user and not user.is_active:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"code": 401, "message": "账户已被禁用", "data": None}
                )
        finally:
            db.close()
        
        # 超级管理员跳过权限验证
        if not is_superuser:
            # 验证API权限
            permission_result = await self._check_api_permission(request, user_id)
            
            if not permission_result.allowed:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "code": 403, 
                        "message": "无权访问该接口", 
                        "data": {
                            "path": request.url.path,
                            "method": request.method,
                            "deny_reason": permission_result.deny_reason
                        }
                    }
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
    
    async def _check_api_permission(self, request: Request, user_id: int):
        """
        检查用户是否有访问该API的权限
        支持通配符匹配和优先级机制
        
        权限检查流程：
        1. 获取用户所有角色的权限（包括effect和priority）
        2. 匹配请求路径（支持通配符）
        3. 按优先级排序
        4. 应用最高优先级规则
        5. 默认拒绝（无匹配规则时）
        
        Returns:
            PermissionCheckResult 包含详细的权限检查结果
        """
        from app.core.database import SessionLocal
        from app.services.admin_rbac_service import AdminRBACService
        from app.schemas.admin_permission import PermissionCheckResult, PermissionSource, SourceType
        
        # 获取请求路径和方法
        api_path = request.url.path
        method = request.method
        
        app_logger.info(f"权限中间件：检查 [{method}] {api_path}")
        
        # 创建数据库会话
        db = SessionLocal()
        try:
            # 使用新的权限检查方法（返回详细结果）
            result = AdminRBACService.check_permission_detail(db, user_id, api_path, method)
            
            if result.allowed:
                app_logger.info(f"权限中间件：用户 {user_id} 有权限访问 [{method}] {api_path}")
            else:
                app_logger.warning(f"权限中间件：用户 {user_id} 无权限访问 [{method}] {api_path}，原因：{result.deny_reason}")
            
            return result
        except Exception as e:
            app_logger.error(f"检查API权限时出错: {str(e)}")
            # 返回默认拒绝结果
            source = PermissionSource(type=SourceType.NO_PERMISSION)
            return PermissionCheckResult(
                allowed=False,
                effect="deny",
                source=source,
                deny_reason=f"权限检查出错: {str(e)}"
            )
        finally:
            db.close()


