---
inclusion: manual
---

agent rules
规范要求、接口开发规范、项目总要求、架构要求
对于这个项目来说，你需要谨记以下几点：

1. 该 python 项目后端是由 fastapi 框架开发，并且混合了前台、后台逻辑一体。对于部分如 api 目录，区分了有/app/api/admin 和/app/api/web 两个目录，分别对应后台和前台的接口。
2. 该项目是前后端分离项目，请注意接口功能实现。
3. 部分灵活变量创建前，请先检查在配置文件中是否有相关配置，例如 JWT 密钥等敏感信息。如果没有请创建到配置文件中，不要写死在代码中。
4. 请保证一个完整的、良好的项目架构。
5. 当你要写一个表单的增删查改操作时，请谨记分页查询功能返回的数据一定要简洁、然后设计一个根据 id 查看该记录详情的接口，保证接口的功能性和简洁性，不要做过多不必要的数据传输。同时对于分页查询的接口而言，只有页数和页码是必传参数，其他参数都是可选的。
6. 切记，只能使用 get 和 post 方法，其他方法一律不许使用。删除、更新方法使用 post 方法带参数传输。
7. 解析参数时，使用.\app\utils\query_params.py 这个参数解析工具来，参考方法如 params = clean_query_params(keyword=keyword,s_active=(is_active, bool)) 类似的方法，还有
8. 对于每个 API 模块的 tags，一定要是英文的简洁描述如 router = APIRouter(prefix="/auth", tags=["auth"])。
9. 请注意，api 接口部分应保持清爽、干净的代码风格，除参数预处理、调用 service 方法、返回返回值、处理返回体之外，不应当有任何业务逻辑的方法和代码。最佳 api 接口实践：.\app\api\admin\users.py 以及 .\app\api\admin\api_logs.py 如果你需要修改 api 或者创建 api 模块时可以供你参考。编写API时，若要使用路径参数，只能在api路径结尾使用，如/system/user/{user_id}，有且仅能有一个路径参数且在末尾。因为这样才能方便后续的api鉴权的调用。
10. services 文件夹中的服务模块文件命名应遵守如 api_log_service,user_service 这样的命名规范方式。service 最佳实践：.\app\services\api_log_service.py 以及.\app\services\user_service.py 如果你需要修改 service 或者创建 service 服务时可以供你参考。
11. 已配置自动加载表单功能，如果需要修改xx数据库表，我会提前删除数据库中的表，然后你修改表单后我启动项目即可自动添加表单。如果你要创建新的表单，请继承基类Base并指定表名，且在.\app\core\database.py中的init_db()函数中指定对应模型。
