"""
配置管理模块
从 config.yaml 读取配置，支持环境变量覆盖
"""
import os
from typing import List, Optional
from pathlib import Path
import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class AppConfig(BaseModel):
    """应用配置"""
    name: str
    version: str
    debug: bool
    host: str
    port: int
    reload: bool


class DatabaseConfig(BaseModel):
    """数据库配置"""
    host: str
    port: int
    username: str
    password: str
    database: str
    echo: bool
    pool_size: int
    max_overflow: int
    pool_recycle: int

    @property
    def url(self) -> str:
        """生成数据库连接URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseModel):
    """Redis配置"""
    host: str
    port: int
    password: str
    db: int
    max_connections: int
    decode_responses: bool


class JWTConfig(BaseModel):
    """JWT配置"""
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str
    format: str
    file_path: str
    max_bytes: int
    backup_count: int


class CORSConfig(BaseModel):
    """CORS配置"""
    allow_origins: List[str]
    allow_credentials: bool
    allow_methods: List[str]
    allow_headers: List[str]


class APILogConfig(BaseModel):
    """API日志配置"""
    enabled: bool
    exclude_paths: List[str]
    log_request_body: bool
    log_response_body: bool
    max_body_length: int


class Settings(BaseSettings):
    """全局配置类"""
    environment: str = "DEV"
    app: AppConfig
    database: DatabaseConfig
    redis: RedisConfig
    jwt: JWTConfig
    logging: LoggingConfig
    cors: CORSConfig
    api_log: APILogConfig

    class Config:
        case_sensitive = False


def load_config() -> Settings:
    """
    加载配置文件
    1. 从 config.yaml 读取配置
    2. 根据 environment 选择对应环境配置
    3. 环境变量可以覆盖配置文件
    """
    config_file = BASE_DIR / "config.yaml"
    
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")
    
    # 读取YAML配置
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    # 获取环境变量，默认为DEV
    environment = os.getenv("ENVIRONMENT", config_data.get("environment", "DEV")).upper()
    
    # 获取对应环境的配置
    env_key = environment.lower()
    if env_key not in config_data:
        raise ValueError(f"配置文件中不存在环境: {environment}")
    
    env_config = config_data[env_key]
    
    # 环境变量覆盖（如果存在）
    if os.getenv("DATABASE_HOST"):
        env_config["database"]["host"] = os.getenv("DATABASE_HOST")
    if os.getenv("DATABASE_PORT"):
        env_config["database"]["port"] = int(os.getenv("DATABASE_PORT"))
    if os.getenv("DATABASE_USERNAME"):
        env_config["database"]["username"] = os.getenv("DATABASE_USERNAME")
    if os.getenv("DATABASE_PASSWORD"):
        env_config["database"]["password"] = os.getenv("DATABASE_PASSWORD")
    if os.getenv("DATABASE_NAME"):
        env_config["database"]["database"] = os.getenv("DATABASE_NAME")
    
    if os.getenv("REDIS_HOST"):
        env_config["redis"]["host"] = os.getenv("REDIS_HOST")
    if os.getenv("REDIS_PORT"):
        env_config["redis"]["port"] = int(os.getenv("REDIS_PORT"))
    if os.getenv("REDIS_PASSWORD"):
        env_config["redis"]["password"] = os.getenv("REDIS_PASSWORD")
    if os.getenv("REDIS_DB"):
        env_config["redis"]["db"] = int(os.getenv("REDIS_DB"))
    
    if os.getenv("JWT_SECRET_KEY"):
        env_config["jwt"]["secret_key"] = os.getenv("JWT_SECRET_KEY")
    
    # 创建配置对象
    env_config["environment"] = environment
    settings_obj = Settings(**env_config)
    
    return settings_obj


# 全局配置实例
settings = load_config()


