"""
Redis连接管理
"""
import redis
from typing import Optional
from app.core.config import settings

# Redis连接池
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None


def init_redis() -> redis.Redis:
    """
    初始化Redis连接
    """
    global redis_pool, redis_client
    
    redis_pool = redis.ConnectionPool(
        host=settings.redis.host,
        port=settings.redis.port,
        password=settings.redis.password if settings.redis.password else None,
        db=settings.redis.db,
        max_connections=settings.redis.max_connections,
        decode_responses=settings.redis.decode_responses,
    )
    
    redis_client = redis.Redis(connection_pool=redis_pool)
    
    return redis_client


def get_redis() -> redis.Redis:
    """
    获取Redis客户端
    用于FastAPI的依赖注入
    """
    if redis_client is None:
        return init_redis()
    return redis_client


def close_redis() -> None:
    """
    关闭Redis连接
    """
    global redis_pool, redis_client
    
    if redis_client:
        redis_client.close()
        redis_client = None
    
    if redis_pool:
        redis_pool.disconnect()
        redis_pool = None


