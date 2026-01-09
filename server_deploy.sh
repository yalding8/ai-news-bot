#!/bin/bash
# 服务器端部署脚本
# Server-side deployment script

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# 读取配置
REMOTE_DIR="${1:-/opt/apps/ai-news-bot}"
BACKUP_DIR="${2:-/opt/backups/ai-news-bot}"
MAX_BACKUPS="${3:-5}"

log_info "开始部署到目录: $REMOTE_DIR"

# 1. 创建备份目录
log_info "创建备份目录..."
sudo mkdir -p "$BACKUP_DIR"
sudo chown $USER:$USER "$BACKUP_DIR" 2>/dev/null || true

# 2. 备份当前版本
if [ -d "$REMOTE_DIR" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_NAME="backup_$TIMESTAMP"
    
    log_info "备份当前版本到: $BACKUP_DIR/$BACKUP_NAME"
    cp -r "$REMOTE_DIR" "$BACKUP_DIR/$BACKUP_NAME"
    
    # 清理旧备份（保留最新的 MAX_BACKUPS 个）
    log_info "清理旧备份（保留最新 $MAX_BACKUPS 个）..."
    cd "$BACKUP_DIR"
    ls -t | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -rf
    cd - > /dev/null
else
    log_warn "目标目录不存在，跳过备份"
    sudo mkdir -p "$REMOTE_DIR"
    sudo chown $USER:$USER "$REMOTE_DIR" 2>/dev/null || true
fi

# 3. 停止现有服务（如果正在运行）
log_info "检查并停止现有进程..."
pkill -f "python.*bot_wecom.py" || log_warn "没有发现运行中的 bot_wecom.py 进程"

sleep 2

# 4. 解压上传的代码
log_info "解压新代码..."
cd "$REMOTE_DIR"
if [ -f "/tmp/ai-news-bot-deploy.tar.gz" ]; then
    tar -xzf /tmp/ai-news-bot-deploy.tar.gz
    rm -f /tmp/ai-news-bot-deploy.tar.gz
    log_info "代码解压完成"
else
    log_error "未找到上传的代码包"
    exit 1
fi

# 5. 设置权限
log_info "设置文件权限..."
chmod +x *.sh 2>/dev/null || true
chmod 644 *.py 2>/dev/null || true

# 6. 检查并创建虚拟环境
if [ ! -d "venv" ]; then
    log_info "创建Python虚拟环境..."
    python3 -m venv venv
else
    log_info "虚拟环境已存在"
fi

# 7. 安装/更新依赖
log_info "安装Python依赖..."
source venv/bin/activate
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 8. 检查配置文件
if [ ! -f ".env" ]; then
    log_warn ".env 文件不存在！"
    if [ -f ".env.example" ]; then
        log_info "从备份恢复 .env 文件..."
        if [ -f "$BACKUP_DIR/backup_$TIMESTAMP/.env" ]; then
            cp "$BACKUP_DIR/backup_$TIMESTAMP/.env" .env
            log_info ".env 文件已从备份恢复"
        else
            log_warn "请手动配置 .env 文件"
            cp .env.example .env
        fi
    fi
else
    log_info ".env 配置文件存在"
fi

# 9. 测试运行
log_info "测试导入模块..."
python3 -c "import bot_wecom; import news_fetcher; import config" && \
    log_info "模块导入测试通过" || \
    log_error "模块导入测试失败，请检查代码"

# 10. 设置定时任务（北京时间 8:30 = UTC 00:30）
log_info "设置定时任务..."
CRON_CMD="30 0 * * * cd $REMOTE_DIR && $REMOTE_DIR/venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1"

# 检查定时任务是否已存在
if ! crontab -l 2>/dev/null | grep -q "bot_wecom.py"; then
    log_info "添加新的定时任务..."
    # 获取现有的crontab（如果有）
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    log_info "✓ 定时任务已添加: 每天早上9点执行"
else
    log_info "定时任务已存在，更新中..."
    # 删除旧的bot_wecom.py任务，添加新的
    (crontab -l 2>/dev/null | grep -v "bot_wecom.py"; echo "$CRON_CMD") | crontab -
    log_info "✓ 定时任务已更新"
fi

# 确认定时任务已设置
log_info "当前定时任务："
crontab -l 2>/dev/null | grep "bot_wecom.py" || log_warn "定时任务设置失败"

# 11. 生成部署报告
log_info "生成部署报告..."
cat > /tmp/deploy_report.txt << EOF
========================================
AI News Bot 部署报告
========================================
部署时间: $(date '+%Y-%m-%d %H:%M:%S')
部署目录: $REMOTE_DIR
备份目录: $BACKUP_DIR/$BACKUP_NAME

Python版本: $(python3 --version)
虚拟环境: $REMOTE_DIR/venv

已安装的包:
$(pip list | head -20)

文件清单:
$(ls -lh *.py *.sh 2>/dev/null | awk '{print $9, $5}')

配置状态:
- .env: $([ -f .env ] && echo "✓ 存在" || echo "✗ 缺失")
- requirements.txt: $([ -f requirements.txt ] && echo "✓ 存在" || echo "✗ 缺失")

定时任务:
$(crontab -l 2>/dev/null | grep -i "bot" || echo "未配置")

========================================
EOF

cat /tmp/deploy_report.txt

log_info "=========================================="
log_info "部署完成！ 🎉"
log_info "=========================================="
log_info "下一步操作："
log_info "1. 检查 .env 配置"
log_info "2. 运行测试: source venv/bin/activate && python3 bot_wecom.py"
log_info "3. 查看日志: tail -f /var/log/ai-news.log"
log_info "=========================================="
