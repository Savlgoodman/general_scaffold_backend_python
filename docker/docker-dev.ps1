# Docker 开发环境管理脚本 (Windows)

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# 颜色输出函数
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 显示帮助信息
function Show-Help {
    Write-Host @"
Docker 开发环境管理脚本

用法: .\docker-dev.ps1 [命令]

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
  .\docker-dev.ps1 start
  .\docker-dev.ps1 logs
  .\docker-dev.ps1 shell

"@
}

# 启动开发环境
function Start-Dev {
    Write-Info "启动开发环境..."
    docker-compose -f docker-compose.dev.yml up -d
    Write-Info "开发环境已启动！"
    Write-Info "应用地址: http://localhost:8000"
    Write-Info "API文档: http://localhost:8000/docs"
    Write-Info "查看日志: .\docker-dev.ps1 logs"
}

# 停止开发环境
function Stop-Dev {
    Write-Info "停止开发环境..."
    docker-compose -f docker-compose.dev.yml down
    Write-Info "开发环境已停止！"
}

# 重启开发环境
function Restart-Dev {
    Write-Info "重启开发环境..."
    docker-compose -f docker-compose.dev.yml restart
    Write-Info "开发环境已重启！"
}

# 查看日志
function Show-Logs {
    Write-Info "查看日志（Ctrl+C 退出）..."
    docker-compose -f docker-compose.dev.yml logs -f
}

# 进入应用容器shell
function Enter-Shell {
    Write-Info "进入应用容器..."
    docker exec -it scaffold_app_dev /bin/bash
}

# 进入数据库shell
function Enter-DbShell {
    Write-Info "进入数据库..."
    docker exec -it scaffold_postgres_dev psql -U postgres -d scaffold_dev
}

# 清理环境
function Clean-Dev {
    Write-Warn "这将删除所有容器和数据！"
    $confirm = Read-Host "确定要继续吗？(yes/no)"
    if ($confirm -eq "yes") {
        Write-Info "清理开发环境..."
        docker-compose -f docker-compose.dev.yml down -v
        Write-Info "清理完成！"
    } else {
        Write-Info "取消清理操作"
    }
}

# 重新构建
function Rebuild-Dev {
    Write-Info "重新构建开发环境..."
    docker-compose -f docker-compose.dev.yml down
    docker-compose -f docker-compose.dev.yml build --no-cache
    docker-compose -f docker-compose.dev.yml up -d
    Write-Info "重新构建完成！"
}

# 查看状态
function Show-Status {
    Write-Info "服务状态："
    docker-compose -f docker-compose.dev.yml ps
}

# 主逻辑
switch ($Command.ToLower()) {
    "start" { Start-Dev }
    "stop" { Stop-Dev }
    "restart" { Restart-Dev }
    "logs" { Show-Logs }
    "shell" { Enter-Shell }
    "db-shell" { Enter-DbShell }
    "clean" { Clean-Dev }
    "rebuild" { Rebuild-Dev }
    "status" { Show-Status }
    "help" { Show-Help }
    default {
        Write-Error-Custom "未知命令: $Command"
        Write-Host ""
        Show-Help
        exit 1
    }
}

