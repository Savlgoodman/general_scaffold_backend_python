"""
管理员RBAC权限服务层
处理用户权限验证相关的业务逻辑
"""
from typing import List, Set, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.admin_user_role import AdminUserRole
from app.models.admin_role_permission import AdminRolePermission
from app.models.admin_role_menu import AdminRoleMenu
from app.models.admin_user_permission_override import AdminUserPermissionOverride, EffectType
from app.models.admin_user_menu_override import AdminUserMenuOverride, MenuEffectType
from app.models.admin_permission import AdminPermission
from app.models.admin_menu import AdminMenu
from app.schemas.admin_menu import AdminMenuTreeNode
from app.schemas.admin_permission import (
    PermissionAssignment, 
    PermissionWithEffect, 
    PermissionGroup, 
    RolePermissionsGroupedResponse,
    RoleGroupPermissionsResponse,
    GroupPermissionItem,
    NonGroupPermissionItem,
    SourceType,
    PermissionSource,
    PermissionDetailItem,
    PermissionGroupDetail,
    RolePermissionsDetailResponse,
    UserPermissionsDetailResponse,
    PermissionCheckResult,
    UserPermissionOverrideItem
)
from app.services.admin_menu_service import AdminMenuService
from app.services.admin_permission_service import AdminPermissionService
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
        
        return set([p.resource_pattern for p in permissions])
    
    @staticmethod
    def get_user_permissions_with_effect(
        db: Session, 
        admin_user_id: int
    ) -> List[Tuple[AdminPermission, str, int]]:
        """
        获取用户的所有权限（包含 effect 和 priority 信息）
        
        Args:
            db: 数据库会话
            admin_user_id: 用户ID
            
        Returns:
            List of (AdminPermission, effect, priority) tuples
        """
        # 1. 获取用户的角色
        role_ids = AdminRBACService.get_user_roles(db, admin_user_id)
        
        if not role_ids:
            return []
        
        # 2. 获取角色的权限（包含 effect 和 priority）
        role_permissions = db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id.in_(role_ids),
            AdminRolePermission.is_deleted == False
        ).all()
        
        if not role_permissions:
            return []
        
        # 3. 获取权限详情
        permission_ids = [rp.permission_id for rp in role_permissions]
        permissions = db.query(AdminPermission).filter(
            AdminPermission.id.in_(permission_ids),
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all()
        
        # 4. 构建权限映射
        perm_map = {p.id: p for p in permissions}
        
        # 5. 返回带 effect 和 priority 的权限列表
        result = []
        for rp in role_permissions:
            if rp.permission_id in perm_map:
                result.append((perm_map[rp.permission_id], rp.effect, rp.priority))
        
        return result
    
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
    def check_user_permission(db: Session, admin_user_id: int, api_path: str, method: str = "POST") -> bool:
        """
        检查用户是否有某个API的权限（支持通配符和优先级）
        
        .. deprecated::
            此方法已废弃，请使用 check_permission_detail 方法获取更详细的权限检查结果。
        
        权限检查流程：
        1. 获取用户所有角色
        2. 获取角色的所有权限（包括effect和priority）
        3. 匹配请求路径（支持通配符）
        4. 按优先级排序
        5. 应用最高优先级规则
        6. 默认拒绝（无匹配规则时）
        
        Args:
            db: 数据库会话
            admin_user_id: 用户ID
            api_path: API路径
            method: HTTP方法
            
        Returns:
            是否有权限
        """
        import warnings
        warnings.warn(
            "check_user_permission 已废弃，请使用 check_permission_detail 方法",
            DeprecationWarning,
            stacklevel=2
        )
        # 1. 获取用户角色
        role_ids = AdminRBACService.get_user_roles(db, admin_user_id)
        
        if not role_ids:
            return False
        
        # 2. 获取角色权限
        role_permissions = db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id.in_(role_ids),
            AdminRolePermission.is_deleted == False
        ).all()
        
        if not role_permissions:
            return False
        
        # 3. 获取权限详情
        permission_ids = [rp.permission_id for rp in role_permissions]
        permissions = db.query(AdminPermission).filter(
            AdminPermission.id.in_(permission_ids),
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all()
        
        # 4. 匹配路径并收集规则
        matched_rules = []
        for perm in permissions:
            # 检查方法匹配（"*" 表示匹配所有方法，用于组权限）
            if perm.method != "*" and perm.method != method:
                continue
            
            # 检查路径匹配（精确匹配或通配符匹配）
            if perm.resource_pattern == api_path or AdminPermissionService.match_pattern(perm.resource_pattern, api_path):
                # 找到对应的role_permission获取effect和priority
                for rp in role_permissions:
                    if rp.permission_id == perm.id:
                        matched_rules.append((rp.effect, rp.priority))
        
        # 5. 如果没有匹配规则，默认拒绝
        if not matched_rules:
            return False
        
        # 6. 按优先级排序（降序），相同优先级时 deny 优先
        matched_rules.sort(key=lambda x: (x[1], 0 if x[0] == "deny" else 1), reverse=True)
        
        # 7. 应用最高优先级规则
        highest_priority_effect = matched_rules[0][0]
        
        return highest_priority_effect == "allow"
    
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
                    AdminPermission.resource_pattern.like(f"%{keyword}%")
                )
            )
        
        # 6. 获取总数
        total = query.count()
        
        # 7. 分页
        permissions = query.order_by(AdminPermission.id.asc()).offset(skip).limit(limit).all()
        
        return permissions, total
    
    @staticmethod
    def get_role_permissions_grouped(db: Session, role_id: int) -> RolePermissionsGroupedResponse:
        """
        获取角色的分组权限信息
        
        .. deprecated::
            此方法已废弃，请使用 get_role_permissions_detail 方法获取更详细的权限信息（包含来源追踪）。
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            
        Returns:
            RolePermissionsGroupedResponse
        """
        import warnings
        warnings.warn(
            "get_role_permissions_grouped 已废弃，请使用 get_role_permissions_detail 方法",
            DeprecationWarning,
            stacklevel=2
        )
        # 1. 获取角色的所有权限关联
        role_permissions = db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id == role_id,
            AdminRolePermission.is_deleted == False
        ).all()
        
        # 2. 获取权限详情
        permission_ids = [rp.permission_id for rp in role_permissions]
        permissions = db.query(AdminPermission).filter(
            AdminPermission.id.in_(permission_ids),
            AdminPermission.is_deleted == False
        ).all() if permission_ids else []
        
        # 3. 构建权限映射
        perm_map = {p.id: p for p in permissions}
        rp_map = {rp.permission_id: rp for rp in role_permissions}
        
        # 4. 获取所有权限（用于计算继承关系）
        all_permissions = db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all()
        
        # 5. 按 group_key 分组
        groups_dict: Dict[str, Dict[str, Any]] = {}
        
        # 首先处理角色直接拥有的权限
        for perm_id, rp in rp_map.items():
            if perm_id not in perm_map:
                continue
            
            perm = perm_map[perm_id]
            group_key = perm.group_key or "未分组"
            group_name = perm.group_name or group_key
            
            if group_key not in groups_dict:
                groups_dict[group_key] = {
                    "group_key": group_key,
                    "group_name": group_name,
                    "group_permission": None,
                    "children": []
                }
            
            perm_with_effect = PermissionWithEffect(
                id=perm.id,
                name=perm.name,
                resource_pattern=perm.resource_pattern,
                method=perm.method,
                effect=rp.effect,
                priority=rp.priority,
                is_inherited=False,
                is_overridden=False
            )
            
            if perm.is_group:
                groups_dict[group_key]["group_permission"] = perm_with_effect
            else:
                groups_dict[group_key]["children"].append(perm_with_effect)
        
        # 6. 处理继承的权限（从组权限继承）
        for group_key, group_data in groups_dict.items():
            if group_data["group_permission"] is None:
                continue
            
            group_perm = group_data["group_permission"]
            group_pattern = group_perm.resource_pattern
            
            if not group_pattern:
                continue
            
            # 找到所有匹配该组模式的子权限
            for perm in all_permissions:
                # 跳过组权限本身
                if perm.is_group:
                    continue
                
                # 检查是否已经在 children 中
                existing_ids = [c.id for c in group_data["children"]]
                if perm.id in existing_ids:
                    continue
                
                # 检查子权限的 pattern 是否属于组权限的范围
                if AdminPermissionService.is_pattern_subset(group_pattern, perm.resource_pattern):
                    # 继承的权限
                    inherited_perm = PermissionWithEffect(
                        id=perm.id,
                        name=perm.name,
                        resource_pattern=perm.resource_pattern,
                        method=perm.method,
                        effect=group_perm.effect,
                        priority=group_perm.priority,
                        is_inherited=True,
                        is_overridden=False
                    )
                    group_data["children"].append(inherited_perm)
        
        # 7. 标记被覆盖的权限
        for group_key, group_data in groups_dict.items():
            if group_data["group_permission"] is None:
                continue
            
            group_effect = group_data["group_permission"].effect
            
            for child in group_data["children"]:
                # 如果子权限有显式的 deny 而组是 allow，标记为被覆盖
                if not child.is_inherited and child.effect == "deny" and group_effect == "allow":
                    child.is_overridden = True
        
        # 8. 构建响应
        groups = [
            PermissionGroup(
                group_key=data["group_key"],
                group_name=data["group_name"],
                group_permission=data["group_permission"],
                children=data["children"]
            )
            for data in groups_dict.values()
        ]
        
        return RolePermissionsGroupedResponse(role_id=role_id, groups=groups)
    
    @staticmethod
    def assign_role_permissions(
        db: Session, 
        role_id: int, 
        permission_assignments: List[PermissionAssignment]
    ) -> bool:
        """
        批量为角色分配权限
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            permission_assignments: 权限分配列表
            
        Returns:
            是否成功
        """
        # 1. 验证所有 permission_id 存在
        permission_ids = [pa.permission_id for pa in permission_assignments]
        existing_permissions = db.query(AdminPermission).filter(
            AdminPermission.id.in_(permission_ids),
            AdminPermission.is_deleted == False
        ).all()
        
        existing_ids = {p.id for p in existing_permissions}
        for pa in permission_assignments:
            if pa.permission_id not in existing_ids:
                raise ValueError(f"权限不存在: {pa.permission_id}")
        
        # 2. 检查重复关联
        for pa in permission_assignments:
            existing = db.query(AdminRolePermission).filter(
                AdminRolePermission.role_id == role_id,
                AdminRolePermission.permission_id == pa.permission_id,
                AdminRolePermission.is_deleted == False
            ).first()
            
            if existing:
                # 更新现有关联
                existing.effect = pa.effect
                existing.priority = pa.priority
                existing.updated_at = datetime.now(timezone.utc)
            else:
                # 创建新关联
                role_permission = AdminRolePermission(
                    role_id=role_id,
                    permission_id=pa.permission_id,
                    effect=pa.effect,
                    priority=pa.priority
                )
                db.add(role_permission)
        
        db.commit()
        
        app_logger.info(f"为角色 {role_id} 分配权限成功，共 {len(permission_assignments)} 个")
        
        return True
    
    @staticmethod
    def assign_non_group_permissions(
        db: Session, 
        role_id: int, 
        permission_assignments: List[PermissionAssignment]
    ) -> bool:
        """
        批量为角色分配非组权限（只能分配 is_group=False 的权限）
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            permission_assignments: 权限分配列表
            
        Returns:
            是否成功
            
        Raises:
            ValueError: 如果包含组权限
        """
        if not permission_assignments:
            return True
        
        # 1. 验证所有 permission_id 存在且不是组权限
        permission_ids = [pa.permission_id for pa in permission_assignments]
        existing_permissions = db.query(AdminPermission).filter(
            AdminPermission.id.in_(permission_ids),
            AdminPermission.is_deleted == False
        ).all()
        
        existing_ids = {p.id for p in existing_permissions}
        
        # 检查是否所有权限都存在
        for pa in permission_assignments:
            if pa.permission_id not in existing_ids:
                raise ValueError(f"权限不存在: {pa.permission_id}")
        
        # 检查是否包含组权限
        group_perms = [p for p in existing_permissions if p.is_group]
        if group_perms:
            group_names = [p.name for p in group_perms]
            raise ValueError(f"以下是组权限，不能通过此接口分配: {group_names}")
        
        # 2. 更新或创建权限关联
        for pa in permission_assignments:
            existing = db.query(AdminRolePermission).filter(
                AdminRolePermission.role_id == role_id,
                AdminRolePermission.permission_id == pa.permission_id,
                AdminRolePermission.is_deleted == False
            ).first()
            
            if existing:
                # 更新现有关联
                existing.effect = pa.effect
                existing.priority = pa.priority
                existing.updated_at = datetime.now(timezone.utc)
            else:
                # 创建新关联
                role_permission = AdminRolePermission(
                    role_id=role_id,
                    permission_id=pa.permission_id,
                    effect=pa.effect,
                    priority=pa.priority
                )
                db.add(role_permission)
        
        db.commit()
        
        app_logger.info(f"为角色 {role_id} 分配非组权限成功，共 {len(permission_assignments)} 个")
        
        return True
    
    @staticmethod
    def remove_role_permissions(db: Session, role_id: int, permission_ids: List[int]) -> bool:
        """
        移除角色的权限
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            permission_ids: 权限ID列表
            
        Returns:
            是否成功
        """
        result = db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id == role_id,
            AdminRolePermission.permission_id.in_(permission_ids),
            AdminRolePermission.is_deleted == False
        ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)})
        
        db.commit()
        
        app_logger.info(f"移除角色 {role_id} 的权限成功，共 {result} 个")
        
        return True
    
    @staticmethod
    def calculate_effective_permission(
        db: Session, 
        role_id: int, 
        api_path: str, 
        method: str = "POST"
    ) -> Optional[str]:
        """
        计算特定 API 路径的有效权限
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            api_path: API路径
            method: HTTP方法
            
        Returns:
            有效权限效果 ("allow", "deny") 或 None（无匹配）
        """
        # 1. 获取角色权限
        role_permissions = db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id == role_id,
            AdminRolePermission.is_deleted == False
        ).all()
        
        if not role_permissions:
            return None
        
        # 2. 获取权限详情
        permission_ids = [rp.permission_id for rp in role_permissions]
        permissions = db.query(AdminPermission).filter(
            AdminPermission.id.in_(permission_ids),
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all()
        
        # 3. 匹配路径并收集规则
        matched_rules = []
        for perm in permissions:
            # 检查方法匹配（"*" 表示匹配所有方法，用于组权限）
            if perm.method != "*" and perm.method != method:
                continue
            
            if perm.resource_pattern == api_path or AdminPermissionService.match_pattern(perm.resource_pattern, api_path):
                for rp in role_permissions:
                    if rp.permission_id == perm.id:
                        matched_rules.append((rp.effect, rp.priority))
        
        if not matched_rules:
            return None
        
        # 4. 按优先级排序
        matched_rules.sort(key=lambda x: (x[1], 0 if x[0] == "deny" else 1), reverse=True)
        
        return matched_rules[0][0]
    
    @staticmethod
    def get_role_group_permissions(
        db: Session, 
        role_id: int,
        granted: Optional[str] = None
    ) -> RoleGroupPermissionsResponse:
        """
        获取所有组权限列表，标记已授权的
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            granted: 筛选条件 - "granted"=已授权, "not_granted"=未授权, None=全部
            
        Returns:
            RoleGroupPermissionsResponse
        """
        # 1. 获取所有组权限
        all_group_permissions = db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1,
            AdminPermission.is_group == True
        ).all()
        
        # 2. 获取角色已授权的权限
        role_permissions = db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id == role_id,
            AdminRolePermission.is_deleted == False
        ).all()
        
        granted_map = {rp.permission_id: rp for rp in role_permissions}
        
        # 3. 获取所有非组权限（用于计算子权限数量）
        all_non_group_permissions = db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1,
            AdminPermission.is_group == False
        ).all()
        
        # 按 group_key 统计子权限数量
        group_key_children_count: Dict[str, int] = {}
        for perm in all_non_group_permissions:
            if perm.group_key:
                group_key_children_count[perm.group_key] = group_key_children_count.get(perm.group_key, 0) + 1
        
        # 4. 构建结果
        items = []
        for perm in all_group_permissions:
            is_granted = perm.id in granted_map
            rp = granted_map.get(perm.id)
            
            # 筛选
            if granted == "granted" and not is_granted:
                continue
            if granted == "not_granted" and is_granted:
                continue
            
            # 通过 group_key 获取子权限数量
            children_count = group_key_children_count.get(perm.group_key, 0) if perm.group_key else 0
            
            item = GroupPermissionItem(
                id=perm.id,
                name=perm.name,
                resource_pattern=perm.resource_pattern,
                method=perm.method,
                group_key=perm.group_key,
                group_name=perm.group_name,
                description=perm.description,
                is_granted=is_granted,
                effect=rp.effect if rp else None,
                priority=rp.priority if rp else None,
                children_count=children_count
            )
            items.append(item)
        
        return RoleGroupPermissionsResponse(role_id=role_id, items=items)
    
    @staticmethod
    def get_role_non_group_permissions(
        db: Session,
        role_id: int,
        skip: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None,
        granted: Optional[str] = None
    ) -> tuple[List[NonGroupPermissionItem], int]:
        """
        获取所有非组权限列表（分页），标记已授权的
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            skip: 跳过数量
            limit: 限制数量
            keyword: 搜索关键词
            granted: 筛选条件 - "granted"=已授权, "not_granted"=未授权, None=全部
            
        Returns:
            (权限列表, 总数)
        """
        from sqlalchemy import or_
        
        # 1. 获取角色已授权的权限
        role_permissions = db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id == role_id,
            AdminRolePermission.is_deleted == False
        ).all()
        
        granted_map = {rp.permission_id: rp for rp in role_permissions}
        granted_ids = set(granted_map.keys())
        
        # 2. 获取角色已授权的组权限（用于计算继承）
        granted_group_perms = db.query(AdminPermission).filter(
            AdminPermission.id.in_(granted_ids),
            AdminPermission.is_deleted == False,
            AdminPermission.is_group == True
        ).all() if granted_ids else []
        
        # 构建已授权组权限的 group_key -> role_permission 映射
        granted_group_keys: Dict[str, AdminRolePermission] = {}
        for group_perm in granted_group_perms:
            if group_perm.group_key:
                rp = granted_map.get(group_perm.id)
                if rp:
                    granted_group_keys[group_perm.group_key] = rp
        
        # 3. 构建查询
        query = db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1,
            AdminPermission.is_group == False
        )
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    AdminPermission.name.like(f"%{keyword}%"),
                    AdminPermission.resource_pattern.like(f"%{keyword}%")
                )
            )
        
        # 4. 获取所有非组权限
        all_non_group_permissions = query.all()
        
        # 5. 处理每个权限，判断是否已授权或继承
        items = []
        for perm in all_non_group_permissions:
            is_granted = perm.id in granted_ids
            is_inherited = False
            inherited_effect = None
            inherited_priority = None
            
            # 检查是否从组权限继承（通过 group_key 匹配）
            if not is_granted and perm.group_key and perm.group_key in granted_group_keys:
                is_inherited = True
                rp = granted_group_keys[perm.group_key]
                inherited_effect = rp.effect
                inherited_priority = rp.priority
            
            rp = granted_map.get(perm.id)
            
            # 筛选
            actual_granted = is_granted or is_inherited
            if granted == "granted" and not actual_granted:
                continue
            if granted == "not_granted" and actual_granted:
                continue
            
            item = NonGroupPermissionItem(
                id=perm.id,
                name=perm.name,
                resource_pattern=perm.resource_pattern,
                method=perm.method,
                group_key=perm.group_key,
                group_name=perm.group_name,
                description=perm.description,
                is_granted=is_granted or is_inherited,
                effect=rp.effect if rp else inherited_effect,
                priority=rp.priority if rp else inherited_priority,
                is_inherited=is_inherited
            )
            items.append(item)
        
        # 6. 计算总数和分页
        total = len(items)
        paginated_items = items[skip:skip + limit]
        
        return paginated_items, total
    
    @staticmethod
    def get_role_permissions_detail(
        db: Session, 
        role_id: int
    ) -> RolePermissionsDetailResponse:
        """
        获取角色的完整权限详情（按分组）
        
        计算逻辑：
        1. 获取角色的所有权限关联
        2. 处理组权限
        3. 处理子权限继承
        4. 处理子权限覆盖
        5. 按 group_key 分组返回
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            
        Returns:
            RolePermissionsDetailResponse
        """
        from app.models.admin_role import AdminRole
        
        # 获取角色信息
        role = db.query(AdminRole).filter(
            AdminRole.id == role_id,
            AdminRole.is_deleted == False
        ).first()
        
        if not role:
            raise ValueError(f"角色不存在: {role_id}")
        
        # 1. 获取角色的所有权限关联
        role_permissions = db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id == role_id,
            AdminRolePermission.is_deleted == False
        ).all()
        
        # 2. 获取权限详情
        permission_ids = [rp.permission_id for rp in role_permissions]
        permissions = db.query(AdminPermission).filter(
            AdminPermission.id.in_(permission_ids),
            AdminPermission.is_deleted == False
        ).all() if permission_ids else []
        
        # 3. 构建权限映射
        perm_map = {p.id: p for p in permissions}
        rp_map = {rp.permission_id: rp for rp in role_permissions}
        
        # 4. 获取所有权限（用于计算继承关系）
        all_permissions = db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all()
        
        # 5. 按 group_key 分组处理
        groups_dict: Dict[str, Dict[str, Any]] = {}
        
        # 5.1 首先处理角色直接拥有的组权限
        for perm_id, rp in rp_map.items():
            if perm_id not in perm_map:
                continue
            
            perm = perm_map[perm_id]
            if not perm.is_group:
                continue
            
            group_key = perm.group_key or "未分组"
            group_name = perm.group_name or group_key
            
            if group_key not in groups_dict:
                groups_dict[group_key] = {
                    "group_key": group_key,
                    "group_name": group_name,
                    "group_permission": None,
                    "children": [],
                    "children_map": {}  # 用于快速查找子权限
                }
            
            # 创建组权限的来源信息
            source = PermissionSource(
                type=SourceType.GROUP_PERMISSION,
                role_id=role_id,
                role_name=role.name,
                permission_id=perm.id,
                permission_name=perm.name
            )
            
            group_perm_item = PermissionDetailItem(
                id=perm.id,
                name=perm.name,
                resource_pattern=perm.resource_pattern,
                method=perm.method,
                group_key=perm.group_key,
                group_name=perm.group_name,
                effect=rp.effect,
                source=source,
                source_description=source.get_description(rp.effect),
                is_inherited=False,
                is_overridden=False
            )
            
            groups_dict[group_key]["group_permission"] = group_perm_item
        
        # 5.2 处理继承的子权限（从组权限继承）
        for group_key, group_data in groups_dict.items():
            if group_data["group_permission"] is None:
                continue
            
            group_perm = group_data["group_permission"]
            
            # 找到所有属于该组的子权限
            for perm in all_permissions:
                if perm.is_group:
                    continue
                
                # 检查子权限是否属于该组
                if perm.group_key != group_key:
                    continue
                
                # 创建继承的子权限
                source = PermissionSource(
                    type=SourceType.GROUP_PERMISSION,
                    role_id=role_id,
                    role_name=role.name,
                    permission_id=group_perm.id,
                    permission_name=group_perm.name
                )
                
                child_item = PermissionDetailItem(
                    id=perm.id,
                    name=perm.name,
                    resource_pattern=perm.resource_pattern,
                    method=perm.method,
                    group_key=perm.group_key,
                    group_name=perm.group_name,
                    effect=group_perm.effect,  # 继承组权限的 effect
                    source=source,
                    source_description=source.get_description(group_perm.effect),
                    is_inherited=True,
                    is_overridden=False
                )
                
                group_data["children"].append(child_item)
                group_data["children_map"][perm.id] = child_item
        
        # 5.3 处理角色直接拥有的子权限（可能覆盖继承的）
        for perm_id, rp in rp_map.items():
            if perm_id not in perm_map:
                continue
            
            perm = perm_map[perm_id]
            if perm.is_group:
                continue
            
            group_key = perm.group_key or "未分组"
            group_name = perm.group_name or group_key
            
            # 确保分组存在
            if group_key not in groups_dict:
                groups_dict[group_key] = {
                    "group_key": group_key,
                    "group_name": group_name,
                    "group_permission": None,
                    "children": [],
                    "children_map": {}
                }
            
            # 创建子权限的来源信息
            source = PermissionSource(
                type=SourceType.SINGLE_PERMISSION,
                role_id=role_id,
                role_name=role.name,
                permission_id=perm.id,
                permission_name=perm.name
            )
            
            # 检查是否已存在继承的权限
            if perm.id in groups_dict[group_key]["children_map"]:
                # 覆盖继承的权限
                existing_child = groups_dict[group_key]["children_map"][perm.id]
                group_perm = groups_dict[group_key]["group_permission"]
                
                # 判断是否被覆盖（effect 与组权限不同）
                is_overridden = group_perm is not None and rp.effect != group_perm.effect
                
                # 更新子权限
                existing_child.effect = rp.effect
                existing_child.source = source
                existing_child.source_description = source.get_description(rp.effect)
                existing_child.is_inherited = False
                existing_child.is_overridden = is_overridden
            else:
                # 新增子权限
                child_item = PermissionDetailItem(
                    id=perm.id,
                    name=perm.name,
                    resource_pattern=perm.resource_pattern,
                    method=perm.method,
                    group_key=perm.group_key,
                    group_name=perm.group_name,
                    effect=rp.effect,
                    source=source,
                    source_description=source.get_description(rp.effect),
                    is_inherited=False,
                    is_overridden=False
                )
                
                groups_dict[group_key]["children"].append(child_item)
                groups_dict[group_key]["children_map"][perm.id] = child_item
        
        # 6. 构建响应
        groups = [
            PermissionGroupDetail(
                group_key=data["group_key"],
                group_name=data["group_name"],
                group_permission=data["group_permission"],
                children=data["children"]
            )
            for data in groups_dict.values()
        ]
        
        return RolePermissionsDetailResponse(
            role_id=role_id,
            role_name=role.name,
            groups=groups
        )








    @staticmethod
    def get_user_permissions_detail(
        db: Session, 
        user_id: int
    ) -> UserPermissionsDetailResponse:
        """
        获取用户的完整权限详情（按分组）
        
        计算逻辑：
        1. 获取用户的所有角色
        2. 对每个角色获取权限详情
        3. 合并多角色权限（allow 优先）
        4. 应用用户权限覆盖
        5. 按 group_key 分组返回
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            UserPermissionsDetailResponse
        """
        from app.models.admin_user import AdminUser
        from app.models.admin_role import AdminRole
        
        # 获取用户信息
        user = db.query(AdminUser).filter(
            AdminUser.id == user_id,
            AdminUser.is_deleted == False
        ).first()
        
        if not user:
            raise ValueError(f"用户不存在: {user_id}")
        
        # 1. 获取用户的所有角色
        role_ids = AdminRBACService.get_user_roles(db, user_id)
        
        # 获取角色信息
        roles = db.query(AdminRole).filter(
            AdminRole.id.in_(role_ids),
            AdminRole.is_deleted == False
        ).all() if role_ids else []
        
        role_map = {r.id: r for r in roles}
        
        # 2. 获取所有权限（用于后续处理）
        all_permissions = db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all()
        
        perm_map = {p.id: p for p in all_permissions}
        
        # 3. 合并多角色权限
        # 结构: {permission_id: {"effect": str, "source": PermissionSource, "is_inherited": bool}}
        merged_permissions: Dict[int, Dict[str, Any]] = {}
        
        for role_id in role_ids:
            if role_id not in role_map:
                continue
            
            role = role_map[role_id]
            
            # 获取角色的权限关联
            role_permissions = db.query(AdminRolePermission).filter(
                AdminRolePermission.role_id == role_id,
                AdminRolePermission.is_deleted == False
            ).all()
            
            rp_map = {rp.permission_id: rp for rp in role_permissions}
            
            # 处理组权限和继承
            for perm_id, rp in rp_map.items():
                if perm_id not in perm_map:
                    continue
                
                perm = perm_map[perm_id]
                
                if perm.is_group:
                    # 组权限
                    source = PermissionSource(
                        type=SourceType.GROUP_PERMISSION,
                        role_id=role_id,
                        role_name=role.name,
                        permission_id=perm.id,
                        permission_name=perm.name
                    )
                    
                    # 合并组权限
                    if perm.id not in merged_permissions:
                        merged_permissions[perm.id] = {
                            "effect": rp.effect,
                            "source": source,
                            "is_inherited": False,
                            "is_overridden": False
                        }
                    elif rp.effect == "allow" and merged_permissions[perm.id]["effect"] == "deny":
                        # allow 优先
                        merged_permissions[perm.id] = {
                            "effect": rp.effect,
                            "source": source,
                            "is_inherited": False,
                            "is_overridden": False
                        }
                    
                    # 处理继承的子权限
                    for child_perm in all_permissions:
                        if child_perm.is_group or child_perm.group_key != perm.group_key:
                            continue
                        
                        child_source = PermissionSource(
                            type=SourceType.GROUP_PERMISSION,
                            role_id=role_id,
                            role_name=role.name,
                            permission_id=perm.id,
                            permission_name=perm.name
                        )
                        
                        if child_perm.id not in merged_permissions:
                            merged_permissions[child_perm.id] = {
                                "effect": rp.effect,
                                "source": child_source,
                                "is_inherited": True,
                                "is_overridden": False
                            }
                        elif rp.effect == "allow" and merged_permissions[child_perm.id]["effect"] == "deny":
                            # allow 优先
                            merged_permissions[child_perm.id] = {
                                "effect": rp.effect,
                                "source": child_source,
                                "is_inherited": True,
                                "is_overridden": False
                            }
                else:
                    # 子权限
                    source = PermissionSource(
                        type=SourceType.SINGLE_PERMISSION,
                        role_id=role_id,
                        role_name=role.name,
                        permission_id=perm.id,
                        permission_name=perm.name
                    )
                    
                    if perm.id not in merged_permissions:
                        merged_permissions[perm.id] = {
                            "effect": rp.effect,
                            "source": source,
                            "is_inherited": False,
                            "is_overridden": False
                        }
                    elif rp.effect == "allow" and merged_permissions[perm.id]["effect"] == "deny":
                        # allow 优先
                        merged_permissions[perm.id] = {
                            "effect": rp.effect,
                            "source": source,
                            "is_inherited": False,
                            "is_overridden": False
                        }
                    elif merged_permissions[perm.id]["is_inherited"]:
                        # 子权限覆盖继承的权限
                        merged_permissions[perm.id] = {
                            "effect": rp.effect,
                            "source": source,
                            "is_inherited": False,
                            "is_overridden": True
                        }
        
        # 4. 应用用户权限覆盖
        overrides = db.query(AdminUserPermissionOverride).filter(
            AdminUserPermissionOverride.admin_user_id == user_id,
            AdminUserPermissionOverride.is_deleted == False
        ).all()
        
        for override in overrides:
            if override.permission_id not in perm_map:
                continue
            
            perm = perm_map[override.permission_id]
            effect = "allow" if override.effect == EffectType.ALLOW else "deny"
            
            source = PermissionSource(
                type=SourceType.USER_OVERRIDE,
                permission_id=perm.id,
                permission_name=perm.name
            )
            
            merged_permissions[perm.id] = {
                "effect": effect,
                "source": source,
                "is_inherited": False,
                "is_overridden": True
            }
        
        # 5. 按 group_key 分组
        groups_dict: Dict[str, Dict[str, Any]] = {}
        
        for perm_id, perm_data in merged_permissions.items():
            if perm_id not in perm_map:
                continue
            
            perm = perm_map[perm_id]
            group_key = perm.group_key or "未分组"
            group_name = perm.group_name or group_key
            
            if group_key not in groups_dict:
                groups_dict[group_key] = {
                    "group_key": group_key,
                    "group_name": group_name,
                    "group_permission": None,
                    "children": []
                }
            
            perm_item = PermissionDetailItem(
                id=perm.id,
                name=perm.name,
                resource_pattern=perm.resource_pattern,
                method=perm.method,
                group_key=perm.group_key,
                group_name=perm.group_name,
                effect=perm_data["effect"],
                source=perm_data["source"],
                source_description=perm_data["source"].get_description(perm_data["effect"]),
                is_inherited=perm_data["is_inherited"],
                is_overridden=perm_data["is_overridden"]
            )
            
            if perm.is_group:
                groups_dict[group_key]["group_permission"] = perm_item
            else:
                groups_dict[group_key]["children"].append(perm_item)
        
        # 6. 构建响应
        groups = [
            PermissionGroupDetail(
                group_key=data["group_key"],
                group_name=data["group_name"],
                group_permission=data["group_permission"],
                children=data["children"]
            )
            for data in groups_dict.values()
        ]
        
        return UserPermissionsDetailResponse(
            user_id=user_id,
            username=user.username,
            groups=groups
        )

    @staticmethod
    def check_permission_detail(
        db: Session, 
        user_id: int, 
        api_path: str, 
        method: str = "POST"
    ) -> PermissionCheckResult:
        """
        检查用户是否有某个 API 的权限（返回详细结果）
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            api_path: API路径
            method: HTTP方法
            
        Returns:
            PermissionCheckResult 包含详细的权限检查结果
        """
        from app.models.admin_user import AdminUser
        from app.models.admin_role import AdminRole
        
        # 获取用户信息
        user = db.query(AdminUser).filter(
            AdminUser.id == user_id,
            AdminUser.is_deleted == False
        ).first()
        
        if not user:
            source = PermissionSource(type=SourceType.NO_PERMISSION)
            return PermissionCheckResult(
                allowed=False,
                effect="deny",
                source=source,
                deny_reason="用户不存在"
            )
        
        # 1. 获取用户的所有角色
        role_ids = AdminRBACService.get_user_roles(db, user_id)
        
        if not role_ids:
            source = PermissionSource(type=SourceType.NO_PERMISSION)
            return PermissionCheckResult(
                allowed=False,
                effect="deny",
                source=source,
                deny_reason="拒绝于无权限配置"
            )
        
        # 获取角色信息
        roles = db.query(AdminRole).filter(
            AdminRole.id.in_(role_ids),
            AdminRole.is_deleted == False
        ).all()
        
        role_map = {r.id: r for r in roles}
        
        # 2. 获取所有角色的权限
        role_permissions = db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id.in_(role_ids),
            AdminRolePermission.is_deleted == False
        ).all()
        
        if not role_permissions:
            source = PermissionSource(type=SourceType.NO_PERMISSION)
            return PermissionCheckResult(
                allowed=False,
                effect="deny",
                source=source,
                deny_reason="拒绝于无权限配置"
            )
        
        # 3. 获取权限详情（包括所有启用的权限，用于组权限匹配）
        permission_ids = [rp.permission_id for rp in role_permissions]
        
        # 获取角色直接拥有的权限
        direct_permissions = db.query(AdminPermission).filter(
            AdminPermission.id.in_(permission_ids),
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all()
        
        perm_map = {p.id: p for p in direct_permissions}
        
        # 构建角色权限映射 {permission_id: [(role_id, effect, priority), ...]}
        rp_by_perm: Dict[int, list] = {}
        for rp in role_permissions:
            if rp.permission_id not in rp_by_perm:
                rp_by_perm[rp.permission_id] = []
            rp_by_perm[rp.permission_id].append((rp.role_id, rp.effect, rp.priority))
        
        # 4. 匹配路径并收集规则
        matched_rules = []
        
        for perm in direct_permissions:
            # 检查方法匹配（"*" 表示匹配所有方法，用于组权限）
            if perm.method != "*" and perm.method != method:
                continue
            
            # 检查路径匹配（精确匹配或通配符匹配）
            if perm.resource_pattern == api_path or AdminPermissionService.match_pattern(perm.resource_pattern, api_path):
                # 找到对应的 role_permission 获取 effect 和 priority
                for role_id, effect, priority in rp_by_perm.get(perm.id, []):
                    role = role_map.get(role_id)
                    role_name = role.name if role else "未知角色"
                    
                    source_type = SourceType.GROUP_PERMISSION if perm.is_group else SourceType.SINGLE_PERMISSION
                    source = PermissionSource(
                        type=source_type,
                        role_id=role_id,
                        role_name=role_name,
                        permission_id=perm.id,
                        permission_name=perm.name
                    )
                    
                    # 计算路径具体程度（用于排序）
                    # 精确匹配 > 单通配符 > 双通配符
                    specificity = 0
                    if perm.resource_pattern == api_path:
                        specificity = 3  # 精确匹配
                    elif '**' not in perm.resource_pattern:
                        specificity = 2  # 单通配符 (*)
                    else:
                        specificity = 1  # 双通配符 (**)
                    
                    # 子权限比组权限更具体
                    if not perm.is_group:
                        specificity += 10  # 子权限加分
                    
                    matched_rules.append({
                        "effect": effect,
                        "priority": priority,
                        "specificity": specificity,
                        "is_group": perm.is_group,
                        "source": source
                    })
        
        # 5. 应用用户权限覆盖
        overrides = db.query(AdminUserPermissionOverride).filter(
            AdminUserPermissionOverride.admin_user_id == user_id,
            AdminUserPermissionOverride.is_deleted == False
        ).all()
        
        # 获取覆盖权限的详情
        override_perm_ids = [o.permission_id for o in overrides]
        override_perms = db.query(AdminPermission).filter(
            AdminPermission.id.in_(override_perm_ids),
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all() if override_perm_ids else []
        
        override_perm_map = {p.id: p for p in override_perms}
        
        for override in overrides:
            if override.permission_id not in override_perm_map:
                continue
            
            perm = override_perm_map[override.permission_id]
            
            # 检查方法匹配
            if perm.method != "*" and perm.method != method:
                continue
            
            # 检查路径匹配
            if perm.resource_pattern == api_path or AdminPermissionService.match_pattern(perm.resource_pattern, api_path):
                effect = "allow" if override.effect == EffectType.ALLOW else "deny"
                
                source = PermissionSource(
                    type=SourceType.USER_OVERRIDE,
                    permission_id=perm.id,
                    permission_name=perm.name
                )
                
                # 用户覆盖优先级最高
                # specificity 设为最高，确保用户覆盖优先
                specificity = 100
                if not perm.is_group:
                    specificity += 10
                
                matched_rules.append({
                    "effect": effect,
                    "priority": 9999,  # 最高优先级
                    "specificity": specificity,
                    "is_group": perm.is_group,
                    "source": source
                })
        
        # 6. 如果没有匹配规则，默认拒绝
        if not matched_rules:
            source = PermissionSource(type=SourceType.NO_PERMISSION)
            return PermissionCheckResult(
                allowed=False,
                effect="deny",
                source=source,
                deny_reason="拒绝于无权限配置"
            )
        
        # 7. 排序规则（优先级从高到低）：
        #    1. specificity（具体程度）：子权限 > 组权限，精确匹配 > 通配符
        #    2. priority（用户设置的优先级）
        #    3. effect：deny 优先于 allow（安全原则）
        matched_rules.sort(
            key=lambda x: (
                x["specificity"],           # 具体程度越高越优先
                x["priority"],              # 优先级越高越优先
                0 if x["effect"] == "deny" else 1  # deny 优先于 allow
            ),
            reverse=True
        )
        
        # 8. 应用最高优先级规则
        highest_rule = matched_rules[0]
        allowed = highest_rule["effect"] == "allow"
        
        deny_reason = None
        if not allowed:
            deny_reason = highest_rule["source"].get_description(highest_rule["effect"])
        
        return PermissionCheckResult(
            allowed=allowed,
            effect=highest_rule["effect"],
            source=highest_rule["source"],
            deny_reason=deny_reason
        )

    @staticmethod
    def get_user_permissions_for_override_management(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None,
        overridden_filter: Optional[str] = None
    ) -> tuple[list, int]:
        """
        获取用户权限覆盖管理列表
        
        用于管理员查看和管理用户的权限覆盖状态。
        返回所有非组权限，标记每个权限的角色授权状态和用户覆盖状态。
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过数量
            limit: 限制数量
            keyword: 搜索关键词（权限名称、资源模式）
            overridden_filter: 覆盖状态筛选 - "overridden"=已覆盖, "not_overridden"=未覆盖, None=全部
            
        Returns:
            (权限列表, 总数)
        """
        from sqlalchemy import or_
        from app.schemas.admin_permission import UserPermissionOverrideItem
        from app.models.admin_user import AdminUser
        from app.models.admin_role import AdminRole
        
        # 获取用户信息
        user = db.query(AdminUser).filter(
            AdminUser.id == user_id,
            AdminUser.is_deleted == False
        ).first()
        
        if not user:
            raise ValueError(f"用户不存在: {user_id}")
        
        # 1. 获取所有非组权限
        query = db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1,
            AdminPermission.is_group == False
        )
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    AdminPermission.name.like(f"%{keyword}%"),
                    AdminPermission.resource_pattern.like(f"%{keyword}%")
                )
            )
        
        all_non_group_permissions = query.all()
        
        # 2. 获取用户的角色
        role_ids = AdminRBACService.get_user_roles(db, user_id)
        
        # 获取角色信息
        roles = db.query(AdminRole).filter(
            AdminRole.id.in_(role_ids),
            AdminRole.is_deleted == False
        ).all() if role_ids else []
        
        role_map = {r.id: r for r in roles}
        
        # 3. 获取角色的权限关联
        role_permissions = db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id.in_(role_ids),
            AdminRolePermission.is_deleted == False
        ).all() if role_ids else []
        
        # 构建角色权限映射 {permission_id: [(role_id, effect), ...]}
        # 需要保留所有角色的授权，用于合并（allow 优先）
        role_perm_list: Dict[int, list] = {}
        for rp in role_permissions:
            if rp.permission_id not in role_perm_list:
                role_perm_list[rp.permission_id] = []
            role_perm_list[rp.permission_id].append((rp.role_id, rp.effect))
        
        # 合并多角色权限（allow 优先）
        role_perm_map: Dict[int, tuple] = {}
        for perm_id, rp_list in role_perm_list.items():
            # 优先选择 allow
            best_rp = None
            for role_id, effect in rp_list:
                if best_rp is None:
                    best_rp = (role_id, effect)
                elif effect == "allow" and best_rp[1] == "deny":
                    best_rp = (role_id, effect)
            if best_rp:
                role_perm_map[perm_id] = best_rp
        
        # 4. 获取角色的组权限（用于计算继承）
        all_permissions = db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all()
        
        # 构建组权限映射 {group_key: [(role_id, effect, perm_name), ...]}
        group_perm_list: Dict[str, list] = {}
        for perm in all_permissions:
            if perm.is_group and perm.id in role_perm_map:
                role_id, effect = role_perm_map[perm.id]
                if perm.group_key:
                    if perm.group_key not in group_perm_list:
                        group_perm_list[perm.group_key] = []
                    group_perm_list[perm.group_key].append((role_id, effect, perm.name))
        
        # 合并组权限（allow 优先）
        group_perm_map: Dict[str, tuple] = {}
        for group_key, gp_list in group_perm_list.items():
            best_gp = None
            for role_id, effect, perm_name in gp_list:
                if best_gp is None:
                    best_gp = (role_id, effect, perm_name)
                elif effect == "allow" and best_gp[1] == "deny":
                    best_gp = (role_id, effect, perm_name)
            if best_gp:
                group_perm_map[group_key] = best_gp
        
        # 5. 获取用户权限覆盖
        overrides = db.query(AdminUserPermissionOverride).filter(
            AdminUserPermissionOverride.admin_user_id == user_id,
            AdminUserPermissionOverride.is_deleted == False
        ).all()
        
        override_map = {o.permission_id: o for o in overrides}
        
        # 6. 构建结果列表
        items = []
        for perm in all_non_group_permissions:
            # 角色层面的权限状态
            role_granted = False
            role_effect = None
            role_source = None
            is_inherited = False
            
            # 检查角色直接授权
            if perm.id in role_perm_map:
                role_id, effect = role_perm_map[perm.id]
                role = role_map.get(role_id)
                role_name = role.name if role else "未知角色"
                role_granted = True
                role_effect = effect
                role_source = f"角色[{role_name}]的子权限[{perm.name}]"
                is_inherited = False
            # 检查组权限继承
            elif perm.group_key and perm.group_key in group_perm_map:
                role_id, effect, group_perm_name = group_perm_map[perm.group_key]
                role = role_map.get(role_id)
                role_name = role.name if role else "未知角色"
                role_granted = True
                role_effect = effect
                role_source = f"角色[{role_name}]的组权限[{group_perm_name}]"
                is_inherited = True
            
            # 用户覆盖状态
            is_overridden = perm.id in override_map
            override_effect = None
            if is_overridden:
                override = override_map[perm.id]
                override_effect = "allow" if override.effect == EffectType.ALLOW else "deny"
            
            # 计算最终效果和来源描述
            final_effect = "deny"  # 默认拒绝
            source_description = "无权限配置"
            
            if is_overridden:
                # 用户覆盖优先
                final_effect = override_effect
                source_description = f"{'允许' if override_effect == 'allow' else '拒绝'}于用户权限覆盖"
            elif role_granted:
                # 角色授权
                final_effect = role_effect
                effect_text = "允许" if role_effect == "allow" else "拒绝"
                source_description = f"{effect_text}于{role_source}"
            
            # 筛选
            if overridden_filter == "overridden" and not is_overridden:
                continue
            if overridden_filter == "not_overridden" and is_overridden:
                continue
            
            item = UserPermissionOverrideItem(
                id=perm.id,
                name=perm.name,
                resource_pattern=perm.resource_pattern,
                method=perm.method,
                group_key=perm.group_key,
                group_name=perm.group_name,
                description=perm.description,
                role_granted=role_granted,
                role_effect=role_effect,
                role_source=role_source,
                is_inherited=is_inherited,
                is_overridden=is_overridden,
                override_effect=override_effect,
                final_effect=final_effect,
                source_description=source_description
            )
            items.append(item)
        
        # 7. 计算总数和分页
        total = len(items)
        paginated_items = items[skip:skip + limit]
        
        return paginated_items, total
