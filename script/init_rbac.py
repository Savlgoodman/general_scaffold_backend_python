"""
RBAC 数据初始化脚本
初始化菜单、权限、角色等数据
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, init_db
from app.models.admin_menu import AdminMenu
from app.models.admin_permission import AdminPermission
from app.models.admin_role import AdminRole
from app.models.admin_role_permission import AdminRolePermission
from app.models.admin_role_menu import AdminRoleMenu
from app.core.logger import app_logger


# ==================== 菜单数据 ====================
MENUS = [
    # 一级菜单：系统管理
    {
        "id": 1,
        "name": "系统管理",
        "path": "/system",
        "parent_id": 0,
        "sort": 1,
        "remark": "系统管理模块",
        "status": 1
    },
    # 二级菜单
    {
        "id": 2,
        "name": "用户管理",
        "path": "/system/users",
        "parent_id": 1,
        "sort": 1,
        "remark": "管理员用户管理",
        "status": 1
    },
    {
        "id": 3,
        "name": "角色管理",
        "path": "/system/roles",
        "parent_id": 1,
        "sort": 2,
        "remark": "角色管理",
        "status": 1
    },
    {
        "id": 4,
        "name": "权限管理",
        "path": "/system/permissions",
        "parent_id": 1,
        "sort": 3,
        "remark": "API权限管理",
        "status": 1
    },
    {
        "id": 5,
        "name": "菜单管理",
        "path": "/system/menus",
        "parent_id": 1,
        "sort": 4,
        "remark": "菜单管理",
        "status": 1
    },
    {
        "id": 6,
        "name": "日志管理",
        "path": "/system/logs",
        "parent_id": 1,
        "sort": 5,
        "remark": "API日志管理",
        "status": 1
    },
]


# ==================== 权限数据 ====================
PERMISSIONS = [
    # ========== 用户管理权限 ==========
    {
        "id": 1,
        "name": "获取当前用户信息",
        "resource_pattern": "/api/admin/admin_users/me",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "获取当前登录用户信息",
        "status": 1
    },
    {
        "id": 2,
        "name": "更新当前用户信息",
        "resource_pattern": "/api/admin/admin_users/me/update",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "更新当前登录用户信息",
        "status": 1
    },
    {
        "id": 3,
        "name": "修改密码",
        "resource_pattern": "/api/admin/admin_users/me/change-password",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "修改当前用户密码",
        "status": 1
    },
    {
        "id": 4,
        "name": "获取用户列表",
        "resource_pattern": "/api/admin/admin_users/list",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "获取管理员用户列表",
        "status": 1
    },
    {
        "id": 5,
        "name": "获取用户详情",
        "resource_pattern": "/api/admin/admin_users/detail/*",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "获取指定用户详情",
        "status": 1
    },
    {
        "id": 6,
        "name": "创建用户",
        "resource_pattern": "/api/admin/admin_users/create",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "创建管理员用户",
        "status": 1
    },
    {
        "id": 7,
        "name": "更新用户",
        "resource_pattern": "/api/admin/admin_users/update/*",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "更新管理员用户信息",
        "status": 1
    },
    {
        "id": 8,
        "name": "删除用户",
        "resource_pattern": "/api/admin/admin_users/delete/*",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "删除管理员用户",
        "status": 1
    },
    {
        "id": 9,
        "name": "为用户分配角色",
        "resource_pattern": "/api/admin/admin_users/assign-roles/*",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "为用户分配角色",
        "status": 1
    },
    {
        "id": 10,
        "name": "获取用户角色",
        "resource_pattern": "/api/admin/admin_users/roles/*",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "获取用户的角色列表",
        "status": 1
    },
    {
        "id": 11,
        "name": "设置用户权限覆盖",
        "resource_pattern": "/api/admin/admin_users/permission-overrides/*",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "批量设置用户权限覆盖（POST）",
        "status": 1
    },
    {
        "id": 12,
        "name": "设置用户菜单覆盖",
        "resource_pattern": "/api/admin/admin_users/menu-overrides/*",
        "method": "POST",
        "group_key": "admin_users",
        "group_name": "用户管理",
        "description": "批量设置用户菜单覆盖（POST）",
        "status": 1
    },

    # ========== 角色管理权限 ==========
    {
        "id": 20,
        "name": "获取角色列表",
        "resource_pattern": "/api/admin/roles/list",
        "method": "POST",
        "group_key": "roles",
        "group_name": "角色管理",
        "description": "获取角色列表",
        "status": 1
    },
    {
        "id": 21,
        "name": "获取角色详情",
        "resource_pattern": "/api/admin/roles/detail/*",
        "method": "POST",
        "group_key": "roles",
        "group_name": "角色管理",
        "description": "获取指定角色详情",
        "status": 1
    },
    {
        "id": 22,
        "name": "创建角色",
        "resource_pattern": "/api/admin/roles/create",
        "method": "POST",
        "group_key": "roles",
        "group_name": "角色管理",
        "description": "创建角色",
        "status": 1
    },
    {
        "id": 23,
        "name": "更新角色",
        "resource_pattern": "/api/admin/roles/update/*",
        "method": "POST",
        "group_key": "roles",
        "group_name": "角色管理",
        "description": "更新角色信息",
        "status": 1
    },
    {
        "id": 24,
        "name": "删除角色",
        "resource_pattern": "/api/admin/roles/delete/*",
        "method": "POST",
        "group_key": "roles",
        "group_name": "角色管理",
        "description": "删除角色",
        "status": 1
    },
    {
        "id": 25,
        "name": "为角色分配权限",
        "resource_pattern": "/api/admin/roles/assign-permissions/*",
        "method": "POST",
        "group_key": "roles",
        "group_name": "角色管理",
        "description": "为角色分配权限",
        "status": 1
    },
    {
        "id": 26,
        "name": "为角色分配菜单",
        "resource_pattern": "/api/admin/roles/assign-menus/*",
        "method": "POST",
        "group_key": "roles",
        "group_name": "角色管理",
        "description": "为角色分配菜单",
        "status": 1
    },
    {
        "id": 27,
        "name": "获取角色权限",
        "resource_pattern": "/api/admin/roles/permissions/*",
        "method": "POST",
        "group_key": "roles",
        "group_name": "角色管理",
        "description": "获取角色的权限列表",
        "status": 1
    },
    {
        "id": 28,
        "name": "获取角色菜单",
        "resource_pattern": "/api/admin/roles/menus/*",
        "method": "POST",
        "group_key": "roles",
        "group_name": "角色管理",
        "description": "获取角色的菜单列表",
        "status": 1
    },

    # ========== 权限管理权限 ==========
    {
        "id": 30,
        "name": "获取权限列表",
        "resource_pattern": "/api/admin/permissions/list",
        "method": "POST",
        "group_key": "permissions",
        "group_name": "权限管理",
        "description": "获取权限列表",
        "status": 1
    },
    {
        "id": 31,
        "name": "获取权限详情",
        "resource_pattern": "/api/admin/permissions/detail/*",
        "method": "POST",
        "group_key": "permissions",
        "group_name": "权限管理",
        "description": "获取指定权限详情",
        "status": 1
    },
    {
        "id": 32,
        "name": "创建权限",
        "resource_pattern": "/api/admin/permissions/create",
        "method": "POST",
        "group_key": "permissions",
        "group_name": "权限管理",
        "description": "创建权限",
        "status": 1
    },
    {
        "id": 33,
        "name": "更新权限",
        "resource_pattern": "/api/admin/permissions/update/*",
        "method": "POST",
        "group_key": "permissions",
        "group_name": "权限管理",
        "description": "更新权限信息",
        "status": 1
    },
    {
        "id": 34,
        "name": "删除权限",
        "resource_pattern": "/api/admin/permissions/delete/*",
        "method": "POST",
        "group_key": "permissions",
        "group_name": "权限管理",
        "description": "删除权限",
        "status": 1
    },

    # ========== 菜单管理权限 ==========
    {
        "id": 40,
        "name": "获取菜单列表",
        "resource_pattern": "/api/admin/menus/list",
        "method": "POST",
        "group_key": "menus",
        "group_name": "菜单管理",
        "description": "获取菜单列表",
        "status": 1
    },
    {
        "id": 41,
        "name": "获取菜单树",
        "resource_pattern": "/api/admin/menus/tree",
        "method": "POST",
        "group_key": "menus",
        "group_name": "菜单管理",
        "description": "获取菜单树形结构",
        "status": 1
    },
    {
        "id": 42,
        "name": "获取菜单详情",
        "resource_pattern": "/api/admin/menus/detail/*",
        "method": "POST",
        "group_key": "menus",
        "group_name": "菜单管理",
        "description": "获取指定菜单详情",
        "status": 1
    },
    {
        "id": 43,
        "name": "创建菜单",
        "resource_pattern": "/api/admin/menus/create",
        "method": "POST",
        "group_key": "menus",
        "group_name": "菜单管理",
        "description": "创建菜单",
        "status": 1
    },
    {
        "id": 44,
        "name": "更新菜单",
        "resource_pattern": "/api/admin/menus/update/*",
        "method": "POST",
        "group_key": "menus",
        "group_name": "菜单管理",
        "description": "更新菜单信息",
        "status": 1
    },
    {
        "id": 45,
        "name": "删除菜单",
        "resource_pattern": "/api/admin/menus/delete/*",
        "method": "POST",
        "group_key": "menus",
        "group_name": "菜单管理",
        "description": "删除菜单",
        "status": 1
    },

    # ========== 日志管理权限 ==========
    {
        "id": 50,
        "name": "获取日志列表",
        "resource_pattern": "/api/admin/logs/list",
        "method": "POST",
        "group_key": "logs",
        "group_name": "日志管理",
        "description": "获取API日志列表",
        "status": 1
    },
    {
        "id": 51,
        "name": "获取日志详情",
        "resource_pattern": "/api/admin/logs/detail/*",
        "method": "POST",
        "group_key": "logs",
        "group_name": "日志管理",
        "description": "获取指定日志详情",
        "status": 1
    },
    {
        "id": 52,
        "name": "获取我的日志",
        "resource_pattern": "/api/admin/logs/my",
        "method": "POST",
        "group_key": "logs",
        "group_name": "日志管理",
        "description": "获取当前用户的API日志",
        "status": 1
    },
    {
        "id": 53,
        "name": "获取日志统计",
        "resource_pattern": "/api/admin/logs/statistics",
        "method": "POST",
        "group_key": "logs",
        "group_name": "日志管理",
        "description": "获取API日志统计信息",
        "status": 1
    },
    {
        "id": 54,
        "name": "清理旧日志",
        "resource_pattern": "/api/admin/logs/cleanup",
        "method": "POST",
        "group_key": "logs",
        "group_name": "日志管理",
        "description": "清理旧日志",
        "status": 1
    },
]


# ==================== 角色数据 ====================
ROLES = [
    {
        "id": 1,
        "name": "普通管理员",
        "remark": "拥有基本的系统管理权限",
        "status": 1
    },
    {
        "id": 2,
        "name": "运维人员",
        "remark": "拥有日志查看和系统监控权限",
        "status": 1
    },
    {
        "id": 3,
        "name": "审计员",
        "remark": "只读权限，用于审计",
        "status": 1
    },
]


# ==================== 角色-权限关联 ====================
# 普通管理员：拥有用户管理、角色查看权限
ROLE_PERMISSIONS = {
    1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 21, 27, 28, 52],  # 普通管理员
    2: [1, 2, 3, 50, 51, 52, 53],  # 运维人员
    3: [1, 4, 5, 20, 21, 30, 31, 40, 41, 42, 50, 51, 52, 53],  # 审计员（只读）
}


# ==================== 角色-菜单关联 ====================
ROLE_MENUS = {
    1: [1, 2, 3],  # 普通管理员：系统管理、用户管理、角色管理
    2: [1, 6],  # 运维人员：系统管理、日志管理
    3: [1, 2, 3, 4, 5, 6],  # 审计员：所有菜单（只读）
}


def init_menus(db):
    """初始化菜单数据"""
    app_logger.info("开始初始化菜单数据...")
    
    for menu_data in MENUS:
        existing = db.query(AdminMenu).filter(AdminMenu.id == menu_data["id"]).first()
        if existing:
            app_logger.info(f"菜单已存在，跳过: {menu_data['name']}")
            continue
        
        menu = AdminMenu(**menu_data)
        db.add(menu)
        app_logger.info(f"创建菜单: {menu_data['name']}")
    
    db.commit()
    app_logger.info(f"菜单初始化完成，共 {len(MENUS)} 条")


def init_permissions(db):
    """初始化权限数据"""
    app_logger.info("开始初始化权限数据...")
    
    for perm_data in PERMISSIONS:
        existing = db.query(AdminPermission).filter(AdminPermission.id == perm_data["id"]).first()
        if existing:
            app_logger.info(f"权限已存在，跳过: {perm_data['name']}")
            continue
        
        permission = AdminPermission(**perm_data)
        db.add(permission)
        app_logger.info(f"创建权限: {perm_data['name']}")
    
    db.commit()
    app_logger.info(f"权限初始化完成，共 {len(PERMISSIONS)} 条")


def init_roles(db):
    """初始化角色数据"""
    app_logger.info("开始初始化角色数据...")
    
    for role_data in ROLES:
        existing = db.query(AdminRole).filter(AdminRole.id == role_data["id"]).first()
        if existing:
            app_logger.info(f"角色已存在，跳过: {role_data['name']}")
            continue
        
        role = AdminRole(**role_data)
        db.add(role)
        app_logger.info(f"创建角色: {role_data['name']}")
    
    db.commit()
    app_logger.info(f"角色初始化完成，共 {len(ROLES)} 条")


def init_role_permissions(db):
    """初始化角色-权限关联"""
    app_logger.info("开始初始化角色-权限关联...")
    
    for role_id, permission_ids in ROLE_PERMISSIONS.items():
        for perm_id in permission_ids:
            existing = db.query(AdminRolePermission).filter(
                AdminRolePermission.role_id == role_id,
                AdminRolePermission.permission_id == perm_id
            ).first()
            
            if existing:
                continue
            
            role_perm = AdminRolePermission(role_id=role_id, permission_id=perm_id)
            db.add(role_perm)
    
    db.commit()
    app_logger.info("角色-权限关联初始化完成")


def init_role_menus(db):
    """初始化角色-菜单关联"""
    app_logger.info("开始初始化角色-菜单关联...")
    
    for role_id, menu_ids in ROLE_MENUS.items():
        for menu_id in menu_ids:
            existing = db.query(AdminRoleMenu).filter(
                AdminRoleMenu.role_id == role_id,
                AdminRoleMenu.menu_id == menu_id
            ).first()
            
            if existing:
                continue
            
            role_menu = AdminRoleMenu(role_id=role_id, menu_id=menu_id)
            db.add(role_menu)
    
    db.commit()
    app_logger.info("角色-菜单关联初始化完成")


def init_rbac():
    """
    初始化 RBAC 数据
    """
    # 初始化数据库表
    init_db()
    
    db = SessionLocal()
    
    try:
        # 按顺序初始化数据
        init_menus(db)
        init_permissions(db)
        init_roles(db)
        init_role_permissions(db)
        init_role_menus(db)
        
        app_logger.info("=" * 50)
        app_logger.info("RBAC 数据初始化完成！")
        app_logger.info("=" * 50)
        app_logger.info("已创建菜单:")
        app_logger.info("  - 系统管理（一级菜单）")
        app_logger.info("    - 用户管理")
        app_logger.info("    - 角色管理")
        app_logger.info("    - 权限管理")
        app_logger.info("    - 菜单管理")
        app_logger.info("    - 日志管理")
        app_logger.info("-" * 50)
        app_logger.info("已创建角色:")
        app_logger.info("  - 普通管理员（用户管理、角色查看）")
        app_logger.info("  - 运维人员（日志管理）")
        app_logger.info("  - 审计员（只读权限）")
        app_logger.info("-" * 50)
        app_logger.info(f"已创建权限: {len(PERMISSIONS)} 条")
        app_logger.info("=" * 50)
        
    except Exception as e:
        db.rollback()
        app_logger.error(f"RBAC 数据初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_rbac()

