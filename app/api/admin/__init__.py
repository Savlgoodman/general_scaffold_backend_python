"""
API v1 路由
"""
from fastapi import APIRouter
from app.api.admin import auth, admin_users, api_logs, roles, permissions, menus

router = APIRouter(prefix="/admin")

# 注册子路由
router.include_router(auth.router)
router.include_router(admin_users.router)
router.include_router(api_logs.router)
router.include_router(roles.router)
router.include_router(permissions.router)
router.include_router(menus.router)


