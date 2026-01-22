"""
修复数据库序列问题
"""
from app.core.database import SessionLocal
from sqlalchemy import text

def fix_sequences():
    """修复所有表的序列"""
    db = SessionLocal()
    try:
        # 修复 admin_menus 表的序列
        result = db.execute(text(
            "SELECT setval('admin_menus_id_seq', (SELECT COALESCE(MAX(id), 1) FROM admin_menus))"
        ))
        db.commit()
        print("✓ admin_menus 序列已修复")
        
        # 可以添加其他表的序列修复
        tables = [
            'admin_users',
            'admin_roles', 
            'admin_permissions',
            'admin_user_roles',
            'admin_role_permissions',
            'admin_role_menus',
            'admin_user_permission_overrides',
            'admin_user_menu_overrides',
            'api_logs'
        ]
        
        for table in tables:
            try:
                result = db.execute(text(
                    f"SELECT setval('{table}_id_seq', (SELECT COALESCE(MAX(id), 1) FROM {table}))"
                ))
                db.commit()
                print(f"✓ {table} 序列已修复")
            except Exception as e:
                print(f"✗ {table} 序列修复失败: {e}")
        
        print("\n所有序列修复完成！")
        
    except Exception as e:
        print(f"修复失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_sequences()
