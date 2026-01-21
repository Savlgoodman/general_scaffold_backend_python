"""
管理员用户服务层
处理管理员用户相关的业务逻辑
"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.admin_user import AdminUser
from app.schemas.admin_user import AdminUserCreate, AdminUserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.logger import app_logger


class AdminUserService:
    """管理员用户服务"""
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[AdminUser]:
        """
        根据ID获取管理员用户
        """
        return db.query(AdminUser).filter(
            AdminUser.id == user_id,
            AdminUser.is_deleted == False
        ).first()
    
    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[AdminUser]:
        """
        根据用户名获取管理员用户
        """
        return db.query(AdminUser).filter(
            AdminUser.username == username,
            AdminUser.is_deleted == False
        ).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[AdminUser]:
        """
        根据邮箱获取管理员用户
        """
        return db.query(AdminUser).filter(
            AdminUser.email == email,
            AdminUser.is_deleted == False
        ).first()
    
    @staticmethod
    def get_list(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[AdminUser], int]:
        """
        获取管理员用户列表
        
        Returns:
            (管理员用户列表, 总数)
        """
        query = db.query(AdminUser).filter(AdminUser.is_deleted == False)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    AdminUser.username.like(f"%{keyword}%"),
                    AdminUser.email.like(f"%{keyword}%"),
                    AdminUser.full_name.like(f"%{keyword}%"),
                )
            )
        
        # 状态筛选
        if is_active is not None:
            query = query.filter(AdminUser.is_active == is_active)
        
        # 获取总数
        total = query.count()
        
        # 分页
        users = query.order_by(AdminUser.created_at.desc()).offset(skip).limit(limit).all()
        
        return users, total
    
    @staticmethod
    def create(db: Session, user_in: AdminUserCreate) -> AdminUser:
        """
        创建管理员用户
        """
        # 检查用户名是否存在
        if AdminUserService.get_by_username(db, user_in.username):
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否存在
        if AdminUserService.get_by_email(db, user_in.email):
            raise ValueError("邮箱已存在")
        
        # 创建管理员用户
        user = AdminUser(
            username=user_in.username,
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            phone=user_in.phone,
            avatar=user_in.avatar,
            is_active=user_in.is_active,
            is_superuser=user_in.is_superuser,
            remark=user_in.remark,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 分配角色
        if user_in.role_ids:
            from app.services.admin_rbac_service import AdminRBACService
            AdminRBACService.assign_user_roles(db, user.id, user_in.role_ids)
        
        app_logger.info(f"创建管理员用户成功: {user.username}")
        
        return user
    
    @staticmethod
    def update(db: Session, user_id: int, user_in: AdminUserUpdate) -> Optional[AdminUser]:
        """
        更新管理员用户
        """
        user = AdminUserService.get_by_id(db, user_id)
        if not user:
            return None
        
        # 更新字段
        update_data = user_in.model_dump(exclude_unset=True)
        
        # 检查邮箱是否被其他用户使用
        if "email" in update_data:
            existing_user = AdminUserService.get_by_email(db, update_data["email"])
            if existing_user and existing_user.id != user_id:
                raise ValueError("邮箱已被使用")
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user)
        
        app_logger.info(f"更新管理员用户成功: {user.username}")
        
        return user
    
    @staticmethod
    def delete(db: Session, user_id: int) -> bool:
        """
        逻辑删除管理员用户
        """
        user = AdminUserService.get_by_id(db, user_id)
        if not user:
            return False
        
        user.is_deleted = True
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        app_logger.info(f"逻辑删除管理员用户成功: {user.username}")
        
        return True
    
    @staticmethod
    def change_password(
        db: Session,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        修改密码
        """
        user = AdminUserService.get_by_id(db, user_id)
        if not user:
            return False
        
        # 验证旧密码
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("旧密码错误")
        
        # 更新密码
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        app_logger.info(f"管理员用户修改密码成功: {user.username}")
        
        return True
    
    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[AdminUser]:
        """
        验证管理员用户登录
        """
        user = AdminUserService.get_by_username(db, username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # 检查是否已被删除
        if user.is_deleted:
            return None
        
        # 更新最后登录时间
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        
        return user


