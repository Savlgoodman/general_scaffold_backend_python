"""
API v1 路由
"""
from fastapi import APIRouter
from app.api.admin import auth, admin_users, api_logs, roles, permissions, menus, system_info, error_logs, login_logs, operation_logs, notices

router = APIRouter(prefix="/admin")

# 注册子路由
router.include_router(auth.router)
router.include_router(admin_users.router)
router.include_router(api_logs.router)
router.include_router(roles.router)
router.include_router(permissions.router)
router.include_router(menus.router)
router.include_router(system_info.router)
router.include_router(error_logs.router)
router.include_router(login_logs.router)
router.include_router(operation_logs.router)
router.include_router(notices.router)


