#!/bin/bash
set -e

BACKEND_DIR="$(cd "$(dirname "$0")/backend" && pwd)"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== 分布式PBFT演示系统 ==="

# 检查 Python3
if ! command -v python3 &>/dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3.9+"
    echo "Mac 安装方法: brew install python"
    exit 1
fi

# 检查 dist 目录
if [ ! -d "$PROJECT_DIR/dist" ]; then
    echo "错误: 未找到 dist/ 目录，请确保已包含构建好的前端文件"
    exit 1
fi

# 安装 Python 依赖（首次运行）
echo "安装 Python 依赖..."
pip3 install -r "$BACKEND_DIR/requirements.txt" -q

# 启动
echo "启动服务..."
echo "访问地址: http://localhost:8000"
echo "局域网地址: http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'your-ip'):8000"
echo "按 Ctrl+C 停止"
echo ""

cd "$BACKEND_DIR"
python3 main.py
