"""
管理员RBAC权限服务层
处理用户权限验证相关的业务逻辑
"""
from typing import List, Set, Optional
from sqlalchemy.orm import Session

from app.models.admin_user_role import AdminUserRole
from app.models.admin_role_permission import AdminRolePermission
from app.models.admin_role_menu import AdminRoleMenu
from app.models.admin_user_permission_override import AdminUserPermissionOverride, EffectType
from app.models.admin_user_menu_override import AdminUserMenuOverride, MenuEffectType
from app.models.admin_permission import AdminPermission
from app.models.admin_menu import AdminMenu
from app.schemas.admin_menu import AdminMenuTreeNode
from app.services.admin_menu_service import AdminMenuService
from app.core.logger import app_logger


class AdminRBACService:
    """管理员RBAC权限服务"""
    
    @staticmethod
    def get_user_roles(db: Session, admin_user_id: int) -> List[int]:
        """获取用户的角色ID列表"""
        user_roles = db.query(AdminUserRole).filter(
            AdminUserRole.admin_user_id == admin_user_id,
            AdminUserRole.is_deleted == False
        ).all()
        
        return [ur.role_id for ur in user_roles]
    
    @staticmethod
    def assign_user_roles(db: Session, admin_user_id: int, role_ids: List[int]) -> bool:
        """为用户分配角色"""
        from datetime import datetime, timezone
        
        # 删除旧的角色关联
        db.query(AdminUserRole).filter(
            AdminUserRole.admin_user_id == admin_user_id,
            AdminUserRole.is_deleted == False
        ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)})
        
        # 创建新的角色关联
        for role_id in role_ids:
            user_role = AdminUserRole(
                admin_user_id=admin_user_id,
                role_id=role_id
            )
            db.add(user_role)
        
        db.commit()
        
        app_logger.info(f"为用户 {admin_user_id} 分配角色成功")
        
        return True
    
    @staticmethod
    def get_user_permissions(db: Session, admin_user_id: int) -> Set[str]:
        """
        获取用户的所有权限（API路径集合）
        逻辑：
        1. 获取用户所有角色的权限（取并集）
        2. 应用用户权限覆盖表（ALLOW添加，DENY删除）
        """
        # 1. 获取用户的角色
        role_ids = AdminRBACService.get_user_roles(db, admin_user_id)
        
        if not role_ids:
            permission_ids = set()
        else:
            # 2. 获取角色的权限（取并集）
            role_permissions = db.query(AdminRolePermission).filter(
                AdminRolePermission.role_id.in_(role_ids),
                AdminRolePermission.is_deleted == False
            ).all()
            
            permission_ids = set([rp.permission_id for rp in role_permissions])
        
        # 3. 应用用户权限覆盖
        overrides = db.query(AdminUserPermissionOverride).filter(
            AdminUserPermissionOverride.admin_user_id == admin_user_id,
            AdminUserPermissionOverride.is_deleted == False
        ).all()
        
        for override in overrides:
            if override.effect == EffectType.ALLOW:
                permission_ids.add(override.permission_id)
            elif override.effect == EffectType.DENY:
                permission_ids.discard(override.permission_id)
        
        # 4. 获取权限对应的API路径（只获取激活的权限）
        if not permission_ids:
            return set()
        
        permissions = db.query(AdminPermission).filter(
            AdminPermission.id.in_(permission_ids),
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all()
        
        return set([p.api_path for p in permissions])
    
    @staticmethod
    def get_user_menus(db: Session, admin_user_id: int) -> List[AdminMenuTreeNode]:
        """
        获取用户的所有菜单（树形结构）
        逻辑：
        1. 获取用户所有角色的菜单（取并集）
        2. 应用用户菜单覆盖表（ALLOW添加，DENY删除）
        3. 只返回激活的菜单
        4. 构建树形结构
        """
        # 1. 获取用户的角色
        role_ids = AdminRBACService.get_user_roles(db, admin_user_id)
        
        if not role_ids:
            menu_ids = set()
        else:
            # 2. 获取角色的菜单（取并集）
            role_menus = db.query(AdminRoleMenu).filter(
                AdminRoleMenu.role_id.in_(role_ids),
                AdminRoleMenu.is_deleted == False
            ).all()
            
            menu_ids = set([rm.menu_id for rm in role_menus])
        
        # 3. 应用用户菜单覆盖
        overrides = db.query(AdminUserMenuOverride).filter(
            AdminUserMenuOverride.admin_user_id == admin_user_id,
            AdminUserMenuOverride.is_deleted == False
        ).all()
        
        for override in overrides:
            if override.effect == MenuEffectType.ALLOW:
                menu_ids.add(override.menu_id)
            elif override.effect == MenuEffectType.DENY:
                menu_ids.discard(override.menu_id)
        
        # 4. 获取菜单（只获取激活的菜单）
        if not menu_ids:
            return []
        
        menus = db.query(AdminMenu).filter(
            AdminMenu.id.in_(menu_ids),
            AdminMenu.is_deleted == False,
            AdminMenu.status == 1
        ).order_by(AdminMenu.sort.asc()).all()
        
        # 5. 构建树形结构
        return AdminMenuService.build_menu_tree(menus)
    
    @staticmethod
    def check_user_permission(db: Session, admin_user_id: int, api_path: str) -> bool:
        """检查用户是否有某个API的权限"""
        permissions = AdminRBACService.get_user_permissions(db, admin_user_id)
        return api_path in permissions
    
    @staticmethod
    def set_user_permission_overrides(
        db: Session,
        admin_user_id: int,
        permission_id: int,
        effect: EffectType
    ) -> bool:
        """设置用户权限覆盖"""
        from datetime import datetime, timezone
        
        # 检查是否已存在
        existing = db.query(AdminUserPermissionOverride).filter(
            AdminUserPermissionOverride.admin_user_id == admin_user_id,
            AdminUserPermissionOverride.permission_id == permission_id,
            AdminUserPermissionOverride.is_deleted == False
        ).first()
        
        if existing:
            # 更新
            existing.effect = effect
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # 创建
            override = AdminUserPermissionOverride(
                admin_user_id=admin_user_id,
                permission_id=permission_id,
                effect=effect
            )
            db.add(override)
        
        db.commit()
        
        app_logger.info(f"设置用户 {admin_user_id} 权限覆盖成功")
        
        return True
    
    @staticmethod
    def set_user_menu_overrides(
        db: Session,
        admin_user_id: int,
        menu_id: int,
        effect: MenuEffectType
    ) -> bool:
        """设置用户菜单覆盖"""
        from datetime import datetime, timezone
        
        # 检查是否已存在
        existing = db.query(AdminUserMenuOverride).filter(
            AdminUserMenuOverride.admin_user_id == admin_user_id,
            AdminUserMenuOverride.menu_id == menu_id,
            AdminUserMenuOverride.is_deleted == False
        ).first()
        
        if existing:
            # 更新
            existing.effect = effect
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # 创建
            override = AdminUserMenuOverride(
                admin_user_id=admin_user_id,
                menu_id=menu_id,
                effect=effect
            )
            db.add(override)
        
        db.commit()
        
        app_logger.info(f"设置用户 {admin_user_id} 菜单覆盖成功")
        
        return True
    
    @staticmethod
    def get_user_permission_overrides(db: Session, admin_user_id: int) -> List[AdminUserPermissionOverride]:
        """获取用户的权限覆盖列表"""
        return db.query(AdminUserPermissionOverride).filter(
            AdminUserPermissionOverride.admin_user_id == admin_user_id,
            AdminUserPermissionOverride.is_deleted == False
        ).all()
    
    @staticmethod
    def get_user_menu_overrides(db: Session, admin_user_id: int) -> List[AdminUserMenuOverride]:
        """获取用户的菜单覆盖列表"""
        return db.query(AdminUserMenuOverride).filter(
            AdminUserMenuOverride.admin_user_id == admin_user_id,
            AdminUserMenuOverride.is_deleted == False
        ).all()
    
    @staticmethod
    def delete_user_permission_override(db: Session, override_id: int) -> bool:
        """删除用户权限覆盖"""
        from datetime import datetime, timezone
        
        override = db.query(AdminUserPermissionOverride).filter(
            AdminUserPermissionOverride.id == override_id,
            AdminUserPermissionOverride.is_deleted == False
        ).first()
        
        if not override:
            return False
        
        override.is_deleted = True
        override.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return True
    
    @staticmethod
    def delete_user_menu_override(db: Session, override_id: int) -> bool:
        """删除用户菜单覆盖"""
        from datetime import datetime, timezone
        
        override = db.query(AdminUserMenuOverride).filter(
            AdminUserMenuOverride.id == override_id,
            AdminUserMenuOverride.is_deleted == False
        ).first()
        
        if not override:
            return False
        
        override.is_deleted = True
        override.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return True
    
    @staticmethod
    def clear_all_permission_overrides(db: Session, admin_user_id: int) -> bool:
        """清除用户的所有权限覆盖"""
        from datetime import datetime, timezone
        
        # 软删除所有该用户的权限覆盖记录
        result = db.query(AdminUserPermissionOverride).filter(
            AdminUserPermissionOverride.admin_user_id == admin_user_id,
            AdminUserPermissionOverride.is_deleted == False
        ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)})
        
        db.commit()
        
        app_logger.info(f"清除用户 {admin_user_id} 的所有权限覆盖成功，共清除 {result} 条记录")
        
        return True
    
    @staticmethod
    def clear_all_menu_overrides(db: Session, admin_user_id: int) -> bool:
        """清除用户的所有菜单覆盖"""
        from datetime import datetime, timezone
        
        # 软删除所有该用户的菜单覆盖记录
        result = db.query(AdminUserMenuOverride).filter(
            AdminUserMenuOverride.admin_user_id == admin_user_id,
            AdminUserMenuOverride.is_deleted == False
        ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)})
        
        db.commit()
        
        app_logger.info(f"清除用户 {admin_user_id} 的所有菜单覆盖成功，共清除 {result} 条记录")
        
        return True
    
    @staticmethod
    def get_user_complete_permissions(
        db: Session,
        admin_user_id: int,
        skip: int,
        limit: int,
        keyword: Optional[str] = None
    ) -> tuple[List[AdminPermission], int]:
        """
        获取用户的完整权限列表（分页）
        逻辑：
        1. 获取用户所有角色的权限（取并集）
        2. 应用用户权限覆盖表（ALLOW添加，DENY删除）
        3. 只返回激活的权限
        4. 支持关键词搜索
        """
        # 1. 获取用户的角色
        role_ids = AdminRBACService.get_user_roles(db, admin_user_id)
        
        if not role_ids:
            permission_ids = set()
        else:
            # 2. 获取角色的权限（取并集）
            role_permissions = db.query(AdminRolePermission).filter(
                AdminRolePermission.role_id.in_(role_ids),
                AdminRolePermission.is_deleted == False
            ).all()
            
            permission_ids = set([rp.permission_id for rp in role_permissions])
        
        # 3. 应用用户权限覆盖
        overrides = db.query(AdminUserPermissionOverride).filter(
            AdminUserPermissionOverride.admin_user_id == admin_user_id,
            AdminUserPermissionOverride.is_deleted == False
        ).all()
        
        for override in overrides:
            if override.effect == EffectType.ALLOW:
                permission_ids.add(override.permission_id)
            elif override.effect == EffectType.DENY:
                permission_ids.discard(override.permission_id)
        
        # 4. 构建查询（只获取激活的权限）
        if not permission_ids:
            return [], 0
        
        query = db.query(AdminPermission).filter(
            AdminPermission.id.in_(permission_ids),
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        )
        
        # 5. 关键词搜索
        if keyword:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    AdminPermission.name.like(f"%{keyword}%"),
                    AdminPermission.api_path.like(f"%{keyword}%")
                )
            )
        
        # 6. 获取总数
        total = query.count()
        
        # 7. 分页
        permissions = query.order_by(AdminPermission.id.asc()).offset(skip).limit(limit).all()
        
        return permissions, total







