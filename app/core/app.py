"""
FastAPI应用创建和配置
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
        debug=settings.app.debug,
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
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "environment": settings.environment}
    
    return app


