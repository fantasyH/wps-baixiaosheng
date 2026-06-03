#!/bin/bash
# ===== WPS百晓生 - 阿里云ECS一键部署脚本 =====
# 用法: chmod +x deploy.sh && ./deploy.sh
set -e

echo "=========================================="
echo "  WPS百晓生 - 服务器部署"
echo "=========================================="

# 1. 检查环境
echo ""
echo "[1/5] 检查环境..."
command -v python3 >/dev/null 2>&1 || { echo "需要 Python3，请先安装"; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "需要 pip3，请先安装"; exit 1; }

# 2. 安装依赖
echo ""
echo "[2/5] 安装依赖..."
pip3 install flask flask-cors requests gunicorn -q

# 检查 Node.js (用于前端构建)
if command -v node &>/dev/null && command -v npm &>/dev/null; then
    echo "  Node.js: $(node -v), npm: $(npm -v)"
else
    echo "  ⚠️ Node.js 未安装，跳过前端构建（将使用旧版前端）"
    SKIP_FRONTEND=1
fi

# 3. 下载项目代码
echo ""
echo "[3/5] 下载项目代码..."
if [ -d "wps-baixiaosheng" ]; then
    echo "  目录已存在，跳过下载"
else
    git clone https://github.com/fantasyH/wps-baixiaosheng.git
fi
cd wps-baixiaosheng

# 3.5 构建前端（React v2）
echo ""
echo "[3.5/5] 构建前端..."
if [ -z "$SKIP_FRONTEND" ] && [ -d "frontend" ]; then
    cd frontend
    npm install --silent
    npx vite build
    cd ..
    echo "  ✅ React 前端构建完成"
else
    echo "  跳过前端构建，使用旧版前端"
fi

# 4. 配置环境变量
echo ""
echo "[4/5] 配置环境变量..."
if [ ! -f ".env" ]; then
    echo ""
    echo "  请从浏览器获取 WPS_SID:"
    echo "  打开 https://365.kdocs.cn → F12 → 控制台 → 粘贴:"
    echo "    document.cookie.match(/wps_sid=([^;]+)/)?.[1]"
    echo ""
    read -p "  请输入 WPS_SID: " wps_sid
    echo "WPS_SID=$wps_sid" > .env
    echo "  .env 文件已创建"
fi
source .env

# 5. 启动服务
echo ""
echo "[5/5] 启动服务..."
PORT=${PORT:-5099}
echo "  监听端口: $PORT"
echo "  访问地址: http://$(curl -s ifconfig.me):$PORT"
echo ""

# 停止旧进程
pkill -f "gunicorn.*app:app" 2>/dev/null || true
sleep 1

# 启动
nohup gunicorn app:app \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    > /tmp/wps-baixiaosheng.log 2>&1 &

echo "  服务已启动！PID: $!"
echo "  日志: tail -f /tmp/wps-baixiaosheng.log"
echo ""
echo "=========================================="
echo "  部署完成！"
echo "  浏览器访问: http://$(curl -s ifconfig.me):$PORT"
echo "=========================================="
