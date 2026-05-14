# 以管理员身份运行
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator")) {
    Write-Host "请以管理员身份运行此脚本！右键 -> 以管理员身份运行 PowerShell" -ForegroundColor Red
    pause
    exit 1
}

$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$SERVICE_NAME = "pbft-demo"
$NSSM_DIR = "$PROJECT_DIR\nssm"
$NSSM = "$NSSM_DIR\nssm.exe"
$PYTHON = (Get-Command python -ErrorAction SilentlyContinue).Source

Write-Host "=== PBFT 服务器部署 ===" -ForegroundColor Cyan
Write-Host "项目路径: $PROJECT_DIR"

# 检查 Python
if (-not $PYTHON) {
    Write-Host "错误: 未找到 python，请先安装 Python 3.9+" -ForegroundColor Red
    pause; exit 1
}
Write-Host "Python: $PYTHON"

# 安装 Python 依赖
Write-Host "`n[1/4] 安装 Python 依赖..."
& pip install --user -r "$PROJECT_DIR\backend\requirements.txt" -q

# 下载 NSSM
Write-Host "[2/4] 准备 NSSM..."
if (-not (Test-Path $NSSM)) {
    New-Item -ItemType Directory -Force -Path $NSSM_DIR | Out-Null
    $nssmZip = "$env:TEMP\nssm.zip"
    Write-Host "  下载 NSSM..."
    Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile $nssmZip
    Expand-Archive -Path $nssmZip -DestinationPath "$env:TEMP\nssm_extract" -Force
    Copy-Item "$env:TEMP\nssm_extract\nssm-2.24\win64\nssm.exe" $NSSM
    Remove-Item $nssmZip -Force
}
Write-Host "  NSSM 就绪"

# 注册 Windows 服务
Write-Host "[3/4] 注册 Windows 服务..."
& $NSSM stop $SERVICE_NAME 2>$null
& $NSSM remove $SERVICE_NAME confirm 2>$null

& $NSSM install $SERVICE_NAME $PYTHON "$PROJECT_DIR\backend\main.py"
& $NSSM set $SERVICE_NAME AppDirectory "$PROJECT_DIR\backend"
& $NSSM set $SERVICE_NAME DisplayName "Distributed PBFT Demo"
& $NSSM set $SERVICE_NAME Description "PBFT consensus demo web application"
& $NSSM set $SERVICE_NAME Start SERVICE_AUTO_START
& $NSSM set $SERVICE_NAME AppStdout "$PROJECT_DIR\server.log"
& $NSSM set $SERVICE_NAME AppStderr "$PROJECT_DIR\server.log"
& $NSSM start $SERVICE_NAME

# 开放防火墙端口
Write-Host "[4/4] 开放防火墙端口 8080..."
netsh advfirewall firewall delete rule name="PBFT Demo" >$null 2>&1
netsh advfirewall firewall add rule name="PBFT Demo" dir=in action=allow protocol=TCP localport=8080

# 获取本机 IP
$IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } | Select-Object -First 1).IPAddress

Write-Host "`n=== 部署完成 ===" -ForegroundColor Green
Write-Host "访问地址: http://${IP}:8080"
Write-Host ""
Write-Host "常用命令:"
Write-Host "  查看日志: Get-Content $PROJECT_DIR\server.log -Wait"
Write-Host "  重启服务: Restart-Service $SERVICE_NAME"
Write-Host "  停止服务: Stop-Service $SERVICE_NAME"
Write-Host "  查看状态: Get-Service $SERVICE_NAME"
pause
