#!/bin/bash

# Docker 快速启动脚本 - 开发环境

echo "=================================="
echo "  启动 Docker 开发环境"
echo "=================================="
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "[错误] Docker 未运行，请先启动 Docker"
    exit 1
fi

echo "[信息] Docker 正在运行..."
echo "[信息] 启动开发环境..."
echo ""

# 启动开发环境
docker-compose -f docker/docker-compose.dev.yml up -d

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "  开发环境启动成功！"
    echo "=================================="
    echo ""
    echo "访问地址："
    echo "  - 应用: http://localhost:8000"
    echo "  - API文档: http://localhost:8000/docs"
    echo "  - 健康检查: http://localhost:8000/health"
    echo ""
    echo "默认管理员账号："
    echo "  - 用户名: admin"
    echo "  - 密码: admin123"
    echo ""
    echo "常用命令："
    echo "  - 查看日志: ./docker/docker-dev.sh logs"
    echo "  - 停止环境: ./docker/docker-dev.sh stop"
    echo "  - 进入容器: ./docker/docker-dev.sh shell"
    echo ""
else
    echo ""
    echo "[错误] 启动失败，请查看错误信息"
    exit 1
fi

