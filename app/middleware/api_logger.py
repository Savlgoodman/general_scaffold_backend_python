"""
API日志中间件
记录所有API请求和响应信息
"""
import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from app.core.config import settings
from app.core.logger import app_logger
from app.core.database import SessionLocal
from app.models.api_log import APILog


class APILoggerMiddleware(BaseHTTPMiddleware):
    """
    API日志中间件
    记录API调用信息到数据库
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录日志
        """
        # 检查是否需要记录日志
        if not self._should_log(request.url.path):
            return await call_next(request)
        
        # 记录开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        
        # 获取请求体
        request_body = None
        if settings.api_log.log_request_body and method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_body = body.decode("utf-8")
                    # 限制长度
                    if len(request_body) > settings.api_log.max_body_length:
                        request_body = request_body[:settings.api_log.max_body_length] + "..."
            except Exception as e:
                app_logger.warning(f"读取请求体失败: {e}")
        
        # 获取用户信息
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)
        
        # 获取客户端信息
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # 处理请求
        response = await call_next(request)
        
        # 计算响应时长
        duration = time.time() - start_time
        
        # 获取响应信息
        status_code = response.status_code
        response_body = None
        
        # 记录响应体（仅对JSON响应）
        if settings.api_log.log_response_body:
            # 注意：这里只能记录简单的响应，对于StreamingResponse需要特殊处理
            # 为了简化，这里不记录响应体，可以根据需要扩展
            pass
        
        # 异步保存日志到数据库
        try:
            self._save_log(
                method=method,
                path=path,
                query_params=query_params,
                request_body=request_body,
                status_code=status_code,
                response_body=response_body,
                duration=duration,
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as e:
            app_logger.error(f"保存API日志失败: {e}")
        
        # 控制台日志
        app_logger.info(
            f"{method} {path} - {status_code} - {duration:.3f}s - "
            f"User: {username or 'Anonymous'} - IP: {ip_address}"
        )
        
        return response
    
    def _should_log(self, path: str) -> bool:
        """
        判断是否需要记录日志
        """
        for exclude_path in settings.api_log.exclude_paths:
            if path.startswith(exclude_path):
                return False
        return True
    
    def _save_log(
        self,
        method: str,
        path: str,
        query_params: str,
        request_body: str,
        status_code: int,
        response_body: str,
        duration: float,
        user_id: int,
        username: str,
        ip_address: str,
        user_agent: str,
    ):
        """
        保存日志到数据库
        """
        db = SessionLocal()
        try:
            log = APILog(
                method=method,
                path=path,
                query_params=query_params,
                request_body=request_body,
                status_code=status_code,
                response_body=response_body,
                duration=duration,
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            app_logger.error(f"保存API日志到数据库失败: {e}")
        finally:
            db.close()


