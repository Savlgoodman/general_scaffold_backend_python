"""
查询参数处理工具
自动处理空字符串转换为None，以及类型转换
"""
from typing import Optional, TypeVar, Type, get_origin, get_args
from datetime import datetime
from fastapi import Query
from pydantic import BaseModel


def EmptyStrToNone(default=None, **kwargs):
    """
    自定义Query参数，自动将空字符串转换为None
    
    用法：
        @router.get("/list")
        def get_list(
            keyword: Optional[str] = EmptyStrToNone(None, description="搜索关键词"),
            user_id: Optional[int] = EmptyStrToNone(None, description="用户ID"),
        ):
            pass
    """
    # 创建一个Query对象，但使用str类型接收所有参数
    return Query(default=default, **kwargs)


class QueryParamParser:
    """
    查询参数解析器
    自动处理空字符串和类型转换
    """
    
    @staticmethod
    def parse_str(value: Optional[str]) -> Optional[str]:
        """解析字符串，空字符串返回None"""
        if value is None or value.strip() == "":
            return None
        return value.strip()
    
    @staticmethod
    def parse_int(value: Optional[str]) -> Optional[int]:
        """解析整数，空字符串或无效值返回None"""
        if value is None or value.strip() == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def parse_float(value: Optional[str]) -> Optional[float]:
        """解析浮点数，空字符串或无效值返回None"""
        if value is None or value.strip() == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def parse_bool(value: Optional[str]) -> Optional[bool]:
        """解析布尔值，空字符串返回None"""
        if value is None or value.strip() == "":
            return None
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        if value.lower() in ("false", "0", "no", "off"):
            return False
        return None
    
    @staticmethod
    def parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """解析日期时间，空字符串或无效值返回None"""
        if value is None or value.strip() == "":
            return None
        try:
            # 支持多种
            value = value.strip()
            # ISO格式 (带时区)
            if 'T' in value:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            # 标准日期时间格式
            if ' ' in value:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            # 仅日期格式
            return datetime.strptime(value, "%Y-%m-%d")
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def parse_list(value: Optional[str], item_type: Type = str, separator: str = ",") -> Optional[list]:
        """解析列表，空字符串返回None"""
        if value is None or value.strip() == "":
            return None
        try:
            items = [item.strip() for item in value.split(separator) if item.strip()]
            if not items:
                return None
            if item_type == int:
                return [int(item) for item in items]
            elif item_type == float:
                return [float(item) for item in items]
            return items
        except (ValueError, TypeError):
            return None


# 创建便捷的解析函数别名
parse_str = QueryParamParser.parse_str
parse_int = QueryParamParser.parse_int
parse_float = QueryParamParser.parse_float
parse_bool = QueryParamParser.parse_bool
parse_datetime = QueryParamParser.parse_datetime
parse_list = QueryParamParser.parse_list


def clean_query_params(**kwargs) -> dict:
    """
    清理查询参数，将空字符串转换为None
    
    用法：
        params = clean_query_params(
            keyword=keyword,
            user_id=(user_id, int),
            is_active=(is_active, bool),
            start_time=(start_time, datetime),
        )
    
    参数格式：
        - 直接传值：自动作为字符串处理
        - 元组 (value, type)：按指定类型解析
    
    返回：
        清理后的参数字典
    """
    result = {}
    for key, value in kwargs.items():
        if isinstance(value, tuple) and len(value) == 2:
            val, val_type = value
            if val_type == int:
                result[key] = parse_int(val)
            elif val_type == float:
                result[key] = parse_float(val)
            elif val_type == bool:
                result[key] = parse_bool(val)
            elif val_type == datetime:
                result[key] = parse_datetime(val)
            elif val_type == list:
                result[key] = parse_list(val)
            else:
                result[key] = parse_str(val)
        else:
            result[key] = parse_str(value)
    return result

