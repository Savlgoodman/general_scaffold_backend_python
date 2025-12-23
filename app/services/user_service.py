"""
用户服务层
处理用户相关的业务逻辑
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.logger import app_logger


class UserService:
    """用户服务"""
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        根据ID获取用户
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        """
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        """
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_list(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[User], int]:
        """
        获取用户列表
        
        Returns:
            (用户列表, 总数)
        """
        query = db.query(User)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    User.username.like(f"%{keyword}%"),
                    User.email.like(f"%{keyword}%"),
                    User.full_name.like(f"%{keyword}%"),
                )
            )
        
        # 状态筛选
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # 获取总数
        total = query.count()
        
        # 分页
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        return users, total
    
    @staticmethod
    def create(db: Session, user_in: UserCreate) -> User:
        """
        创建用户
        """
        # 检查用户名是否存在
        if UserService.get_by_username(db, user_in.username):
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否存在
        if UserService.get_by_email(db, user_in.email):
            raise ValueError("邮箱已存在")
        
        # 创建用户
        user = User(
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
        
        app_logger.info(f"创建用户成功: {user.username}")
        
        return user
    
    @staticmethod
    def update(db: Session, user_id: int, user_in: UserUpdate) -> Optional[User]:
        """
        更新用户
        """
        user = UserService.get_by_id(db, user_id)
        if not user:
            return None
        
        # 更新字段
        update_data = user_in.model_dump(exclude_unset=True)
        
        # 检查邮箱是否被其他用户使用
        if "email" in update_data:
            existing_user = UserService.get_by_email(db, update_data["email"])
            if existing_user and existing_user.id != user_id:
                raise ValueError("邮箱已被使用")
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        app_logger.info(f"更新用户成功: {user.username}")
        
        return user
    
    @staticmethod
    def delete(db: Session, user_id: int) -> bool:
        """
        删除用户
        """
        user = UserService.get_by_id(db, user_id)
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        
        app_logger.info(f"删除用户成功: {user.username}")
        
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
        user = UserService.get_by_id(db, user_id)
        if not user:
            return False
        
        # 验证旧密码
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("旧密码错误")
        
        # 更新密码
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        app_logger.info(f"用户修改密码成功: {user.username}")
        
        return True
    
    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[User]:
        """
        验证用户登录
        """
        user = UserService.get_by_username(db, username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user


