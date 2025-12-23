#!/bin/bash

# Docker 生产环境管理脚本

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

# 检查环境文件
check_env_file() {
    if [ ! -f .env.prod ]; then
        print_error ".env.prod 文件不存在！"
        print_info "请复制 .env.prod.example 为 .env.prod 并填写配置"
        print_info "cp .env.prod.example .env.prod"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
Docker 生产环境管理脚本

用法: ./docker-prod.sh [命令]

命令:
  start       启动生产环境
  stop        停止生产环境
  restart     重启生产环境
  logs        查看日志
  shell       进入应用容器shell
  db-shell    进入数据库shell
  backup      备份数据库
  status      查看服务状态
  help        显示此帮助信息

示例:
  ./docker-prod.sh start
  ./docker-prod.sh logs
  ./docker-prod.sh backup

EOF
}

# 启动生产环境
start_prod() {
    check_env_file
    print_info "启动生产环境..."
    docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
    print_info "生产环境已启动！"
    print_info "应用地址: http://localhost:8001"
    print_info "查看日志: ./docker-prod.sh logs"
}

# 停止生产环境
stop_prod() {
    print_info "停止生产环境..."
    docker-compose -f docker-compose.prod.yml down
    print_info "生产环境已停止！"
}

# 重启生产环境
restart_prod() {
    print_info "重启生产环境..."
    docker-compose -f docker-compose.prod.yml restart
    print_info "生产环境已重启！"
}

# 查看日志
show_logs() {
    print_info "查看日志（Ctrl+C 退出）..."
    docker-compose -f docker-compose.prod.yml logs -f
}

# 进入应用容器shell
enter_shell() {
    print_info "进入应用容器..."
    docker exec -it scaffold_app_prod /bin/bash
}

# 进入数据库shell
enter_db_shell() {
    print_info "进入数据库..."
    docker exec -it scaffold_postgres_prod psql -U postgres -d scaffold_prod
}

# 备份数据库
backup_db() {
    print_info "备份数据库..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    docker exec scaffold_postgres_prod pg_dump -U postgres scaffold_prod > "$BACKUP_FILE"
    print_info "数据库已备份到: $BACKUP_FILE"
}

# 查看状态
show_status() {
    print_info "服务状态："
    docker-compose -f docker-compose.prod.yml ps
}

# 主逻辑
case "${1:-}" in
    start)
        start_prod
        ;;
    stop)
        stop_prod
        ;;
    restart)
        restart_prod
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
    backup)
        backup_db
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

