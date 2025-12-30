"""
API日志数据库模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from app.core.database import Base


class APILog(Base):
    """API调用日志表"""
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    
    # 请求信息
    method = Column(String(10), nullable=False, comment="请求方法")
    path = Column(String(500), nullable=False, index=True, comment="请求路径")
    query_params = Column(Text, comment="查询参数")
    request_body = Column(Text, comment="请求体")
    
    # 响应信息
    status_code = Column(Integer, comment="响应状态码")
    response_body = Column(Text, comment="响应体")
    
    # 性能信息
    duration = Column(Float, comment="响应时长(秒)")
    
    # 用户信息
    user_id = Column(Integer, index=True, comment="用户ID")
    username = Column(String(50), comment="用户名")
    
    # 客户端信息
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="User Agent")
    
    # created_at, updated_at, is_deleted 字段由 Base 基类自动提供
    
    def __repr__(self):
        return f"<APILog(id={self.id}, method={self.method}, path={self.path})>"


