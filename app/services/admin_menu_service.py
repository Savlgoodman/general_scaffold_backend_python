"""
管理员菜单服务层
处理管理员菜单相关的业务逻辑
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.admin_menu import AdminMenu
from app.schemas.admin_menu import AdminMenuCreate, AdminMenuUpdate, AdminMenuTreeNode
from app.core.logger import app_logger


class AdminMenuService:
    """管理员菜单服务"""
    
    @staticmethod
    def get_by_id(db: Session, menu_id: int) -> Optional[AdminMenu]:
        """根据ID获取菜单"""
        return db.query(AdminMenu).filter(
            AdminMenu.id == menu_id,
            AdminMenu.is_deleted == False
        ).first()
    
    @staticmethod
    def get_list(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None,
        status: Optional[int] = None,
        parent_id: Optional[int] = None,
    ) -> tuple[List[AdminMenu], int]:
        """
        获取菜单列表
        
        Returns:
            (菜单列表, 总数)
        """
        query = db.query(AdminMenu).filter(AdminMenu.is_deleted == False)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    AdminMenu.name.like(f"%{keyword}%"),
                    AdminMenu.path.like(f"%{keyword}%"),
                )
            )
        
        # 状态筛选
        if status is not None:
            query = query.filter(AdminMenu.status == status)
        
        # 父菜单筛选
        if parent_id is not None:
            query = query.filter(AdminMenu.parent_id == parent_id)
        
        # 获取总数
        total = query.count()
        
        # 分页
        menus = query.order_by(AdminMenu.sort.asc(), AdminMenu.created_at.desc()).offset(skip).limit(limit).all()
        
        return menus, total
    
    @staticmethod
    def get_all_active(db: Session) -> List[AdminMenu]:
        """获取所有激活的菜单"""
        return db.query(AdminMenu).filter(
            AdminMenu.is_deleted == False,
            AdminMenu.status == 1
        ).order_by(AdminMenu.sort.asc()).all()
    
    @staticmethod
    def create(db: Session, menu_in: AdminMenuCreate) -> AdminMenu:
        """创建菜单"""
        # 如果有父菜单，检查父菜单是否存在
        if menu_in.parent_id > 0:
            parent_menu = AdminMenuService.get_by_id(db, menu_in.parent_id)
            if not parent_menu:
                raise ValueError("父菜单不存在")
            
            # 检查父菜单是否已经是二级菜单（不允许三级菜单）
            if parent_menu.parent_id > 0:
                raise ValueError("不允许创建三级菜单")
        
        # 创建菜单
        menu = AdminMenu(
            name=menu_in.name,
            path=menu_in.path,
            parent_id=menu_in.parent_id,
            sort=menu_in.sort,
            remark=menu_in.remark,
            status=menu_in.status,
        )
        
        db.add(menu)
        db.commit()
        db.refresh(menu)
        
        app_logger.info(f"创建菜单成功: {menu.name}")
        
        return menu
    
    @staticmethod
    def update(db: Session, menu_id: int, menu_in: AdminMenuUpdate) -> Optional[AdminMenu]:
        """更新菜单"""
        menu = AdminMenuService.get_by_id(db, menu_id)
        if not menu:
            return None
        
        # 更新字段
        update_data = menu_in.model_dump(exclude_unset=True)
        
        # 如果修改了父菜单，检查父菜单是否存在
        if "parent_id" in update_data and update_data["parent_id"] > 0:
            parent_menu = AdminMenuService.get_by_id(db, update_data["parent_id"])
            if not parent_menu:
                raise ValueError("父菜单不存在")
            
            # 不能将菜单设置为自己的子菜单
            if update_data["parent_id"] == menu_id:
                raise ValueError("不能将菜单设置为自己的子菜单")
            
            # 检查父菜单是否已经是二级菜单（不允许三级菜单）
            if parent_menu.parent_id > 0:
                raise ValueError("不允许创建三级菜单")
        
        for field, value in update_data.items():
            setattr(menu, field, value)
        
        menu.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(menu)
        
        app_logger.info(f"更新菜单成功: {menu.name}")
        
        return menu
    
    @staticmethod
    def delete(db: Session, menu_id: int) -> bool:
        """逻辑删除菜单"""
        menu = AdminMenuService.get_by_id(db, menu_id)
        if not menu:
            return False
        
        # 检查是否有子菜单
        children = db.query(AdminMenu).filter(
            AdminMenu.parent_id == menu_id,
            AdminMenu.is_deleted == False
        ).first()
        
        if children:
            raise ValueError("该菜单下有子菜单，无法删除")
        
        menu.is_deleted = True
        menu.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        app_logger.info(f"逻辑删除菜单成功: {menu.name}")
        
        return True
    
    @staticmethod
    def build_menu_tree(menus: List[AdminMenu]) -> List[AdminMenuTreeNode]:
        """构建菜单树"""
        # 将菜单列表转换为字典，方便查找
        menu_dict: Dict[int, AdminMenuTreeNode] = {}
        for menu in menus:
            menu_dict[menu.id] = AdminMenuTreeNode(
                id=menu.id,
                name=menu.name,
                path=menu.path,
                parent_id=menu.parent_id,
                sort=menu.sort,
                remark=menu.remark,
                status=menu.status,
                children=[]
            )
        
        # 构建树形结构
        tree: List[AdminMenuTreeNode] = []
        for menu in menus:
            node = menu_dict[menu.id]
            if menu.parent_id == 0:
                # 顶级菜单
                tree.append(node)
            else:
                # 子菜单
                if menu.parent_id in menu_dict:
                    menu_dict[menu.parent_id].children.append(node)
        
        return tree
    
    @staticmethod
    def get_menu_tree(db: Session, status: Optional[int] = None) -> List[AdminMenuTreeNode]:
        """获取菜单树"""
        query = db.query(AdminMenu).filter(AdminMenu.is_deleted == False)
        
        if status is not None:
            query = query.filter(AdminMenu.status == status)
        
        menus = query.order_by(AdminMenu.sort.asc()).all()
        
        return AdminMenuService.build_menu_tree(menus)
    
    @staticmethod
    def get_by_ids(db: Session, menu_ids: List[int]) -> List[AdminMenu]:
        """根据ID列表获取菜单"""
        return db.query(AdminMenu).filter(
            AdminMenu.id.in_(menu_ids),
            AdminMenu.is_deleted == False
        ).order_by(AdminMenu.sort.asc()).all()







