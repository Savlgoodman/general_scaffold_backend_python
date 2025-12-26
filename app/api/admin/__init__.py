"""
API v1 路由
"""
from fastapi import APIRouter
from app.api.admin import auth, admin_users, api_logs

router = APIRouter(prefix="/admin")

# 注册子路由
router.include_router(auth.router)
router.include_router(admin_users.router)
router.include_router(api_logs.router)


