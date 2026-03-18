"""
FastAPI应用创建和配置
"""
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.core.redis import init_redis, close_redis
from app.core.logger import app_logger
from app.middleware.auth import AuthMiddleware
from app.middleware.api_logger import APILoggerMiddleware
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    app_logger.info(f"应用启动 - 环境: {settings.environment}")
    
    # 初始化数据库
    try:
        init_db()
        app_logger.info("数据库初始化成功")
    except Exception as e:
        app_logger.error(f"数据库初始化失败: {e}")
    
    # 初始化Redis
    try:
        init_redis()
        app_logger.info("Redis连接成功")
    except Exception as e:
        app_logger.error(f"Redis连接失败: {e}")
    
    yield
    
    # 关闭时执行
    app_logger.info("应用关闭")
    close_redis()


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    """
    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        debug=False,  # 始终关闭 debug，防止 ServerErrorMiddleware 泄露堆栈
        lifespan=lifespan,
        docs_url="/docs" if settings.app.debug else None,
        redoc_url="/redoc" if settings.app.debug else None,
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )
    
    # 添加API日志中间件
    if settings.api_log.enabled:
        app.add_middleware(APILoggerMiddleware)
    
    # 添加认证中间件
    app.add_middleware(AuthMiddleware)
    
    # 注册路由
    app.include_router(api_router, prefix="/api")

    # ==================== 全局异常处理 ====================

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """处理HTTP异常，返回统一格式"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail if isinstance(exc.detail, str) else "请求错误",
                "data": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """处理请求参数校验异常"""
        return JSONResponse(
            status_code= 422,
            content={
                "code": 422,
                "message": "请求参数校验失败",
                "data": exc.errors() if settings.app.debug else None,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """捕获所有未处理异常，防止堆栈信息泄露到前端，同时将异常写入 app_error_logs 表"""
        tb_str = traceback.format_exc()
        app_logger.error(
            f"未处理异常 [{request.method}] {request.url.path}: "
            f"{type(exc).__name__}: {exc}\n{tb_str}"
        )

        # 将带请求上下文的异常写入异常日志表
        try:
            from app.core.database import SessionLocal
            from app.models.app_error_log import AppErrorLog

            user_id = getattr(request.state, "user_id", None)
            username = getattr(request.state, "username", None)

            db = SessionLocal()
            try:
                log_entry = AppErrorLog(
                    level="ERROR",
                    message=f"{type(exc).__name__}: {exc}",
                    traceback=tb_str,
                    request_method=request.method,
                    request_path=str(request.url.path),
                    user_id=user_id,
                    username=username,
                    ip_address=request.client.host if request.client else None,
                )
                db.add(log_entry)
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
        except Exception:
            pass

        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "服务器内部错误" if not settings.app.debug else str(exc),
                "data": None,
            },
        )

    return app


