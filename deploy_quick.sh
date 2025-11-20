#!/bin/bash
# 快速部署脚本 - 跳过连接测试
# 如果你确信服务器配置正确但连接测试失败，使用此脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_step() { echo -e "\n${BLUE}========================================${NC}\n${BLUE}$1${NC}\n${BLUE}========================================${NC}\n"; }

# 读取配置
source .deployrc

log_step "🚀 快速部署（跳过连接测试）"
echo "服务器: $SERVER_USER@$SERVER_IP:$SERVER_PORT"
echo ""
read -p "确认部署？(yes/no): " confirm
[ "$confirm" != "yes" ] && exit 0

# 打包
log_step "📦 打包代码"
PACKAGE_NAME="ai-news-bot-deploy.tar.gz"
tar -czf "/tmp/$PACKAGE_NAME" \
    --exclude=venv --exclude=__pycache__ --exclude=*.pyc --exclude=*.log \
    --exclude=.git --exclude=.env --exclude=*.backup --exclude=.DS_Store \
    *.py *.txt *.sh *.md .env.example 2>/dev/null || true
log_info "打包完成: $(du -h /tmp/$PACKAGE_NAME | cut -f1)"

# 上传
log_step "📤 上传代码和脚本"
scp -P $SERVER_PORT "/tmp/$PACKAGE_NAME" "$SERVER_USER@$SERVER_IP:/tmp/$PACKAGE_NAME"
scp -P $SERVER_PORT "server_deploy.sh" "$SERVER_USER@$SERVER_IP:/tmp/server_deploy.sh"

# 部署
log_step "🔧 执行部署"
ssh -p $SERVER_PORT -t $SERVER_USER@$SERVER_IP << ENDSSH
    set -e
    chmod +x /tmp/server_deploy.sh
    bash /tmp/server_deploy.sh "$REMOTE_DIR" "$BACKUP_DIR" "$MAX_BACKUPS"
ENDSSH

# 清理
rm -f "/tmp/$PACKAGE_NAME"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP "rm -f /tmp/$PACKAGE_NAME /tmp/server_deploy.sh" || true

log_step "✅ 部署完成！"
echo "测试运行: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'cd $REMOTE_DIR && source venv/bin/activate && python3 bot_wecom.py'"
