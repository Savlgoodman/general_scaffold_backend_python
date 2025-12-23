"""
初始化脚本
创建初始管理员用户
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, init_db
from app.core.security import get_password_hash
from app.models.user import User
from app.core.logger import app_logger


def create_superuser():
    """
    创建超级管理员用户
    """
    # 初始化数据库
    init_db()
    
    db = SessionLocal()
    
    try:
        # 检查是否已存在管理员
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            app_logger.info("管理员用户已存在")
            return
        
        # 创建管理员用户
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="系统管理员",
            is_active=True,
            is_superuser=True,
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        app_logger.info("=" * 50)
        app_logger.info("管理员用户创建成功！")
        app_logger.info(f"用户名: {admin.username}")
        app_logger.info(f"密码: admin123")
        app_logger.info(f"邮箱: {admin.email}")
        app_logger.info("请及时修改默认密码！")
        app_logger.info("=" * 50)
        
    except Exception as e:
        db.rollback()
        app_logger.error(f"创建管理员用户失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_superuser()

