@echo off
chcp 65001 >nul
echo === 分布式PBFT演示系统 ===

where python >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 python，请先安装 Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist "dist" (
    echo 错误: 未找到 dist/ 目录，请确认仓库克隆完整
    pause
    exit /b 1
)

echo 安装 Python 依赖...
pip install --user -r backend\requirements.txt -q

echo 检查端口 8000...
netstat -ano 2>nul | findstr ":8000 " > "%TEMP%\pbft_port.txt" 2>nul
for /f "usebackq tokens=5" %%a in ("%TEMP%\pbft_port.txt") do taskkill /F /PID %%a >nul 2>&1
del "%TEMP%\pbft_port.txt" >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo 启动服务，访问地址: http://localhost:8000
echo 按 Ctrl+C 停止
echo.

cd backend
python main.py
