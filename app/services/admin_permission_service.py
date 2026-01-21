"""
管理员权限服务层
处理管理员权限相关的业务逻辑
"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.admin_permission import AdminPermission
from app.schemas.admin_permission import AdminPermissionCreate, AdminPermissionUpdate
from app.core.logger import app_logger


class AdminPermissionService:
    """管理员权限服务"""
    
    @staticmethod
    def get_by_id(db: Session, permission_id: int) -> Optional[AdminPermission]:
        """根据ID获取权限"""
        return db.query(AdminPermission).filter(
            AdminPermission.id == permission_id,
            AdminPermission.is_deleted == False
        ).first()
    
    @staticmethod
    def get_by_api_path(db: Session, api_path: str) -> Optional[AdminPermission]:
        """根据API路径获取权限"""
        return db.query(AdminPermission).filter(
            AdminPermission.api_path == api_path,
            AdminPermission.is_deleted == False
        ).first()
    
    @staticmethod
    def get_list(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None,
        status: Optional[int] = None,
    ) -> tuple[List[AdminPermission], int]:
        """
        获取权限列表
        
        Returns:
            (权限列表, 总数)
        """
        query = db.query(AdminPermission).filter(AdminPermission.is_deleted == False)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    AdminPermission.name.like(f"%{keyword}%"),
                    AdminPermission.api_path.like(f"%{keyword}%"),
                )
            )
        
        # 状态筛选
        if status is not None:
            query = query.filter(AdminPermission.status == status)
        
        # 获取总数
        total = query.count()
        
        # 分页
        permissions = query.order_by(AdminPermission.created_at.desc()).offset(skip).limit(limit).all()
        
        return permissions, total
    
    @staticmethod
    def get_all_active(db: Session) -> List[AdminPermission]:
        """获取所有激活的权限"""
        return db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all()
    
    @staticmethod
    def create(db: Session, permission_in: AdminPermissionCreate) -> AdminPermission:
        """创建权限"""
        # 检查API路径是否存在
        if AdminPermissionService.get_by_api_path(db, permission_in.api_path):
            raise ValueError("API路径已存在")
        
        # 创建权限
        permission = AdminPermission(
            name=permission_in.name,
            api_path=permission_in.api_path,
            remark=permission_in.remark,
            status=permission_in.status,
        )
        
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        app_logger.info(f"创建权限成功: {permission.name}")
        
        return permission
    
    @staticmethod
    def update(db: Session, permission_id: int, permission_in: AdminPermissionUpdate) -> Optional[AdminPermission]:
        """更新权限"""
        permission = AdminPermissionService.get_by_id(db, permission_id)
        if not permission:
            return None
        
        # 更新字段
        update_data = permission_in.model_dump(exclude_unset=True)
        
        # 检查API路径是否被其他权限使用
        if "api_path" in update_data:
            existing_permission = AdminPermissionService.get_by_api_path(db, update_data["api_path"])
            if existing_permission and existing_permission.id != permission_id:
                raise ValueError("API路径已被使用")
        
        for field, value in update_data.items():
            setattr(permission, field, value)
        
        permission.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(permission)
        
        app_logger.info(f"更新权限成功: {permission.name}")
        
        return permission
    
    @staticmethod
    def delete(db: Session, permission_id: int) -> bool:
        """逻辑删除权限"""
        permission = AdminPermissionService.get_by_id(db, permission_id)
        if not permission:
            return False
        
        permission.is_deleted = True
        permission.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        app_logger.info(f"逻辑删除权限成功: {permission.name}")
        
        return True
    
    @staticmethod
    def get_by_ids(db: Session, permission_ids: List[int]) -> List[AdminPermission]:
        """根据ID列表获取权限"""
        return db.query(AdminPermission).filter(
            AdminPermission.id.in_(permission_ids),
            AdminPermission.is_deleted == False
        ).all()

