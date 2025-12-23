#!/bin/bash

# 快速启动脚本

# 检查Python版本
python3 --version

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库并创建管理员用户
python init_db.py

# 启动应用
python main.py


