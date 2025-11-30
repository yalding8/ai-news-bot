#!/bin/bash
# AI News Bot - 一键部署脚本
# One-click deployment script to Aliyun server

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# 读取配置文件
if [ -f ".deployrc" ]; then
    source .deployrc
    log_info "已加载配置文件 .deployrc"
else
    log_error "配置文件 .deployrc 不存在！"
    exit 1
fi

# 显示部署信息
log_step "🚀 AI News Bot - 一键部署"
echo "服务器: $SERVER_USER@$SERVER_IP:$SERVER_PORT"
echo "目标目录: $REMOTE_DIR"
echo "备份目录: $BACKUP_DIR"
echo ""
read -p "确认部署？(yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log_warn "部署已取消"
    exit 0
fi

# 1. 检查必要文件
log_step "📋 步骤 1/6: 检查本地文件"
REQUIRED_FILES=(
    "bot_wecom.py"
    "news_fetcher.py"
    "config.py"
    "requirements.txt"
    "server_deploy.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_info "✓ $file"
    else
        log_error "✗ $file 不存在"
        exit 1
    fi
done

# 2. 打包代码
log_step "📦 步骤 2/6: 打包代码"
PACKAGE_NAME="ai-news-bot-deploy.tar.gz"

# 排除不需要的文件和目录
EXCLUDE_PATTERNS=(
    "--exclude=venv"
    "--exclude=__pycache__"
    "--exclude=*.pyc"
    "--exclude=*.log"
    "--exclude=.git"
    "--exclude=.env"
    "--exclude=*.backup"
    "--exclude=.DS_Store"
    "--exclude=$PACKAGE_NAME"
)

log_info "打包源代码..."
tar -czf "/tmp/$PACKAGE_NAME" ${EXCLUDE_PATTERNS[@]} \
    *.py *.txt *.sh *.md .env.example 2>/dev/null || true

if [ -f "/tmp/$PACKAGE_NAME" ]; then
    PACKAGE_SIZE=$(du -h "/tmp/$PACKAGE_NAME" | cut -f1)
    log_info "打包完成: /tmp/$PACKAGE_NAME ($PACKAGE_SIZE)"
else
    log_error "打包失败"
    exit 1
fi

# 3. 测试服务器连接
log_step "🔌 步骤 3/6: 测试服务器连接"
log_info "连接到 $SERVER_IP..."

if ssh -p $SERVER_PORT \
    -o ConnectTimeout=30 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=60 \
    $SERVER_USER@$SERVER_IP "echo '连接成功'" > /dev/null 2>&1; then
    log_info "✓ 服务器连接正常"
else
    log_error "✗ 无法连接到服务器"
    log_info "请检查："
    log_info "  1. 云服务器防火墙/安全组是否开放22端口"
    log_info "  2. 服务器IP: $SERVER_IP"
    log_info "  3. SSH端口: $SERVER_PORT"
    log_info "  4. 用户名: $SERVER_USER"
    log_info "  5. SSH密码认证是否启用"
    log_info ""
    log_info "💡 调试建议："
    log_info "  尝试手动连接: ssh -v root@$SERVER_IP"
    exit 1
fi

# 4. 上传代码包
log_step "📤 步骤 4/6: 上传代码"
log_info "上传代码包到服务器..."

scp -P $SERVER_PORT -o StrictHostKeyChecking=no \
    "/tmp/$PACKAGE_NAME" \
    "$SERVER_USER@$SERVER_IP:/tmp/$PACKAGE_NAME"

if [ $? -eq 0 ]; then
    log_info "✓ 代码包上传成功"
else
    log_error "✗ 代码包上传失败"
    exit 1
fi

# 5. 上传服务器端部署脚本
log_info "上传部署脚本..."
scp -P $SERVER_PORT -o StrictHostKeyChecking=no \
    "server_deploy.sh" \
    "$SERVER_USER@$SERVER_IP:/tmp/server_deploy.sh"

# 6. 执行服务器端部署
log_step "🔧 步骤 5/6: 执行服务器端部署"
log_info "开始远程部署..."

ssh -p $SERVER_PORT -t $SERVER_USER@$SERVER_IP << ENDSSH
    set -e
    chmod +x /tmp/server_deploy.sh
    bash /tmp/server_deploy.sh "$REMOTE_DIR" "$BACKUP_DIR" "$MAX_BACKUPS"
ENDSSH

if [ $? -eq 0 ]; then
    log_info "✓ 远程部署成功"
else
    log_error "✗ 远程部署失败"
    log_info "可以通过以下命令查看服务器日志："
    log_info "  ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'tail -100 /var/log/ai-news.log'"
    exit 1
fi

# 7. 清理临时文件
log_step "🧹 步骤 6/6: 清理临时文件"
rm -f "/tmp/$PACKAGE_NAME"
log_info "清理本地临时文件"

ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP "rm -f /tmp/$PACKAGE_NAME /tmp/server_deploy.sh" || true
log_info "清理服务器临时文件"

# 8. 完成
log_step "✅ 部署完成！"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 部署成功！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📌 下一步操作："
echo ""
echo "1️⃣  测试运行"
echo "   ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP"
echo "   cd $REMOTE_DIR"
echo "   source venv/bin/activate"
echo "   python3 bot_wecom.py"
echo ""
echo "2️⃣  查看部署报告"
echo "   ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'cat /tmp/deploy_report.txt'"
echo ""
echo "3️⃣  查看日志"
echo "   ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'tail -f /var/log/ai-news.log'"
echo ""
echo "4️⃣  检查定时任务"
echo "   ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'crontab -l'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
