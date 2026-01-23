"""
验证码相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field


class CaptchaResponse(BaseModel):
    """验证码响应模型"""
    captcha_key: str = Field(..., description="验证码唯一标识")
    captcha_image: str = Field(..., description="Base64编码的验证码图片")


class LoginWithCaptcha(BaseModel):
    """带验证码的登录请求模型"""
    username: str = Field(..., description="用户名", min_length=1, max_length=50)
    password: str = Field(..., description="密码", min_length=1)
    captcha_key: str = Field(..., description="验证码键")
    captcha_code: str = Field(..., description="验证码", min_length=1, max_length=10)
