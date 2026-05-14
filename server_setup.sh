#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="pbft-demo"
CURRENT_USER=$(whoami)

echo "=== PBFT 服务器部署 ==="
echo "项目路径: $PROJECT_DIR"
echo "运行用户: $CURRENT_USER"
echo ""

# 安装依赖
echo "[1/4] 安装系统依赖..."
sudo apt-get update -q
sudo apt-get install -y -q python3 python3-pip nginx

echo "[2/4] 安装 Python 依赖..."
pip3 install -r "$PROJECT_DIR/backend/requirements.txt" -q

# 创建 systemd 服务
echo "[3/4] 配置 systemd 服务..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=Distributed PBFT Demo
After=network.target

[Service]
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR/backend
ExecStart=/usr/bin/python3 $PROJECT_DIR/backend/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

# 配置 nginx
echo "[4/4] 配置 nginx..."
sudo tee /etc/nginx/sites-available/${SERVICE_NAME} > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "=== 部署完成 ==="
echo "访问地址: http://$(curl -s ifconfig.me 2>/dev/null || echo '服务器公网IP')"
echo ""
echo "常用命令:"
echo "  查看日志: sudo journalctl -u ${SERVICE_NAME} -f"
echo "  重启服务: sudo systemctl restart ${SERVICE_NAME}"
echo "  停止服务: sudo systemctl stop ${SERVICE_NAME}"
