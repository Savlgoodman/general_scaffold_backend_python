# 数据库初始化说明

## 方式一：使用 psql 命令行

```bash
# 1. 连接到PostgreSQL
psql -U postgres -h localhost

# 2. 创建数据库
CREATE DATABASE scaffold_dev;

# 3. 连接到新数据库
\c scaffold_dev

# 4. 执行SQL文件
\i database/init.sql

# 或者一行命令
psql -U postgres -h localhost -d scaffold_dev -f database/init.sql
```

## 方式二：使用 pgAdmin

1. 打开 pgAdmin
2. 连接到你的PostgreSQL服务器
3. 右键点击 "Databases" -> "Create" -> "Database"
4. 输入数据库名：`scaffold_dev`
5. 右键点击新数据库 -> "Query Tool"
6. 打开 `database/init.sql` 文件
7. 复制内容到查询窗口
8. 点击执行（F5）

## 方式三：使用 Python 脚本（推荐）

```bash
# 确保已安装依赖
pip install -r requirements.txt

# 运行初始化脚本
python init_db.py
```

这个脚本会：
- ✅ 自动创建所有表
- ✅ 创建默认管理员账号
- ✅ 显示创建结果

## 方式四：使用 Docker

```bash
# 启动 Docker 容器（会自动创建数据库和表）
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

## 验证表是否创建成功

```sql
-- 查看所有表
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- 查看用户表结构
\d users

-- 查看API日志表结构
\d api_logs

-- 查看管理员用户
SELECT id, username, email, is_superuser FROM users;
```

## 默认管理员账号

- **用户名**: admin
- **密码**: admin123
- **邮箱**: admin@example.com

## 配置数据库连接

修改 `config.yaml` 中的数据库配置：

```yaml
dev:
  database:
    host: "localhost"      # 数据库地址
    port: 5432            # 端口
    username: "postgres"  # 用户名
    password: "postgres"  # 密码
    database: "scaffold_dev"  # 数据库名
```

或使用环境变量：

```bash
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_USERNAME=postgres
export DATABASE_PASSWORD=your_password
export DATABASE_NAME=scaffold_dev
```

## 常见问题

### 1. 连接失败
- 检查 PostgreSQL 服务是否启动
- 检查防火墙是否开放 5432 端口
- 检查 pg_hba.conf 配置

### 2. 权限不足
```sql
-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE scaffold_dev TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
```

### 3. 表已存在
```sql
-- 删除所有表（谨慎使用）
DROP TABLE IF EXISTS api_logs CASCADE;
DROP TABLE IF EXISTS users CASCADE;
```

