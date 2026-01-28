"""
管理员权限相关的Pydantic模型
"""
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class SourceType(str, Enum):
    """权限来源类型"""
    GROUP_PERMISSION = "group_permission"      # 组权限
    SINGLE_PERMISSION = "single_permission"    # 子权限
    USER_OVERRIDE = "user_override"            # 用户覆盖
    NO_PERMISSION = "no_permission"            # 无权限配置


class PermissionSource(BaseModel):
    """权限来源"""
    type: SourceType                           # 来源类型
    role_id: Optional[int] = None              # 角色ID
    role_name: Optional[str] = None            # 角色名称
    permission_id: Optional[int] = None        # 权限ID
    permission_name: Optional[str] = None      # 权限名称
    
    def get_description(self, effect: str) -> str:
        """生成人类可读的描述"""
        effect_text = "允许" if effect == "allow" else "拒绝"
        
        if self.type == SourceType.USER_OVERRIDE:
            return f"{effect_text}于用户权限覆盖"
        elif self.type == SourceType.NO_PERMISSION:
            return "拒绝于无权限配置"
        elif self.type == SourceType.GROUP_PERMISSION:
            return f"{effect_text}于角色[{self.role_name}]的组权限[{self.permission_name}]"
        elif self.type == SourceType.SINGLE_PERMISSION:
            return f"{effect_text}于角色[{self.role_name}]的子权限[{self.permission_name}]"
        return f"{effect_text}于未知来源"


class AdminPermissionCreate(BaseModel):
    """创建权限"""
    name: str = Field(..., description="权限名称")
    resource_pattern: str = Field(..., description="资源模式，支持通配符")
    method: str = Field("POST", description="HTTP方法")
    group_key: Optional[str] = Field(None, description="分组标识")
    group_name: Optional[str] = Field(None, description="分组名称")
    is_group: bool = Field(False, description="是否是组权限")
    description: Optional[str] = Field(None, description="描述")
    status: int = Field(1, description="状态：1=启用，0=禁用")


class AdminPermissionUpdate(BaseModel):
    """更新权限"""
    name: Optional[str] = Field(None, description="权限名称")
    resource_pattern: Optional[str] = Field(None, description="资源模式，支持通配符")
    method: Optional[str] = Field(None, description="HTTP方法")
    group_key: Optional[str] = Field(None, description="分组标识")
    group_name: Optional[str] = Field(None, description="分组名称")
    is_group: Optional[bool] = Field(None, description="是否是组权限")
    description: Optional[str] = Field(None, description="描述")
    status: Optional[int] = Field(None, description="状态：1=启用，0=禁用")


class AdminPermissionResponse(BaseModel):
    """权限响应模型"""
    id: int
    name: str
    resource_pattern: str
    method: str
    group_key: Optional[str]
    group_name: Optional[str]
    is_group: bool
    description: Optional[str]
    status: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PermissionAssignment(BaseModel):
    """权限分配模型"""
    permission_id: int = Field(..., description="权限ID")
    effect: str = Field("allow", description="效果：allow=允许，deny=拒绝")
    priority: int = Field(0, description="优先级，数值越大优先级越高")


class PermissionWithEffect(BaseModel):
    """带效果的权限模型"""
    id: int
    name: str
    resource_pattern: str
    method: str
    effect: Optional[str] = None  # None 表示未授权
    priority: Optional[int] = None
    is_inherited: bool = False
    is_overridden: bool = False
    is_granted: bool = False  # 是否已授权


class GroupPermissionItem(BaseModel):
    """组权限项（用于列表展示）"""
    id: int
    name: str
    resource_pattern: str
    method: str
    group_key: Optional[str]
    group_name: Optional[str]
    description: Optional[str]
    is_granted: bool = False  # 是否已授权给角色
    effect: Optional[str] = None  # 授权效果
    priority: Optional[int] = None  # 优先级
    children_count: int = 0  # 子权限数量


class PermissionGroup(BaseModel):
    """权限组模型"""
    group_key: str
    group_name: str
    group_permission: Optional[PermissionWithEffect]
    children: List[PermissionWithEffect]


class RolePermissionsGroupedResponse(BaseModel):
    """角色权限分组响应模型"""
    role_id: int
    groups: List[PermissionGroup]


class RoleGroupPermissionsResponse(BaseModel):
    """角色组权限列表响应"""
    role_id: int
    items: List[GroupPermissionItem]


class NonGroupPermissionItem(BaseModel):
    """非组权限项（用于分页列表）"""
    id: int
    name: str
    resource_pattern: str
    method: str
    group_key: Optional[str]
    group_name: Optional[str]
    description: Optional[str]
    is_granted: bool = False  # 是否已授权给角色
    effect: Optional[str] = None  # 授权效果
    priority: Optional[int] = None  # 优先级
    is_inherited: bool = False  # 是否从组权限继承


class PermissionDetailItem(BaseModel):
    """权限详情项"""
    id: int
    name: str
    resource_pattern: str
    method: str
    group_key: Optional[str] = None
    group_name: Optional[str] = None
    effect: str                                # allow/deny
    source: PermissionSource                   # 权限来源
    source_description: str                    # 来源描述文本
    is_inherited: bool = False                 # 是否从组权限继承
    is_overridden: bool = False                # 是否被覆盖


class PermissionGroupDetail(BaseModel):
    """权限分组详情"""
    group_key: str
    group_name: str
    group_permission: Optional[PermissionDetailItem] = None  # 组权限
    children: List[PermissionDetailItem] = []                # 子权限列表


class RolePermissionsDetailResponse(BaseModel):
    """角色权限详情响应"""
    role_id: int
    role_name: str
    groups: List[PermissionGroupDetail]


class UserPermissionsDetailResponse(BaseModel):
    """用户权限详情响应"""
    user_id: int
    username: str
    groups: List[PermissionGroupDetail]


class PermissionCheckResult(BaseModel):
    """权限检查结果"""
    allowed: bool                              # 是否允许
    effect: str                                # allow/deny
    source: PermissionSource                   # 权限来源
    deny_reason: Optional[str] = None          # 拒绝原因描述


class UserPermissionOverrideItem(BaseModel):
    """用户权限覆盖管理项"""
    id: int                                    # 权限ID
    name: str                                  # 权限名称
    resource_pattern: str                      # 资源模式
    method: str                                # HTTP方法
    group_key: Optional[str] = None            # 分组标识
    group_name: Optional[str] = None           # 分组名称
    description: Optional[str] = None          # 描述
    # 角色层面的权限状态
    role_granted: bool = False                 # 角色是否已授权（直接或继承）
    role_effect: Optional[str] = None          # 角色授权效果 (allow/deny)，未授权时为 None
    role_source: Optional[str] = None          # 角色授权来源描述（如"角色[管理员]的组权限[系统信息]"）
    is_inherited: bool = False                 # 是否从组权限继承
    # 用户覆盖状态
    is_overridden: bool = False                # 是否已被用户覆盖
    override_effect: Optional[str] = None      # 用户覆盖效果 (allow/deny)，未覆盖时为 None
    # 最终状态
    final_effect: str                          # 最终效果 (allow/deny)
    source_description: str                    # 最终来源描述







