"""
验证码服务
负责生成和验证图形验证码
"""
import uuid
from typing import Tuple
from easy_captcha import SpecCaptcha

from app.core.redis import get_redis
from app.core.redis_keys import RedisKeyManager
from app.core.config import settings
from app.core.logger import app_logger


class CaptchaService:
    """验证码服务"""
    
    @staticmethod
    def generate_captcha() -> Tuple[str, str]:
        """
        生成验证码
        
        Returns:
            (captcha_key, base64_image): 验证码键和Base64图片数据
        """
        try:
            # 从配置读取验证码参数
            width = settings.captcha.width
            height = settings.captcha.height
            length = settings.captcha.length
            
            # 创建验证码实例
            captcha = SpecCaptcha(width, height, length)
            
            # 获取验证码文本（转小写）
            code = captcha.text().lower()
            
            # 生成唯一标识
            captcha_key = str(uuid.uuid4())
            
            # 存储到 Redis
            redis_client = get_redis()
            redis_key = RedisKeyManager.get_captcha_key(captcha_key)
            expire_time = settings.captcha.expire_seconds
            
            redis_client.setex(redis_key, expire_time, code)
            
            # 生成 Base64 图片
            base64_image = captcha.to_base64()
            
            app_logger.info(f"验证码生成成功: key={captcha_key}")
            
            return captcha_key, base64_image
            
        except Exception as e:
            app_logger.error(f"验证码生成失败: {str(e)}")
            raise
    
    @staticmethod
    def verify_captcha(captcha_key: str, captcha_code: str) -> bool:
        """
        验证验证码
        
        Args:
            captcha_key: 验证码键
            captcha_code: 用户输入的验证码
            
        Returns:
            验证是否成功
        """
        try:
            redis_client = get_redis()
            redis_key = RedisKeyManager.get_captcha_key(captcha_key)
            
            # 从 Redis 获取存储的验证码
            stored_code = redis_client.get(redis_key)
            
            if not stored_code:
                app_logger.warning(f"验证码不存在或已过期: key={captcha_key}")
                return False
            
            # 比较验证码（不区分大小写）
            is_valid = stored_code.lower() == captcha_code.lower()
            
            if is_valid:
                # 验证成功，立即删除验证码（防止重复使用）
                redis_client.delete(redis_key)
                app_logger.info(f"验证码验证成功: key={captcha_key}")
            else:
                app_logger.warning(f"验证码验证失败: key={captcha_key}, input={captcha_code}")
            
            return is_valid
            
        except Exception as e:
            app_logger.error(f"验证码验证异常: {str(e)}")
            return False
