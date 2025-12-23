"""
API路由模块
"""
from fastapi import APIRouter
from app.api.v1 import router as v1_router

# 创建主路由
api_router = APIRouter()

# 注册版本路由
api_router.include_router(v1_router)


