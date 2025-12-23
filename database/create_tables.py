"""
手动创建数据库表的脚本
如果自动创建失败，可以使用此脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine
from app.core.logger import app_logger


def create_tables_manually():
    """
    手动创建数据库表
    """
    # 读取SQL文件
    sql_file = Path(__file__).parent / "init.sql"
    
    if not sql_file.exists():
        app_logger.error(f"SQL文件不存在: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割SQL语句（按分号分割）
    sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    try:
        with engine.connect() as conn:
            for i, statement in enumerate(sql_statements, 1):
                if statement:
                    app_logger.info(f"执行SQL语句 {i}/{len(sql_statements)}...")
                    conn.execute(text(statement))
                    conn.commit()
        
        app_logger.info("=" * 50)
        app_logger.info("数据库表创建成功！")
        app_logger.info("=" * 50)
        
        # 验证表是否创建
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            app_logger.info(f"已创建的表: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        app_logger.error(f"创建表失败: {e}")
        return False


if __name__ == "__main__":
    app_logger.info("开始手动创建数据库表...")
    success = create_tables_manually()
    
    if success:
        app_logger.info("\n✅ 数据库初始化完成！")
        app_logger.info("默认管理员账号：")
        app_logger.info("  用户名: admin")
        app_logger.info("  密码: admin123")
        app_logger.info("\n现在可以启动应用了：python main.py")
    else:
        app_logger.error("\n❌ 数据库初始化失败！")
        app_logger.error("请检查：")
        app_logger.error("  1. PostgreSQL 服务是否启动")
        app_logger.error("  2. 数据库配置是否正确（config.yaml）")
        app_logger.error("  3. 数据库是否已创建")

