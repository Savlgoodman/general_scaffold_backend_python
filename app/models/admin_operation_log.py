"""
操作审计日志数据库模型
记录管理员对系统资源的关键操作（增删改），用于安全审计和问题追溯
"""
from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class AdminOperationLog(Base):
    """管理员操作审计日志表"""
    __tablename__ = "admin_operation_logs"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")

    # 操作人信息
    user_id = Column(Integer, nullable=False, index=True, comment="操作人用户ID")
    username = Column(String(50), nullable=False, comment="操作人用户名")

    # 操作信息
    action = Column(String(20), nullable=False, index=True, comment="操作类型: CREATE/UPDATE/DELETE")
    resource_type = Column(String(50), nullable=False, index=True, comment="操作对象类型，如: user/role/permission/menu")
    resource_id = Column(Integer, comment="操作对象ID")
    description = Column(String(500), comment="操作描述，如: 删除用户张三")

    # 变更数据
    before_data = Column(Text, comment="变更前数据（JSON格式）")
    after_data = Column(Text, comment="变更后数据（JSON格式）")

    # 请求上下文
    request_method = Column(String(10), comment="请求方法")
    request_path = Column(String(500), comment="请求路径")
    ip_address = Column(String(50), comment="客户端IP地址")

    # created_at, updated_at, is_deleted 由 Base 自动提供

    def __repr__(self):
        return f"<AdminOperationLog(id={self.id}, action={self.action}, resource_type={self.resource_type})>"
