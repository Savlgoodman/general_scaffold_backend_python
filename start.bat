# 快速启动脚本

# 检查Python版本
python --version

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库并创建管理员用户
python init_db.py

# 启动应用
python main.py


