"""
API v1 路由
"""
from fastapi import APIRouter
from app.api.v1 import auth, users, api_logs

router = APIRouter(prefix="/v1")

# 注册子路由
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(api_logs.router)


