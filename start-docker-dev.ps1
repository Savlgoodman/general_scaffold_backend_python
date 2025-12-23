# Docker 快速启动脚本 - 开发环境

Write-Host "==================================" -ForegroundColor Green
Write-Host "  启动 Docker 开发环境" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""

# 检查 Docker 是否运行
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
    exit 1
}

Write-Host "[信息] Docker 正在运行..." -ForegroundColor Green
Write-Host "[信息] 启动开发环境..." -ForegroundColor Green
Write-Host ""

# 启动开发环境
docker-compose -f docker/docker-compose.dev.yml up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Green
    Write-Host "  开发环境启动成功！" -ForegroundColor Green
    Write-Host "==================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "访问地址：" -ForegroundColor Cyan
    Write-Host "  - 应用: http://localhost:8000" -ForegroundColor Yellow
    Write-Host "  - API文档: http://localhost:8000/docs" -ForegroundColor Yellow
    Write-Host "  - 健康检查: http://localhost:8000/health" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "默认管理员账号：" -ForegroundColor Cyan
    Write-Host "  - 用户名: admin" -ForegroundColor Yellow
    Write-Host "  - 密码: admin123" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "常用命令：" -ForegroundColor Cyan
    Write-Host "  - 查看日志: .\docker\docker-dev.ps1 logs" -ForegroundColor Yellow
    Write-Host "  - 停止环境: .\docker\docker-dev.ps1 stop" -ForegroundColor Yellow
    Write-Host "  - 进入容器: .\docker\docker-dev.ps1 shell" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[错误] 启动失败，请查看错误信息" -ForegroundColor Red
    exit 1
}
