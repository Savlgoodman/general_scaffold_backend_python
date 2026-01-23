"""
系统信息服务层
处理系统监控相关的业务逻辑
"""
import psutil
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.logger import app_logger
from app.core.redis import get_redis
from app.models.api_log import APILog


class SystemInfoService:
    """系统信息服务"""
    
    # 默认系统配置
    DEFAULT_CONFIGS = {
        "site_name": "通用后台管理系统",
        "version": "1.0.0",
        "last_update_date": "2024-01-01"
    }
    
    # 允许的配置键（白名单）
    ALLOWED_CONFIG_KEYS = {"site_name", "version", "last_update_date"}
    
    @staticmethod
    def get_system_resources() -> Dict:
        """
        获取系统资源使用情况（CPU和内存）
        """
        try:
            # 获取CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 获取内存信息
            memory = psutil.virtual_memory()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_available": memory.available,
                "memory_percent": memory.percent
            }
        except Exception as e:
            app_logger.error(f"获取系统资源信息失败: {str(e)}")
            # 返回默认值
            return {
                "cpu_percent": 0.0,
                "memory_total": 0,
                "memory_used": 0,
                "memory_available": 0,
                "memory_percent": 0.0
            }
    
    @staticmethod
    def get_network_stats() -> Dict:
        """
        获取网络统计信息
        """
        try:
            # 获取网络IO统计
            net_io = psutil.net_io_counters()
            
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        except Exception as e:
            app_logger.error(f"获取网络统计信息失败: {str(e)}")
            # 返回默认值
            return {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0
            }
    
    @staticmethod
    def get_redis_status() -> Dict:
        """
        获取Redis状态和基本信息
        """
        try:
            redis_client = get_redis()
            
            # 测试连接
            redis_client.ping()
            
            # 获取Redis信息
            info = redis_client.info()
            
            # 获取数据库大小
            db_size = redis_client.dbsize()
            
            return {
                "connected": True,
                "db_size": db_size,
                "used_memory": info.get("used_memory"),
                "used_memory_human": info.get("used_memory_human"),
                "error_message": None
            }
        except Exception as e:
            app_logger.error(f"获取Redis状态失败: {str(e)}")
            return {
                "connected": False,
                "db_size": None,
                "used_memory": None,
                "used_memory_human": None,
                "error_message": str(e)
            }
    
    @staticmethod
    def get_redis_keys(
        skip: int,
        limit: int,
        pattern: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        获取Redis键值对（分页）
        使用SCAN命令避免阻塞
        """
        try:
            redis_client = get_redis()
            
            # 使用SCAN命令获取键
            search_pattern = pattern if pattern else "*"
            cursor = 0
            all_keys = []
            
            # 使用SCAN迭代获取所有匹配的键
            while True:
                cursor, keys = redis_client.scan(cursor, match=search_pattern, count=100)
                all_keys.extend(keys)
                if cursor == 0:
                    break
            
            # 总数
            total = len(all_keys)
            
            # 分页
            paginated_keys = all_keys[skip:skip + limit]
            
            # 获取每个键的详细信息
            result = []
            for key in paginated_keys:
                try:
                    # 获取键类型
                    key_type = redis_client.type(key)
                    
                    # 获取TTL
                    ttl = redis_client.ttl(key)
                    
                    # 获取值（根据类型）
                    if key_type == "string":
                        value = redis_client.get(key)
                    elif key_type == "list":
                        value = str(redis_client.lrange(key, 0, -1))
                    elif key_type == "set":
                        value = str(redis_client.smembers(key))
                    elif key_type == "zset":
                        value = str(redis_client.zrange(key, 0, -1))
                    elif key_type == "hash":
                        value = str(redis_client.hgetall(key))
                    else:
                        value = f"<{key_type}>"
                    
                    # 转换为字符串并截断
                    value_str = str(value) if value else ""
                    if len(value_str) > 1000:
                        value_str = value_str[:1000] + "... (已截断)"
                    
                    result.append({
                        "key": key,
                        "type": key_type,
                        "value": value_str,
                        "ttl": ttl
                    })
                except Exception as e:
                    app_logger.error(f"获取Redis键 {key} 的值失败: {str(e)}")
                    result.append({
                        "key": key,
                        "type": "error",
                        "value": f"获取失败: {str(e)}",
                        "ttl": None
                    })
            
            return result, total
        except Exception as e:
            app_logger.error(f"获取Redis键值对失败: {str(e)}")
            return [], 0
    
    @staticmethod
    def get_failed_login_stats(db: Session) -> Dict:
        """
        获取今日失败登录统计
        查询api_logs表中登录接口的非200状态记录
        """
        try:
            from datetime import date
            
            # 获取今天的开始时间（00:00:00）
            today_start = datetime.combine(date.today(), datetime.min.time())
            
            # 构建查询 - 只查询今天的失败登录
            query = db.query(APILog).filter(
                APILog.path == '/api/admin/auth/login',
                APILog.status_code != 200,
                APILog.is_deleted == False,
                APILog.created_at >= today_start
            )
            
            # 获取总数
            total_count = query.count()
            
            return {
                "total_count": total_count
            }
        except Exception as e:
            app_logger.error(f"获取失败登录统计失败: {str(e)}")
            return {
                "total_count": 0
            }

    
    @staticmethod
    def get_system_config(db: Session) -> Dict[str, str]:
        """
        获取系统配置信息
        只返回允许的配置键（site_name, version, last_update_date）
        如果数据库为空，返回默认配置
        """
        try:
            from app.models.admin_system_config import AdminSystemConfig
            
            # 查询所有未删除的配置项，并且只查询允许的键
            configs = db.query(AdminSystemConfig).filter(
                AdminSystemConfig.is_deleted == False,
                AdminSystemConfig.config_key.in_(SystemInfoService.ALLOWED_CONFIG_KEYS)
            ).all()
            
            # 如果数据库为空，返回默认配置
            if not configs:
                app_logger.info("数据库中无配置项，返回默认配置")
                return SystemInfoService.DEFAULT_CONFIGS.copy()
            
            # 转换为字典格式
            result = {config.config_key: config.config_value for config in configs}
            
            # 补充缺失的默认配置项
            for key in SystemInfoService.ALLOWED_CONFIG_KEYS:
                if key not in result:
                    result[key] = SystemInfoService.DEFAULT_CONFIGS.get(key, "")
            
            return result
        except Exception as e:
            app_logger.error(f"获取系统配置失败: {str(e)}")
            # 发生错误时返回默认配置
            return SystemInfoService.DEFAULT_CONFIGS.copy()

    
    @staticmethod
    def update_system_config(db: Session, configs: List[Dict]) -> Dict[str, str]:
        """
        批量更新或创建系统配置
        只允许更新预定义的配置键（site_name, version, last_update_date）
        
        Args:
            db: 数据库会话
            configs: 配置项列表，每项包含 config_key, config_value, description
        
        Returns:
            更新后的所有配置字典
        
        Raises:
            ValueError: 当配置键不在允许列表中时
        """
        try:
            from app.models.admin_system_config import AdminSystemConfig
            
            for config_item in configs:
                config_key = config_item.get("config_key")
                config_value = config_item.get("config_value")
                description = config_item.get("description")
                
                # 验证配置键是否在允许列表中
                if config_key not in SystemInfoService.ALLOWED_CONFIG_KEYS:
                    error_msg = f"不允许的配置键: {config_key}。只允许: {', '.join(SystemInfoService.ALLOWED_CONFIG_KEYS)}"
                    app_logger.warning(error_msg)
                    raise ValueError(error_msg)
                
                # 查询配置项是否存在
                existing_config = db.query(AdminSystemConfig).filter(
                    AdminSystemConfig.config_key == config_key,
                    AdminSystemConfig.is_deleted == False
                ).first()
                
                if existing_config:
                    # 更新已存在的配置项
                    existing_config.config_value = config_value
                    if description is not None:
                        existing_config.description = description
                    app_logger.info(f"更新配置项: {config_key}")
                else:
                    # 创建新的配置项
                    new_config = AdminSystemConfig(
                        config_key=config_key,
                        config_value=config_value,
                        description=description
                    )
                    db.add(new_config)
                    app_logger.info(f"创建配置项: {config_key}")
            
            # 提交事务
            db.commit()
            
            # 返回更新后的所有配置
            return SystemInfoService.get_system_config(db)
        except ValueError:
            # 重新抛出验证错误
            raise
        except Exception as e:
            db.rollback()
            app_logger.error(f"更新系统配置失败: {str(e)}")
            raise
