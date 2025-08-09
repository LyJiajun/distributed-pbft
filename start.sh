#!/bin/bash

echo "🚀 启动分布式PBFT共识系统..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装Node.js"
    exit 1
fi

# 检查npm是否安装
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装，请先安装npm"
    exit 1
fi

echo "📦 安装前端依赖..."
npm install

echo "🐍 安装后端依赖..."
cd backend
pip install -r requirements.txt
cd ..

echo "🔧 启动后端服务..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

echo "⏳ 等待后端服务启动..."
sleep 3

echo "🌐 启动前端服务..."
npm run dev &
FRONTEND_PID=$!

echo "✅ 系统启动完成！"
echo "📱 前端地址: http://localhost:3000"
echo "🔧 后端地址: http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait 