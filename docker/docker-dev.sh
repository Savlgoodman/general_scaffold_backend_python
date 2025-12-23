#!/bin/bash

# Docker 开发环境管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
Docker 开发环境管理脚本

用法: ./docker-dev.sh [命令]

命令:
  start       启动开发环境
  stop        停止开发环境
  restart     重启开发环境
  logs        查看日志
  shell       进入应用容器shell
  db-shell    进入数据库shell
  clean       清理所有容器和数据（谨慎使用）
  rebuild     重新构建并启动
  status      查看服务状态
  help        显示此帮助信息

示例:
  ./docker-dev.sh start
  ./docker-dev.sh logs
  ./docker-dev.sh shell

EOF
}

# 启动开发环境
start_dev() {
    print_info "启动开发环境..."
    docker-compose -f docker-compose.dev.yml up -d
    print_info "开发环境已启动！"
    print_info "应用地址: http://localhost:8000"
    print_info "API文档: http://localhost:8000/docs"
    print_info "查看日志: ./docker-dev.sh logs"
}

# 停止开发环境
stop_dev() {
    print_info "停止开发环境..."
    docker-compose -f docker-compose.dev.yml down
    print_info "开发环境已停止！"
}

# 重启开发环境
restart_dev() {
    print_info "重启开发环境..."
    docker-compose -f docker-compose.dev.yml restart
    print_info "开发环境已重启！"
}

# 查看日志
show_logs() {
    print_info "查看日志（Ctrl+C 退出）..."
    docker-compose -f docker-compose.dev.yml logs -f
}

# 进入应用容器shell
enter_shell() {
    print_info "进入应用容器..."
    docker exec -it scaffold_app_dev /bin/bash
}

# 进入数据库shell
enter_db_shell() {
    print_info "进入数据库..."
    docker exec -it scaffold_postgres_dev psql -U postgres -d scaffold_dev
}

# 清理环境
clean_dev() {
    print_warn "这将删除所有容器和数据！"
    read -p "确定要继续吗？(yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        print_info "清理开发环境..."
        docker-compose -f docker-compose.dev.yml down -v
        print_info "清理完成！"
    else
        print_info "取消清理操作"
    fi
}

# 重新构建
rebuild_dev() {
    print_info "重新构建开发环境..."
    docker-compose -f docker-compose.dev.yml down
    docker-compose -f docker-compose.dev.yml build --no-cache
    docker-compose -f docker-compose.dev.yml up -d
    print_info "重新构建完成！"
}

# 查看状态
show_status() {
    print_info "服务状态："
    docker-compose -f docker-compose.dev.yml ps
}

# 主逻辑
case "${1:-}" in
    start)
        start_dev
        ;;
    stop)
        stop_dev
        ;;
    restart)
        restart_dev
        ;;
    logs)
        show_logs
        ;;
    shell)
        enter_shell
        ;;
    db-shell)
        enter_db_shell
        ;;
    clean)
        clean_dev
        ;;
    rebuild)
        rebuild_dev
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "未知命令: ${1:-}"
        echo ""
        show_help
        exit 1
        ;;
esac

