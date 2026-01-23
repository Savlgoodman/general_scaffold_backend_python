"""
Redis 键名管理器
提供统一的 Redis 键名生成和管理功能
"""
from enum import Enum
from typing import Optional


class RedisKeyPattern(str, Enum):
    """Redis 键名模式枚举"""
    # 验证码相关
    CAPTCHA = "admin:captcha:{key}"
    
    # 可扩展其他键名模式
    # SESSION = "admin:session:{user_id}"
    # RATE_LIMIT = "admin:rate_limit:{ip}:{endpoint}"


class RedisKeyConfig:
    """Redis 键名配置"""
    # 键名过期时间（秒）
    CAPTCHA_EXPIRE = 300  # 5分钟
    
    # 键名前缀（可根据环境配置）
    KEY_PREFIX = ""


class RedisKeyManager:
    """Redis 键名管理器"""
    
    @staticmethod
    def get_captcha_key(captcha_id: str) -> str:
        """
        生成验证码键名
        
        Args:
            captcha_id: 验证码唯一标识
            
        Returns:
            完整的 Redis 键名
        """
        pattern = RedisKeyPattern.CAPTCHA.value
        key = pattern.format(key=captcha_id)
        if RedisKeyConfig.KEY_PREFIX:
            return f"{RedisKeyConfig.KEY_PREFIX}:{key}"
        return key
    
    @staticmethod
    def get_captcha_expire() -> int:
        """
        获取验证码过期时间
        
        Returns:
            过期时间（秒）
        """
        return RedisKeyConfig.CAPTCHA_EXPIRE
    
    @staticmethod
    def set_key_prefix(prefix: str) -> None:
        """
        设置键名前缀（用于环境隔离）
        
        Args:
            prefix: 键名前缀
        """
        RedisKeyConfig.KEY_PREFIX = prefix
