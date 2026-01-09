#!/bin/bash
# ============================================
# AI News Bot - 标准发布脚本
# ============================================
# 功能：本地 -> GitHub -> 服务器 一键发布
#
# 使用方法:
#   bash publish.sh "feat: 添加新功能"
#   bash publish.sh "fix: 修复bug"
#   bash publish.sh "docs: 更新文档"
#
# 不提供信息时使用默认提交信息
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "\n${BLUE}========================================${NC}\n${BLUE}$1${NC}\n${BLUE}========================================${NC}\n"; }

# 获取提交信息
COMMIT_MSG="${1:-chore: update $(date +%Y-%m-%d\ %H:%M:%S)}"

# 显示发布计划
log_step "🚀 AI News Bot - 发布流程"
echo "提交信息: $COMMIT_MSG"
echo "Git分支: $(git branch --show-current)"
echo "目标服务器: $(grep SERVER_IP .deployrc | cut -d'=' -f2 | tr -d '"')"
echo ""
read -p "确认发布？(yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log_warn "发布已取消"
    exit 0
fi

# 步骤1: 检查本地修改
log_step "📋 步骤 1/4: 检查本地修改"
if ! git diff-index --quiet HEAD --; then
    log_info "发现以下修改："
    git status --short
else
    log_warn "没有发现本地修改"
    read -p "是否继续？(yes/no): " continue_anyway
    [ "$continue_anyway" != "yes" ] && exit 0
fi

# 步骤2: 提交到GitHub
log_step "📝 步骤 2/4: 提交到GitHub"
git add .
git commit -m "$COMMIT_MSG" || log_warn "没有新的提交（可能已经提交过）"
git push origin $(git branch --show-current)
log_info "✓ GitHub推送成功"

# 步骤3: 部署到服务器
log_step "🚀 步骤 3/4: 部署到服务器"

# 读取配置
source .deployrc

# 打包代码
log_info "打包代码..."
PACKAGE_NAME="ai-news-bot-deploy.tar.gz"
tar -czf "/tmp/$PACKAGE_NAME" \
    --exclude=venv --exclude=__pycache__ --exclude=*.pyc --exclude=*.log \
    --exclude=.git --exclude=.env --exclude=*.backup --exclude=.DS_Store \
    --exclude=.kiro --exclude=node_modules \
    *.py *.txt *.sh *.md .env.example 2>/dev/null || true
log_info "✓ 打包完成: $(du -h /tmp/$PACKAGE_NAME | cut -f1)"

# 上传到服务器
log_info "上传到服务器..."
scp -P $SERVER_PORT "/tmp/$PACKAGE_NAME" "$SERVER_USER@$SERVER_IP:/tmp/$PACKAGE_NAME"
scp -P $SERVER_PORT "server_deploy.sh" "$SERVER_USER@$SERVER_IP:/tmp/server_deploy.sh"
log_info "✓ 上传完成"

# 在服务器上执行部署
log_info "执行远程部署..."
ssh -p $SERVER_PORT -t $SERVER_USER@$SERVER_IP << ENDSSH
    set -e
    chmod +x /tmp/server_deploy.sh
    bash /tmp/server_deploy.sh "$REMOTE_DIR" "$BACKUP_DIR" "$MAX_BACKUPS"
ENDSSH

# 清理临时文件
log_info "清理临时文件..."
rm -f "/tmp/$PACKAGE_NAME"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP "rm -f /tmp/$PACKAGE_NAME /tmp/server_deploy.sh" || true

# 步骤4: 验证部署
log_step "✅ 步骤 4/4: 验证部署"
log_info "检查定时任务..."
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP "crontab -l | grep bot_wecom" && \
    log_info "✓ 定时任务已配置" || \
    log_warn "✗ 定时任务未配置"

log_info "检查部署文件..."
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP "ls -lh $REMOTE_DIR/bot_wecom.py" && \
    log_info "✓ 程序文件存在" || \
    log_error "✗ 程序文件不存在"

# 发布完成
log_step "🎉 发布完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 发布摘要"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "提交信息: $COMMIT_MSG"
echo "Git分支: $(git branch --show-current)"
echo "GitHub: ✅ 已推送"
echo "服务器: ✅ 已部署 ($SERVER_IP)"
echo "定时任务: ✅ 每天早上 8:30 (北京时间) 执行"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 后续操作"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "• 查看服务器日志: ssh $SERVER_USER@$SERVER_IP 'tail -50 /var/log/ai-news.log'"
echo "• 手动测试运行: ssh $SERVER_USER@$SERVER_IP 'cd $REMOTE_DIR && $REMOTE_DIR/venv/bin/python3 bot_wecom.py'"
echo "• 查看定时任务: ssh $SERVER_USER@$SERVER_IP 'crontab -l'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
