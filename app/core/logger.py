"""
日志配置模块
使用loguru进行日志管理
WARNING 以上级别日志自动写入 app_error_logs 数据库表
"""
import sys
from pathlib import Path
from loguru import logger

from app.core.config import settings, BASE_DIR


def _db_sink(message):
    """
    loguru 自定义 sink：将 WARNING 以上级别的日志自动写入数据库。
    使用独立的数据库 session，避免影响请求上下文中的 session。
    """
    record = message.record
    level = record["level"].name

    # 仅处理 WARNING 以上级别
    if level not in ("WARNING", "ERROR", "CRITICAL"):
        return

    try:
        from app.core.database import SessionLocal
        from app.models.app_error_log import AppErrorLog

        # 提取异常堆栈
        traceback_str = None
        if record["exception"]:
            traceback_str = "".join(
                record["exception"].traceback.format()
            ) if record["exception"].traceback else str(record["exception"])

        db = SessionLocal()
        try:
            log_entry = AppErrorLog(
                level=level,
                message=str(record["message"])[:4000],  # 限制长度防止超大消息
                traceback=traceback_str,
            )
            db.add(log_entry)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
    except Exception:
        # sink 自身不能抛异常，否则会影响日志系统
        pass


def setup_logger():
    """
    配置日志系统
    """
    # 移除默认的handler
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.logging.level,
        colorize=True,
    )

    # 文件输出
    log_path = BASE_DIR / settings.logging.file_path
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.logging.level,
        rotation=settings.logging.max_bytes,
        retention=settings.logging.backup_count,
        encoding="utf-8",
        enqueue=True,  # 异步写入
    )

    # 数据库 sink：WARNING 以上自动入库
    logger.add(
        _db_sink,
        level="WARNING",
        enqueue=True,  # 异步写入，不阻塞主线程
    )

    return logger


# 初始化日志
app_logger = setup_logger()

