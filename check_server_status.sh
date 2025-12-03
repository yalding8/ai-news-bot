#!/bin/bash
# AI News Bot - 服务器状态检查脚本
# Server Status Check Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 读取配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f ".deployrc" ]; then
    source .deployrc
else
    echo -e "${RED}错误: 配置文件 .deployrc 不存在${NC}"
    exit 1
fi

# 日志函数
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_info() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_section() {
    echo -e "\n${CYAN}▶ $1${NC}"
    echo -e "${CYAN}$(printf '─%.0s' {1..50})${NC}"
}

# 显示检查信息
print_header "🔍 AI News Bot - 服务器状态检查"
echo "服务器: $SERVER_USER@$SERVER_IP:$SERVER_PORT"
echo "部署目录: $REMOTE_DIR"
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"

# 1. 测试SSH连接
print_section "1. SSH连接测试"
if ssh -p $SERVER_PORT -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
    $SERVER_USER@$SERVER_IP "echo 'SSH连接成功'" > /dev/null 2>&1; then
    print_info "SSH连接正常"
else
    print_error "SSH连接失败，请检查网络或服务器配置"
    exit 1
fi

# 2. 检查服务器基本信息
print_section "2. 服务器基本信息"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << 'ENDSSH'
echo "主机名: $(hostname)"
echo "操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "内核版本: $(uname -r)"
echo "运行时长: $(uptime -p)"
echo "当前时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "时区: $(timedatectl | grep "Time zone" | awk '{print $3}')"
ENDSSH

# 3. 检查定时任务配置
print_section "3. 定时任务配置 (Crontab)"
echo -e "${CYAN}当前配置的定时任务:${NC}"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP "crontab -l 2>/dev/null || echo '未配置定时任务'"

# 4. 检查代码版本和最后更新时间
print_section "4. 代码部署信息"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << ENDSSH
if [ -d "$REMOTE_DIR" ]; then
    echo "✓ 部署目录存在: $REMOTE_DIR"
    echo ""
    echo "最后修改时间:"
    ls -lht "$REMOTE_DIR"/*.py 2>/dev/null | head -5 | awk '{print "  " \$9 " - " \$6, \$7, \$8}'
    echo ""

    if [ -d "$REMOTE_DIR/.git" ]; then
        cd "$REMOTE_DIR"
        echo "Git信息:"
        echo "  分支: \$(git branch --show-current 2>/dev/null || echo '未知')"
        echo "  最后提交: \$(git log -1 --pretty=format:'%h - %s (%cr)' 2>/dev/null || echo '未知')"
    else
        echo "注意: 不是Git仓库"
    fi

    if [ -f "$REMOTE_DIR/.env" ]; then
        echo ""
        echo "✓ .env 配置文件存在"
        echo "  活跃主题: \$(grep ACTIVE_TOPICS "$REMOTE_DIR/.env" | cut -d'=' -f2)"
    else
        echo ""
        echo "✗ .env 配置文件缺失"
    fi
else
    echo "✗ 部署目录不存在: $REMOTE_DIR"
fi
ENDSSH

# 5. 检查Python环境
print_section "5. Python环境检查"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << ENDSSH
if [ -f "$REMOTE_DIR/venv/bin/python3" ]; then
    echo "✓ 虚拟环境存在"
    echo "  Python版本: \$($REMOTE_DIR/venv/bin/python3 --version)"
    echo ""
    echo "已安装的关键包:"
    $REMOTE_DIR/venv/bin/pip list 2>/dev/null | grep -E "requests|feedparser|python-dotenv|openai" | awk '{print "  " \$1 " - " \$2}'
else
    echo "✗ 虚拟环境不存在"
fi
ENDSSH

# 6. 检查日志文件
print_section "6. 运行日志检查"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << 'ENDSSH'
if [ -f "/var/log/ai-news.log" ]; then
    LOG_SIZE=$(du -h /var/log/ai-news.log | cut -f1)
    LOG_LINES=$(wc -l /var/log/ai-news.log | awk '{print $1}')
    echo "✓ 日志文件存在: /var/log/ai-news.log"
    echo "  文件大小: $LOG_SIZE"
    echo "  总行数: $LOG_LINES"
    echo ""
    echo "最近5次执行记录:"
    grep -E "开始执行|执行完成|成功|失败|ERROR" /var/log/ai-news.log 2>/dev/null | tail -10 | sed 's/^/  /'
    echo ""
    echo "最后一次执行时间:"
    tail -1 /var/log/ai-news.log 2>/dev/null | sed 's/^/  /'
else
    echo "✗ 日志文件不存在: /var/log/ai-news.log"
    echo "  这可能意味着定时任务还未执行过"
fi
ENDSSH

# 7. 检查运行进程
print_section "7. 进程状态检查"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << 'ENDSSH'
if pgrep -f "bot_wecom.py" > /dev/null; then
    echo "✓ 发现运行中的bot_wecom.py进程"
    ps aux | grep "[b]ot_wecom.py" | awk '{print "  PID: " $2 " | CPU: " $3 "% | MEM: " $4 "% | 启动时间: " $9}'
else
    echo "○ 当前没有bot_wecom.py进程运行（这是正常的，定时任务会自动启动）"
fi
ENDSSH

# 8. 检查系统资源
print_section "8. 系统资源使用"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << 'ENDSSH'
echo "CPU使用率:"
top -bn1 | grep "Cpu(s)" | sed 's/^/  /'

echo ""
echo "内存使用:"
free -h | grep -E "Mem|Swap" | awk '{print "  " $1 " 总计:" $2 " | 已用:" $3 " | 可用:" $7}'

echo ""
echo "磁盘使用:"
df -h / | tail -1 | awk '{print "  根分区: " $3 "/" $2 " (" $5 " 已使用)"}'
ENDSSH

# 9. 下次执行时间预测
print_section "9. 下次执行时间预测"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << 'ENDSSH'
CRON_SCHEDULE=$(crontab -l 2>/dev/null | grep "bot_wecom.py" | grep -v "^#" | head -1)
if [ -n "$CRON_SCHEDULE" ]; then
    HOUR=$(echo $CRON_SCHEDULE | awk '{print $2}')
    MINUTE=$(echo $CRON_SCHEDULE | awk '{print $1}')

    CURRENT_HOUR=$(date +%H)
    CURRENT_MINUTE=$(date +%M)

    echo "定时任务配置: 每天 ${HOUR}:${MINUTE:=00}"
    echo "当前服务器时间: $(date '+%H:%M')"

    # 计算距离下次执行的时间
    if [ $CURRENT_HOUR -lt $HOUR ] || ([ $CURRENT_HOUR -eq $HOUR ] && [ ${CURRENT_MINUTE:-0} -lt ${MINUTE:-0} ]); then
        echo "下次执行: 今天 ${HOUR}:${MINUTE:=00}"
    else
        echo "下次执行: 明天 ${HOUR}:${MINUTE:=00}"
    fi
else
    echo "未找到定时任务配置"
fi
ENDSSH

# 10. 生成状态报告
print_header "✅ 检查完成"
echo ""
echo "💡 提示："
echo "  - 查看完整日志: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'tail -100 /var/log/ai-news.log'"
echo "  - 手动测试运行: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'cd $REMOTE_DIR && source venv/bin/activate && python3 bot_wecom.py'"
echo "  - 编辑定时任务: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'crontab -e'"
echo ""

# 保存报告到本地
REPORT_FILE="/tmp/server_status_$(date +%Y%m%d_%H%M%S).txt"
echo "📄 完整报告已保存到: $REPORT_FILE"
