"""
管理员权限服务层
处理管理员权限相关的业务逻辑
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_
import fnmatch

from app.models.admin_permission import AdminPermission
from app.schemas.admin_permission import AdminPermissionCreate, AdminPermissionUpdate
from app.core.logger import app_logger


class AdminPermissionService:
    """管理员权限服务"""
    
    @staticmethod
    def match_pattern(pattern: str, path: str) -> bool:
        """
        匹配资源模式
        
        支持的通配符：
        - * : 匹配任意字符（单个路径段）
        - ** : 匹配任意字符（包括多个路径段）
        - ? : 匹配单个字符
        
        示例：
        - /system/logs/* 匹配 /system/logs/list, /system/logs/123
        - /system/** 匹配 /system/logs/list, /system/a/b/c
        - /system/logs/? 匹配 /system/logs/1
        
        Args:
            pattern: 资源模式
            path: 请求路径
            
        Returns:
            是否匹配
        """
        # 处理 ** 通配符（匹配多个路径段）
        if '**' in pattern:
            # 将 ** 替换为特殊标记，然后转换为正则表达式
            import re
            regex_pattern = pattern.replace('**', '<<<DOUBLE_STAR>>>')
            regex_pattern = re.escape(regex_pattern)
            regex_pattern = regex_pattern.replace('<<<DOUBLE_STAR>>>', '.*')
            regex_pattern = regex_pattern.replace(r'\*', '[^/]*')
            regex_pattern = regex_pattern.replace(r'\?', '[^/]')
            regex_pattern = f'^{regex_pattern}$'
            return bool(re.match(regex_pattern, path))
        
        # 使用 fnmatch 处理单个 * 和 ? 通配符
        return fnmatch.fnmatch(path, pattern)
    
    @staticmethod
    def is_pattern_subset(parent_pattern: str, child_pattern: str) -> bool:
        """
        判断子权限模式是否属于父权限模式的范围
        
        例如：
        - /api/admin/users/** 包含 /api/admin/users/list
        - /api/admin/users/** 包含 /api/admin/users/detail/*
        - /api/admin/users/* 不包含 /api/admin/users/detail/123
        
        Args:
            parent_pattern: 父权限模式（通常是组权限）
            child_pattern: 子权限模式
            
        Returns:
            子权限是否属于父权限范围
        """
        # 如果父模式以 /** 结尾，检查子模式是否以相同前缀开头
        if parent_pattern.endswith('/**'):
            prefix = parent_pattern[:-3]  # 去掉 /**
            # 子模式必须以相同前缀开头
            if child_pattern.startswith(prefix + '/') or child_pattern == prefix:
                return True
            return False
        
        # 如果父模式以 /* 结尾，检查子模式是否在同一层级
        if parent_pattern.endswith('/*'):
            prefix = parent_pattern[:-2]  # 去掉 /*
            # 子模式必须以相同前缀开头，且只有一层
            if child_pattern.startswith(prefix + '/'):
                remaining = child_pattern[len(prefix) + 1:]
                # 剩余部分不能包含 /（除非是末尾的通配符）
                if '/' not in remaining or remaining.endswith('/*'):
                    return True
            return False
        
        # 精确匹配
        return parent_pattern == child_pattern
    
    @staticmethod
    def get_by_id(db: Session, permission_id: int) -> Optional[AdminPermission]:
        """根据ID获取权限"""
        return db.query(AdminPermission).filter(
            AdminPermission.id == permission_id,
            AdminPermission.is_deleted == False
        ).first()
    
    @staticmethod
    def get_by_api_path(db: Session, api_path: str) -> Optional[AdminPermission]:
        """
        根据API路径获取权限（支持向后兼容和通配符匹配）
        
        Args:
            db: 数据库会话
            api_path: API路径
            
        Returns:
            权限对象或None
        """
        # 首先尝试精确匹配 resource_pattern
        permission = db.query(AdminPermission).filter(
            AdminPermission.resource_pattern == api_path,
            AdminPermission.is_deleted == False
        ).first()
        
        if permission:
            return permission
        
        # 如果没有精确匹配，尝试通配符匹配
        all_permissions = db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False
        ).all()
        
        for perm in all_permissions:
            if AdminPermissionService.match_pattern(perm.resource_pattern, api_path):
                return perm
        
        return None
    
    @staticmethod
    def get_by_resource_pattern(db: Session, pattern: str) -> Optional[AdminPermission]:
        """
        根据资源模式精确查询
        
        Args:
            db: 数据库会话
            pattern: 资源模式
            
        Returns:
            权限对象或None
        """
        return db.query(AdminPermission).filter(
            AdminPermission.resource_pattern == pattern,
            AdminPermission.is_deleted == False
        ).first()
    
    @staticmethod
    def get_list(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None,
        status: Optional[int] = None,
        group_key: Optional[str] = None,
        is_group: Optional[bool] = None,
    ) -> tuple[List[AdminPermission], int]:
        """
        获取权限列表
        
        Args:
            db: 数据库会话
            skip: 跳过数量
            limit: 限制数量
            keyword: 关键词搜索
            status: 状态筛选
            group_key: 分组标识筛选
            is_group: 是否组权限筛选
            
        Returns:
            (权限列表, 总数)
        """
        query = db.query(AdminPermission).filter(AdminPermission.is_deleted == False)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    AdminPermission.name.like(f"%{keyword}%"),
                    AdminPermission.resource_pattern.like(f"%{keyword}%"),
                )
            )
        
        # 状态筛选
        if status is not None:
            query = query.filter(AdminPermission.status == status)
        
        # 分组标识筛选
        if group_key is not None:
            query = query.filter(AdminPermission.group_key == group_key)
        
        # 是否组权限筛选
        if is_group is not None:
            query = query.filter(AdminPermission.is_group == is_group)
        
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
    def get_grouped_permissions(db: Session) -> Dict[str, List[AdminPermission]]:
        """
        按分组返回权限
        
        Args:
            db: 数据库会话
            
        Returns:
            按 group_key 分组的权限字典
        """
        permissions = db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1
        ).all()
        
        grouped: Dict[str, List[AdminPermission]] = {}
        
        for perm in permissions:
            group_key = perm.group_key or "未分组"
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(perm)
        
        return grouped
    
    @staticmethod
    def create(db: Session, permission_in: AdminPermissionCreate) -> AdminPermission:
        """
        创建权限
        
        Args:
            db: 数据库会话
            permission_in: 权限创建数据
            
        Returns:
            创建的权限对象
        """
        # 检查资源模式是否存在
        if AdminPermissionService.get_by_resource_pattern(db, permission_in.resource_pattern):
            raise ValueError(f"资源模式已存在: {permission_in.resource_pattern}")
        
        # 自动检测通配符并设置 is_group
        is_group = permission_in.is_group
        if '*' in permission_in.resource_pattern or '?' in permission_in.resource_pattern:
            is_group = True
        
        # 创建权限
        permission = AdminPermission(
            name=permission_in.name,
            resource_pattern=permission_in.resource_pattern,
            method=permission_in.method,
            group_key=permission_in.group_key,
            group_name=permission_in.group_name,
            is_group=is_group,
            description=permission_in.description,
            status=permission_in.status,
        )
        
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        app_logger.info(f"创建权限成功: {permission.name}")
        
        return permission
    
    @staticmethod
    def update(db: Session, permission_id: int, permission_in: AdminPermissionUpdate) -> Optional[AdminPermission]:
        """
        更新权限
        
        Args:
            db: 数据库会话
            permission_id: 权限ID
            permission_in: 权限更新数据
            
        Returns:
            更新后的权限对象或None
        """
        permission = AdminPermissionService.get_by_id(db, permission_id)
        if not permission:
            return None
        
        # 更新字段
        update_data = permission_in.model_dump(exclude_unset=True)
        
        # 检查资源模式是否被其他权限使用
        if "resource_pattern" in update_data:
            existing_permission = AdminPermissionService.get_by_resource_pattern(db, update_data["resource_pattern"])
            if existing_permission and existing_permission.id != permission_id:
                raise ValueError(f"资源模式已被使用: {update_data['resource_pattern']}")
        
        # 如果更新了 resource_pattern，自动检测通配符
        if "resource_pattern" in update_data:
            if '*' in update_data["resource_pattern"] or '?' in update_data["resource_pattern"]:
                update_data["is_group"] = True
        
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
    
    # ==================== 向后兼容适配器方法 ====================
    
    @staticmethod
    def get_by_api_path_legacy(db: Session, api_path: str) -> Optional[AdminPermission]:
        """
        向后兼容的API路径查询方法
        同时支持查询 resource_pattern（新字段）
        
        Args:
            db: 数据库会话
            api_path: API路径
            
        Returns:
            权限对象或None
        """
        # 使用新的 get_by_api_path 方法，它已经支持双重查询
        return AdminPermissionService.get_by_api_path(db, api_path)
    
    @staticmethod
    def find_matching_permissions(db: Session, api_path: str, method: str = "POST") -> List[AdminPermission]:
        """
        查找所有匹配指定路径的权限（包括通配符匹配）
        
        Args:
            db: 数据库会话
            api_path: API路径
            method: HTTP方法
            
        Returns:
            匹配的权限列表
        """
        all_permissions = db.query(AdminPermission).filter(
            AdminPermission.is_deleted == False,
            AdminPermission.status == 1,
            or_(
                AdminPermission.method == method,
                AdminPermission.method == "*"  # 组权限使用 * 匹配所有方法
            )
        ).all()
        
        matched = []
        for perm in all_permissions:
            # 精确匹配
            if perm.resource_pattern == api_path:
                matched.append(perm)
            # 通配符匹配
            elif AdminPermissionService.match_pattern(perm.resource_pattern, api_path):
                matched.append(perm)
        
        return matched
    
    @staticmethod
    def convert_to_legacy_format(permission: AdminPermission) -> dict:
        """
        将新格式权限转换为旧格式（用于向后兼容）
        
        Args:
            permission: 权限对象
            
        Returns:
            旧格式的权限字典
        """
        return {
            "id": permission.id,
            "name": permission.name,
            "api_path": permission.resource_pattern,  # 映射到旧字段名
            "remark": permission.description,  # 映射到旧字段名
            "status": permission.status,
            "created_at": permission.created_at,
            "updated_at": permission.updated_at,
            # 新字段也包含
            "resource_pattern": permission.resource_pattern,
            "method": permission.method,
            "group_key": permission.group_key,
            "group_name": permission.group_name,
            "is_group": permission.is_group,
            "description": permission.description,
        }

