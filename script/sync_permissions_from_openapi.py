#!/usr/bin/env python
"""
从FastAPI应用的OpenAPI规范同步权限到数据库

使用方法:
    python script/sync_permissions_from_openapi.py [--dry-run] [--verbose]

参数:
    --dry-run   预览模式，不实际修改数据库
    --verbose   详细输出

同步逻辑:
1. 从OpenAPI提取所有API路径
2. 对比数据库中的权限:
   - 数据库中不存在的 -> 新增
   - 数据库中存在的 -> 不变
   - 数据库中存在但OpenAPI中没有的 -> 删除（软删除）
3. 组权限处理:
   - 取所有API路径的前三段（如 /api/admin/system_info）
   - 去重后生成组权限
   - 同样执行新增、不变、删除的逻辑
"""
import sys
import argparse
from pathlib import Path
from typing import List, Set, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.core.database import SessionLocal
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
    permissions_added: int
    permissions_unchanged: int
    permissions_deleted: int
    groups_added: int
    groups_unchanged: int
    groups_deleted: int
    errors: List[str]


def get_app() -> FastAPI:
    """获取FastAPI应用实例"""
    from main import app
    return app


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


def convert_path_params_to_wildcard(path: str) -> str:
    """
    将路径末尾的路径参数转换为通配符
    
    例如:
    - /api/admin/users/detail/{user_id} -> /api/admin/users/detail/*
    - /api/admin/roles/{role_id}/permissions -> /api/admin/roles/*/permissions
    """
    import re
    # 匹配 {xxx} 格式的路径参数
    return re.sub(r'/\{[a-z_]+\}', '/*', path)


def extract_group_prefix(path: str) -> str:
    """
    提取路径的前三段作为组权限前缀
    
    例如:
    - /api/admin/system_info/resources -> /api/admin/system_info
    - /api/admin/users/list -> /api/admin/users
    - /api/admin/roles/{role_id}/permissions -> /api/admin/roles
    """
    # 去掉路径参数，只保留静态部分
    import re
    clean_path = re.sub(r'/\{[a-z_]+\}', '', path)
    
    parts = clean_path.strip("/").split("/")
    # 取前三段
    if len(parts) >= 3:
        return "/" + "/".join(parts[:3])
    elif len(parts) >= 1:
        return "/" + "/".join(parts)
    return path


def generate_group_key(prefix: str) -> str:
    """
    从前缀生成 group_key
    
    例如:
    - /api/admin/system_info -> admin.system_info
    - /api/admin/users -> admin.users
    """
    parts = prefix.strip("/").split("/")
    # 跳过 api 前缀
    if parts and parts[0] == "api":
        parts = parts[1:]
    return ".".join(parts)


def generate_group_name(group_key: str) -> str:
    """从 group_key 生成可读的组名称"""
    parts = group_key.replace(".", " ").replace("_", " ").split()
    return " ".join(part.capitalize() for part in parts)


