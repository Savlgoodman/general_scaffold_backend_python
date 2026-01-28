"""
权限同步服务
从FastAPI应用的OpenAPI规范自动同步权限

注意: 主要的同步逻辑已移至 script/sync_permissions_from_openapi.py
此文件保留一些辅助方法供其他模块使用
"""
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import FastAPI
from fastapi.routing import APIRoute
import re

from app.models.admin_permission import AdminPermission
from app.core.logger import app_logger


@dataclass
class RouteInfo:
    """路由信息"""
    path: str
    method: str
    tags: List[str]
    summary: str
    name: str


@dataclass
class SyncResult:
    """同步结果"""
    added: int
    updated: int
    unchanged: int
    group_permissions_created: int
    deleted: int
    errors: List[str]


class PermissionSyncService:
    """权限同步服务"""
    
    @staticmethod
    def convert_path_params_to_wildcard(path: str) -> str:
        """
        将路径中的路径参数转换为通配符
        
        例如:
        - /api/admin/users/detail/{user_id} -> /api/admin/users/detail/*
        - /api/admin/roles/{role_id}/permissions -> /api/admin/roles/*/permissions
        """
        return re.sub(r'/\{[a-z_]+\}', '/*', path)
    
    @staticmethod
    def extract_group_prefix(path: str) -> str:
        """
        提取路径的前三段作为组权限前缀
        
        例如:
        - /api/admin/system_info/resources -> /api/admin/system_info
        - /api/admin/users/list -> /api/admin/users
        """
        # 去掉路径参数
        clean_path = re.sub(r'/\{[a-z_]+\}', '', path)
        parts = clean_path.strip("/").split("/")
        
        if len(parts) >= 3:
            return "/" + "/".join(parts[:3])
        elif len(parts) >= 1:
            return "/" + "/".join(parts)
        return path
    
    @staticmethod
    def extract_routes_from_app(app: FastAPI) -> List[RouteInfo]:
        """从FastAPI应用提取所有路由信息"""
        routes = []
        
        for route in app.routes:
            if isinstance(route, APIRoute):
                methods = list(route.methods - {"HEAD", "OPTIONS"})
                
                for method in methods:
                    route_info = RouteInfo(
                        path=route.path,
                        method=method,
                        tags=list(route.tags) if route.tags else [],
                        summary=route.summary or route.name or "",
                        name=route.name or ""
                    )
                    routes.append(route_info)
        
        return routes

    @staticmethod
    def generate_group_key(path: str, tags: List[str] = None) -> str:
        """
        从路径前缀生成分组标识
        
        例如:
        - /api/admin/system_info -> admin.system_info
        - /api/admin/users -> admin.users
        """
        prefix = PermissionSyncService.extract_group_prefix(path)
        parts = prefix.strip("/").split("/")
        
        # 跳过 api 前缀
        if parts and parts[0] == "api":
            parts = parts[1:]
        
        return ".".join(parts)
    
    @staticmethod
    def generate_group_name(group_key: str) -> str:
        """从分组标识生成分组名称"""
        parts = group_key.replace(".", " ").replace("_", " ").split()
        return " ".join(part.capitalize() for part in parts)
    
    @staticmethod
    def generate_wildcard_pattern(group_key: str) -> str:
        """
        从分组标识生成通配符模式
        
        例如:
        - admin.system_info -> /api/admin/system_info/**
        """
        parts = group_key.split(".")
        return "/api/" + "/".join(parts) + "/**"

    @staticmethod
    def sync_permissions(db: Session, routes: List[RouteInfo]) -> SyncResult:
        """
        同步权限到数据库
        
        逻辑:
        1. 从OpenAPI提取所有API路径
        2. 对比数据库:
           - 新增: OpenAPI有，数据库没有
           - 不变: 两边都有
           - 删除: 数据库有，OpenAPI没有
        """
        result = SyncResult(
            added=0,
            updated=0,
            unchanged=0,
            group_permissions_created=0,
            deleted=0,
            errors=[]
        )
        
        # ========== 处理子权限 ==========
        
        # 1. 从OpenAPI提取所有权限
        openapi_permissions: Dict[Tuple[str, str], RouteInfo] = {}
        group_prefixes: Set[str] = set()
        
        for route in routes:
            resource_pattern = PermissionSyncService.convert_path_params_to_wildcard(route.path)
            key = (resource_pattern, route.method)
            openapi_permissions[key] = route
            
            prefix = PermissionSyncService.extract_group_prefix(route.path)
            group_prefixes.add(prefix)
        
        # 2. 获取数据库中所有非组权限
        db_permissions = db.query(AdminPermission).filter(
            AdminPermission.is_group == False,
            AdminPermission.is_deleted == False
        ).all()
        
        db_permission_map: Dict[Tuple[str, str], AdminPermission] = {
            (p.resource_pattern, p.method): p for p in db_permissions
        }
        
        # 3. 同步子权限
        for key, route in openapi_permissions.items():
            resource_pattern, method = key
            
            if key not in db_permission_map:
                # 新增
                group_key = PermissionSyncService.generate_group_key(route.path)
                group_name = PermissionSyncService.generate_group_name(group_key)
                
                permission = AdminPermission(
                    name=route.summary or route.name or route.path,
                    resource_pattern=resource_pattern,
                    method=method,
                    group_key=group_key,
                    group_name=group_name,
                    is_group=False,
                    description=f"从OpenAPI同步: {route.name}",
                    status=1
                )
                db.add(permission)
                result.added += 1
            else:
                # 检查是否需要更新
                existing = db_permission_map[key]
                group_key = PermissionSyncService.generate_group_key(route.path)
                group_name = PermissionSyncService.generate_group_name(group_key)
                
                needs_update = False
                if existing.group_key != group_key:
                    existing.group_key = group_key
                    needs_update = True
                if existing.group_name != group_name:
                    existing.group_name = group_name
                    needs_update = True
                
                if needs_update:
                    existing.updated_at = datetime.now(timezone.utc)
                    result.updated += 1
                else:
                    result.unchanged += 1
        
        # 删除数据库中多余的权限
        for key, perm in db_permission_map.items():
            if key not in openapi_permissions:
                perm.is_deleted = True
                perm.updated_at = datetime.now(timezone.utc)
                result.deleted += 1
        
        db.commit()
        
        # ========== 处理组权限 ==========
        
        openapi_groups: Dict[str, str] = {}
        for prefix in group_prefixes:
            resource_pattern = prefix + "/**"
            group_key = PermissionSyncService.generate_group_key(prefix + "/dummy")
            # 修正 group_key（去掉 dummy）
            parts = group_key.split(".")
            if parts and parts[-1] == "dummy":
                parts = parts[:-1]
            group_key = ".".join(parts)
            openapi_groups[resource_pattern] = group_key
        
        db_groups = db.query(AdminPermission).filter(
            AdminPermission.is_group == True,
            AdminPermission.is_deleted == False
        ).all()
        
        db_group_map: Dict[str, AdminPermission] = {
            g.resource_pattern: g for g in db_groups
        }
        
        # 新增组权限
        for resource_pattern, group_key in openapi_groups.items():
            if resource_pattern not in db_group_map:
                group_name = PermissionSyncService.generate_group_name(group_key)
                
                permission = AdminPermission(
                    name=f"{group_name} 全部权限",
                    resource_pattern=resource_pattern,
                    method="*",
                    group_key=group_key,
                    group_name=group_name,
                    is_group=True,
                    description=f"自动生成的组权限，匹配 {resource_pattern}",
                    status=1
                )
                db.add(permission)
                result.group_permissions_created += 1
        
        # 删除多余的组权限
        for resource_pattern, perm in db_group_map.items():
            if resource_pattern not in openapi_groups:
                perm.is_deleted = True
                perm.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        app_logger.info(
            f"权限同步完成: 新增 {result.added}, 更新 {result.updated}, "
            f"未变更 {result.unchanged}, 删除 {result.deleted}, "
            f"组权限 {result.group_permissions_created}"
        )
        
        return result
