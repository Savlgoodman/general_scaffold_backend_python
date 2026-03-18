# 数据库迁移指南 (Alembic)

本项目使用 Alembic 管理数据库结构变更，所有表结构的修改都应通过迁移脚本完成。

## 基本概念

Alembic 就是"数据库的 Git"：
- 每次模型变更生成一个迁移文件（类似 commit）
- 迁移文件包含 `upgrade()`（升级）和 `downgrade()`（回滚）
- 数据库中的 `alembic_version` 表记录当前版本

## 日常使用

### 1. 修改模型后生成迁移

当你修改了 `app/models/` 下的模型文件后：

```bash
# 自动检测模型变更，生成迁移脚本
alembic revision --autogenerate -m "描述你的变更"

# 示例
alembic revision --autogenerate -m "add_phone_field_to_admin_users"
```

生成的迁移文件在 `alembic/versions/` 目录下，建议检查一下内容是否正确。

### 2. 应用迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级一个版本
alembic upgrade +1
```

### 3. 回滚迁移

```bash
# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>

# 回滚所有迁移
alembic downgrade base
```

### 4. 查看状态

```bash
# 查看当前数据库版本
alembic current

# 查看迁移历史
alembic history

# 查看待执行的迁移
alembic history --indicate-current
```

## 注意事项

### autogenerate 能检测到的变更
- 新增/删除表
- 新增/删除列
- 列类型变更（部分）
- 新增/删除索引和约束

### autogenerate 检测不到的变更
- 表名或列名重命名（会被识别为删除+新增）
- 数据迁移（需要手动编写）
- 存储过程、触发器等

对于重命名操作，需要手动修改生成的迁移文件，将 `drop_column` + `add_column` 替换为：
```python
op.alter_column('table_name', 'old_column', new_column_name='new_column')
```

### 新增模型文件

如果新增了模型文件（如 `app/models/new_model.py`），需要在 `alembic/env.py` 的导入列表中添加：

```python
from app.models import (
    # ... 已有模型
    new_model,  # 新增
)
```

同时也要在 `app/core/database.py` 的 `init_db()` 中添加对应导入。

## 项目配置说明

- `alembic.ini` — Alembic 主配置文件
- `alembic/env.py` — 迁移环境配置，从 `config.yaml` 动态读取数据库连接
- `alembic/versions/` — 迁移脚本目录
- 数据库 URL 无需在 `alembic.ini` 中配置，由 `env.py` 从项目的 `config.yaml` 自动读取

## 常见问题

### Q: 迁移文件冲突怎么办？
多人协作时可能出现分支冲突，使用 `alembic merge` 合并：
```bash
alembic merge -m "merge_branches" <rev1> <rev2>
```

### Q: 想重新生成基线怎么办？
```bash
# 清空迁移历史（危险操作，仅开发环境使用）
alembic downgrade base
# 删除 alembic/versions/ 下所有文件
# 重新生成
alembic revision --autogenerate -m "new_baseline"
alembic upgrade head
```

### Q: Windows 下报编码错误？
确保 `alembic.ini` 中不包含中文注释，或设置环境变量：
```bash
set PYTHONUTF8=1
```