def sync_permissions(
    db: Session, 
    routes: List[RouteInfo], 
    dry_run: bool = False,
    verbose: bool = False
) -> SyncResult:
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
        permissions_added=0,
        permissions_unchanged=0,
        permissions_deleted=0,
        groups_added=0,
        groups_unchanged=0,
        groups_deleted=0,
        errors=[]
    )
    
    # ========== 处理子权限（非组权限）==========
    
    # 1. 从OpenAPI提取所有权限（resource_pattern + method）
    openapi_permissions: Dict[Tuple[str, str], RouteInfo] = {}
    group_prefixes: Set[str] = set()
    
    for route in routes:
        resource_pattern = convert_path_params_to_wildcard(route.path)
        key = (resource_pattern, route.method)
        openapi_permissions[key] = route
        
        # 提取组前缀
        prefix = extract_group_prefix(route.path)
        group_prefixes.add(prefix)
    
    if verbose:
        print(f"\n从OpenAPI提取到 {len(openapi_permissions)} 个权限")
        print(f"提取到 {len(group_prefixes)} 个组前缀:")
        for prefix in sorted(group_prefixes):
            print(f"  - {prefix}")
    
    # 2. 获取数据库中所有非组权限
    db_permissions = db.query(AdminPermission).filter(
        AdminPermission.is_group == False,
        AdminPermission.is_deleted == False
    ).all()
    
    db_permission_map: Dict[Tuple[str, str], AdminPermission] = {
        (p.resource_pattern, p.method): p for p in db_permissions
    }
    
    if verbose:
        print(f"\n数据库中有 {len(db_permissions)} 个非组权限")
    
    # 3. 对比并同步
    # 3.1 新增: OpenAPI有，数据库没有
    for key, route in openapi_permissions.items():
        resource_pattern, method = key
        
        if key not in db_permission_map:
            # 生成 group_key
            prefix = extract_group_prefix(route.path)
            group_key = generate_group_key(prefix)
            group_name = generate_group_name(group_key)
            
            if not dry_run:
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
            
            result.permissions_added += 1
            if verbose:
                print(f"  [新增] {method} {resource_pattern}")
        else:
            # 更新 group_key（如果需要）
            existing = db_permission_map[key]
            prefix = extract_group_prefix(route.path)
            group_key = generate_group_key(prefix)
            group_name = generate_group_name(group_key)
            
            if existing.group_key != group_key or existing.group_name != group_name:
                if not dry_run:
                    existing.group_key = group_key
                    existing.group_name = group_name
                    existing.updated_at = datetime.now(timezone.utc)
                if verbose:
                    print(f"  [更新] {method} {resource_pattern} -> group: {group_key}")
            
            result.permissions_unchanged += 1
    
    # 3.2 删除: 数据库有，OpenAPI没有
    for key, perm in db_permission_map.items():
        if key not in openapi_permissions:
            if not dry_run:
                perm.is_deleted = True
                perm.updated_at = datetime.now(timezone.utc)
            
            result.permissions_deleted += 1
            if verbose:
                print(f"  [删除] {perm.method} {perm.resource_pattern}")
    
    if not dry_run:
        db.commit()
    
    # ========== 处理组权限 ==========
    
    # 4. 生成组权限
    # 组权限的 resource_pattern 是前缀 + /**
    openapi_groups: Dict[str, str] = {}  # {resource_pattern: group_key}
    
    for prefix in group_prefixes:
        resource_pattern = prefix + "/**"
        group_key = generate_group_key(prefix)
        openapi_groups[resource_pattern] = group_key
    
    if verbose:
        print(f"\n需要的组权限 ({len(openapi_groups)} 个):")
        for pattern, gk in sorted(openapi_groups.items()):
            print(f"  - {pattern} (group_key: {gk})")
    
    # 5. 获取数据库中所有组权限
    db_groups = db.query(AdminPermission).filter(
        AdminPermission.is_group == True,
        AdminPermission.is_deleted == False
    ).all()
    
    db_group_map: Dict[str, AdminPermission] = {
        g.resource_pattern: g for g in db_groups
    }
    
    if verbose:
        print(f"\n数据库中有 {len(db_groups)} 个组权限")
    
    # 6. 对比并同步组权限
    # 6.1 新增: OpenAPI有，数据库没有
    for resource_pattern, group_key in openapi_groups.items():
        if resource_pattern not in db_group_map:
            group_name = generate_group_name(group_key)
            
            if not dry_run:
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
            
            result.groups_added += 1
            if verbose:
                print(f"  [新增组] {resource_pattern} (group_key: {group_key})")
        else:
            # 检查是否需要更新 group_key
            existing = db_group_map[resource_pattern]
            group_name = generate_group_name(group_key)
            
            if existing.group_key != group_key or existing.group_name != group_name:
                if not dry_run:
                    existing.group_key = group_key
                    existing.group_name = group_name
                    existing.updated_at = datetime.now(timezone.utc)
                if verbose:
                    print(f"  [更新组] {resource_pattern} -> group_key: {group_key}")
            
            result.groups_unchanged += 1
    
    # 6.2 删除: 数据库有，OpenAPI没有
    for resource_pattern, perm in db_group_map.items():
        if resource_pattern not in openapi_groups:
            if not dry_run:
                perm.is_deleted = True
                perm.updated_at = datetime.now(timezone.utc)
            
            result.groups_deleted += 1
            if verbose:
                print(f"  [删除组] {resource_pattern}")
    
    if not dry_run:
        db.commit()
    
    return result



def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="从OpenAPI同步权限到数据库")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际修改数据库")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    args = parser.parse_args()
    
    print("=" * 60)
    print("权限同步脚本")
    print("=" * 60)
    
    if args.dry_run:
        print("[预览模式] 不会实际修改数据库")
    
    # 1. 加载FastAPI应用
    print("\n正在加载FastAPI应用...")
    try:
        app = get_app()
        print(f"✓ 应用加载成功: {app.title}")
    except Exception as e:
        print(f"✗ 应用加载失败: {e}")
        sys.exit(1)
    
    # 2. 提取路由
    print("\n正在提取路由...")
    routes = extract_routes_from_app(app)
    print(f"✓ 提取到 {len(routes)} 个路由")
    
    if args.verbose:
        print("\n路由列表:")
        for route in routes:
            resource_pattern = convert_path_params_to_wildcard(route.path)
            prefix = extract_group_prefix(route.path)
            group_key = generate_group_key(prefix)
            print(f"  [{route.method}] {resource_pattern} -> group: {group_key}")
    
    # 3. 连接数据库
    print("\n正在连接数据库...")
    try:
        db = SessionLocal()
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        sys.exit(1)
    
    # 4. 同步权限
    print("\n正在同步权限...")
    try:
        result = sync_permissions(db, routes, dry_run=args.dry_run, verbose=args.verbose)
        
        print("\n" + "=" * 60)
        print("同步结果:")
        print("=" * 60)
        print(f"  子权限:")
        print(f"    - 新增: {result.permissions_added}")
        print(f"    - 不变: {result.permissions_unchanged}")
        print(f"    - 删除: {result.permissions_deleted}")
        print(f"  组权限:")
        print(f"    - 新增: {result.groups_added}")
        print(f"    - 不变: {result.groups_unchanged}")
        print(f"    - 删除: {result.groups_deleted}")
        
        if result.errors:
            print(f"\n错误 ({len(result.errors)}):")
            for error in result.errors:
                print(f"  - {error}")
        
        if args.dry_run:
            print("\n[预览模式] 以上为预览结果，使用不带 --dry-run 参数运行以实际同步")
        else:
            print("\n✓ 同步完成!")
        
    except Exception as e:
        print(f"✗ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
