完整的 RBAC（基于角色的访问控制）权限认证系统。以下是详细总结：
📊 数据库模型（共 8 个新表）
表名 说明 主要字段
admin_roles 角色表 id, name, remark, status
admin_permissions API 权限表 id, name, api_path, remark, status
admin_menus 菜单表 id, name, path, parent_id, sort, remark, status
admin_user_roles 用户角色关联表 id, admin_user_id, role_id
admin_role_permissions 角色权限关联表 id, role_id, permission_id
admin_role_menus 角色菜单关联表 id, role_id, menu_id
admin_user_permission_overrides 用户权限覆盖表 id, admin_user_id, permission_id, effect(ALLOW/DENY)
admin_user_menu_overrides 用户菜单覆盖表 id, admin_user_id, menu_id, effect(ALLOW/DENY)
🔌 API 接口
角色管理 (/api/admin/roles)
GET /list - 获取角色列表
GET /detail/{role_id} - 获取角色详情
POST /create - 创建角色
POST /update/{role_id} - 更新角色
POST /delete/{role_id} - 删除角色
POST /assign-permissions/{role_id} - 为角色分配权限
POST /assign-menus/{role_id} - 为角色分配菜单
GET /permissions/{role_id} - 获取角色的权限列表
GET /menus/{role_id} - 获取角色的菜单列表
权限管理 (/api/admin/permissions)
GET /list - 获取权限列表
GET /detail/{permission_id} - 获取权限详情
POST /create - 创建权限
POST /update/{permission_id} - 更新权限
POST /delete/{permission_id} - 删除权限
菜单管理 (/api/admin/menus)
GET /list - 获取菜单列表
GET /tree - 获取菜单树（树形结构）
GET /detail/{menu_id} - 获取菜单详情
POST /create - 创建菜单
POST /update/{menu_id} - 更新菜单
POST /delete/{menu_id} - 删除菜单
用户管理新增接口 (/api/admin/admin_users)
POST /assign-roles/{user_id} - 为用户分配角色
GET /roles/{user_id} - 获取用户的角色列表
POST /permission-overrides/{user_id} - 批量设置用户权限覆盖
GET /permission-overrides/{user_id} - 获取用户权限覆盖列表
POST /menu-overrides/{user_id} - 批量设置用户菜单覆盖
GET /menu-overrides/{user_id} - 获取用户菜单覆盖列表
🔐 权限验证逻辑
登录/注册接口 - 不需要权限验证
超级管理员 - 自动通过所有 API 权限验证，登录时获取所有激活菜单
普通用户权限计算：
获取用户所有角色的权限（取并集）
应用权限覆盖表：ALLOW 添加权限，DENY 移除权限
菜单权限 - 登录时通过 menus 字段返回树形结构
📁 文件结构
app/├── models/│ ├── admin_role.py # 角色模型 │ ├── admin_permission.py # 权限模型 │ ├── admin_menu.py # 菜单模型 │ ├── admin_user_role.py # 用户角色关联 │ ├── admin_role_permission.py # 角色权限关联 │ ├── admin_role_menu.py # 角色菜单关联 │ ├── admin_user_permission_override.py # 用户权限覆盖 │ └── admin_user_menu_override.py # 用户菜单覆盖 ├── schemas/│ ├── admin_role.py│ ├── admin_permission.py│ ├── admin_menu.py│ ├── admin_auth.py # 登录响应（含菜单树）│ ├── admin_user_permission_override.py│ └── admin_user_menu_override.py├── services/│ ├── admin_role_service.py│ ├── admin_permission_service.py│ ├── admin_menu_service.py│ └── admin_rbac_service.py # RBAC 核心服务 ├── api/admin/│ ├── roles.py│ ├── permissions.py│ └── menus.py└── middleware/ └── auth.py # 已增加 API 权限验证
⚙️ 使用说明
启动项目前，删除数据库中的旧表，启动后会自动创建新表
创建权限：将需要控制的 API 路径添加到 admin_permissions 表
创建菜单：添加菜单项，支持最多二级菜单（parent_id=0 为顶级）
创建角色：创建角色并分配权限和菜单
分配角色：创建用户时选择角色，或后续通过接口分配
细粒度控制：使用覆盖表对特定用户进行权限增减
📝 状态字段说明
所有表的 status 字段统一为：
1 = 激活/启用
0 = 禁用
