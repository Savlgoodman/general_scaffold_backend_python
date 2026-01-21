"""
管理员角色服务层
处理管理员角色相关的业务逻辑
"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.admin_role import AdminRole
from app.models.admin_role_permission import AdminRolePermission
from app.models.admin_role_menu import AdminRoleMenu
from app.schemas.admin_role import AdminRoleCreate, AdminRoleUpdate
from app.core.logger import app_logger


class AdminRoleService:
    """管理员角色服务"""
    
    @staticmethod
    def get_by_id(db: Session, role_id: int) -> Optional[AdminRole]:
        """根据ID获取角色"""
        return db.query(AdminRole).filter(
            AdminRole.id == role_id,
            AdminRole.is_deleted == False
        ).first()
    
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[AdminRole]:
        """根据名称获取角色"""
        return db.query(AdminRole).filter(
            AdminRole.name == name,
            AdminRole.is_deleted == False
        ).first()
    
    @staticmethod
    def get_list(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None,
        status: Optional[int] = None,
    ) -> tuple[List[AdminRole], int]:
        """
        获取角色列表
        
        Returns:
            (角色列表, 总数)
        """
        query = db.query(AdminRole).filter(AdminRole.is_deleted == False)
        
        # 关键词搜索
        if keyword:
            query = query.filter(AdminRole.name.like(f"%{keyword}%"))
        
        # 状态筛选
        if status is not None:
            query = query.filter(AdminRole.status == status)
        
        # 获取总数
        total = query.count()
        
        # 分页
        roles = query.order_by(AdminRole.created_at.desc()).offset(skip).limit(limit).all()
        
        return roles, total
    
    @staticmethod
    def get_all_active(db: Session) -> List[AdminRole]:
        """获取所有激活的角色"""
        return db.query(AdminRole).filter(
            AdminRole.is_deleted == False,
            AdminRole.status == 1
        ).all()
    
    @staticmethod
    def create(db: Session, role_in: AdminRoleCreate) -> AdminRole:
        """创建角色"""
        # 检查角色名称是否存在
        if AdminRoleService.get_by_name(db, role_in.name):
            raise ValueError("角色名称已存在")
        
        # 创建角色
        role = AdminRole(
            name=role_in.name,
            remark=role_in.remark,
            status=role_in.status,
        )
        
        db.add(role)
        db.commit()
        db.refresh(role)
        
        app_logger.info(f"创建角色成功: {role.name}")
        
        return role
    
    @staticmethod
    def update(db: Session, role_id: int, role_in: AdminRoleUpdate) -> Optional[AdminRole]:
        """更新角色"""
        role = AdminRoleService.get_by_id(db, role_id)
        if not role:
            return None
        
        # 更新字段
        update_data = role_in.model_dump(exclude_unset=True)
        
        # 检查角色名称是否被其他角色使用
        if "name" in update_data:
            existing_role = AdminRoleService.get_by_name(db, update_data["name"])
            if existing_role and existing_role.id != role_id:
                raise ValueError("角色名称已被使用")
        
        for field, value in update_data.items():
            setattr(role, field, value)
        
        role.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(role)
        
        app_logger.info(f"更新角色成功: {role.name}")
        
        return role
    
    @staticmethod
    def delete(db: Session, role_id: int) -> bool:
        """逻辑删除角色"""
        role = AdminRoleService.get_by_id(db, role_id)
        if not role:
            return False
        
        role.is_deleted = True
        role.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        app_logger.info(f"逻辑删除角色成功: {role.name}")
        
        return True
    
    @staticmethod
    def assign_permissions(db: Session, role_id: int, permission_ids: List[int]) -> bool:
        """为角色分配权限"""
        role = AdminRoleService.get_by_id(db, role_id)
        if not role:
            return False
        
        # 删除旧的权限关联
        db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id == role_id,
            AdminRolePermission.is_deleted == False
        ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)})
        
        # 创建新的权限关联
        for permission_id in permission_ids:
            role_permission = AdminRolePermission(
                role_id=role_id,
                permission_id=permission_id
            )
            db.add(role_permission)
        
        db.commit()
        
        app_logger.info(f"为角色 {role.name} 分配权限成功")
        
        return True
    
    @staticmethod
    def assign_menus(db: Session, role_id: int, menu_ids: List[int]) -> bool:
        """为角色分配菜单"""
        role = AdminRoleService.get_by_id(db, role_id)
        if not role:
            return False
        
        # 删除旧的菜单关联
        db.query(AdminRoleMenu).filter(
            AdminRoleMenu.role_id == role_id,
            AdminRoleMenu.is_deleted == False
        ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)})
        
        # 创建新的菜单关联
        for menu_id in menu_ids:
            role_menu = AdminRoleMenu(
                role_id=role_id,
                menu_id=menu_id
            )
            db.add(role_menu)
        
        db.commit()
        
        app_logger.info(f"为角色 {role.name} 分配菜单成功")
        
        return True
    
    @staticmethod
    def get_role_permissions(db: Session, role_id: int) -> List[int]:
        """获取角色的权限ID列表"""
        role_permissions = db.query(AdminRolePermission).filter(
            AdminRolePermission.role_id == role_id,
            AdminRolePermission.is_deleted == False
        ).all()
        
        return [rp.permission_id for rp in role_permissions]
    
    @staticmethod
    def get_role_menus(db: Session, role_id: int) -> List[int]:
        """获取角色的菜单ID列表"""
        role_menus = db.query(AdminRoleMenu).filter(
            AdminRoleMenu.role_id == role_id,
            AdminRoleMenu.is_deleted == False
        ).all()
        
        return [rm.menu_id for rm in role_menus]
    
    @staticmethod
    def get_by_ids(db: Session, role_ids: List[int]) -> List[AdminRole]:
        """根据ID列表获取角色"""
        return db.query(AdminRole).filter(
            AdminRole.id.in_(role_ids),
            AdminRole.is_deleted == False
        ).all()







