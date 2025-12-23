"""
日志配置模块
使用loguru进行日志管理
"""
import sys
from pathlib import Path
from loguru import logger

from app.core.config import settings, BASE_DIR


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
    
    return logger


# 初始化日志
app_logger = setup_logger()

