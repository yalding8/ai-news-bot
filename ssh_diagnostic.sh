#!/bin/bash
# SSH连接诊断和配置向导
# SSH Diagnostic and Configuration Wizard

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# 读取配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f ".deployrc" ]; then
    source .deployrc
else
    echo -e "${RED}错误: 配置文件 .deployrc 不存在${NC}"
    exit 1
fi

# 辅助函数
print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════╗${NC}"
    printf "${BLUE}║${NC} %-46s ${BLUE}║${NC}\n" "$1"
    echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}\n"
}

print_step() {
    echo -e "\n${CYAN}▶ 步骤 $1${NC}"
    echo -e "${CYAN}$(printf '─%.0s' {1..50})${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

# 开始诊断
print_header "🔧 SSH连接诊断向导"
echo "目标服务器: ${GREEN}$SERVER_USER@$SERVER_IP:$SERVER_PORT${NC}"
echo "诊断时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ==================== 第1步: 基础网络连接测试 ====================
print_step "1/6: 基础网络连接测试 (ping)"

echo -e "${CYAN}测试服务器是否可达...${NC}"
if ping -c 3 -W 5 $SERVER_IP > /dev/null 2>&1; then
    print_success "服务器可以ping通（网络层连接正常）"
    PING_OK=true
else
    print_fail "服务器无法ping通"
    print_warn "可能原因："
    echo "  1. 服务器禁用了ICMP响应（这是正常的安全设置）"
    echo "  2. 服务器已关闭"
    echo "  3. 网络路径被防火墙阻断"
    PING_OK=false
fi

# ==================== 第2步: SSH端口连接测试 ====================
print_step "2/6: SSH端口连接测试 (Port 22)"

echo -e "${CYAN}测试SSH端口是否开放...${NC}"
if command -v nc > /dev/null 2>&1; then
    if timeout 5 nc -z $SERVER_IP $SERVER_PORT 2>/dev/null; then
        print_success "SSH端口 $SERVER_PORT 可以访问"
        PORT_OK=true
    else
        print_fail "SSH端口 $SERVER_PORT 无法访问"
        print_warn "可能原因："
        echo "  1. 防火墙阻止了你的IP地址"
        echo "  2. SSH服务未启动"
        echo "  3. 端口号不正确"
        PORT_OK=false
    fi
else
    print_warn "nc命令不可用，跳过端口测试"
    PORT_OK=unknown
fi

# ==================== 第3步: 检查本地SSH配置 ====================
print_step "3/6: 检查本地SSH配置"

echo -e "${CYAN}检查SSH密钥...${NC}"
if [ -f "$HOME/.ssh/id_ed25519" ]; then
    print_success "找到SSH密钥: ~/.ssh/id_ed25519"
    SSH_KEY="$HOME/.ssh/id_ed25519"
    echo "  公钥指纹: $(ssh-keygen -lf $SSH_KEY.pub 2>/dev/null | awk '{print $2}')"
elif [ -f "$HOME/.ssh/id_rsa" ]; then
    print_success "找到SSH密钥: ~/.ssh/id_rsa"
    SSH_KEY="$HOME/.ssh/id_rsa"
    echo "  公钥指纹: $(ssh-keygen -lf $SSH_KEY.pub 2>/dev/null | awk '{print $2}')"
else
    print_warn "未找到SSH密钥"
    SSH_KEY=""
fi

echo ""
echo -e "${CYAN}检查SSH配置文件...${NC}"
if [ -f "$HOME/.ssh/config" ]; then
    print_success "SSH配置文件存在"
    if grep -q "$SERVER_IP" "$HOME/.ssh/config"; then
        print_info "配置文件中已有该服务器的配置"
    else
        print_info "配置文件中没有该服务器的配置"
    fi
else
    print_warn "SSH配置文件不存在"
fi

# ==================== 第4步: SSH连接详细测试 ====================
print_step "4/6: SSH连接详细测试"

echo -e "${CYAN}尝试SSH连接（详细模式）...${NC}"
echo ""

if [ -n "$SSH_KEY" ]; then
    SSH_CMD="ssh -v -i $SSH_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $SERVER_USER@$SERVER_IP -p $SERVER_PORT 'echo Connection successful'"
else
    SSH_CMD="ssh -v -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $SERVER_USER@$SERVER_IP -p $SERVER_PORT 'echo Connection successful'"
fi

echo -e "${YELLOW}执行命令: $SSH_CMD${NC}"
echo ""

# 保存SSH输出到临时文件
SSH_OUTPUT="/tmp/ssh_diagnostic_output.log"
if timeout 15 $SSH_CMD > $SSH_OUTPUT 2>&1; then
    print_success "SSH连接成功！"
    SSH_OK=true
else
    print_fail "SSH连接失败"
    SSH_OK=false

    echo ""
    echo -e "${YELLOW}SSH错误详情:${NC}"
    if [ -f "$SSH_OUTPUT" ]; then
        # 提取关键错误信息
        grep -i "error\|timeout\|refused\|denied" $SSH_OUTPUT | head -10 | sed 's/^/  /'
    fi
fi

# ==================== 第5步: 诊断结果分析 ====================
print_step "5/6: 诊断结果分析"

echo -e "${CYAN}连接状态汇总:${NC}"
echo ""
printf "  %-30s : " "网络可达性 (Ping)"
if [ "$PING_OK" = true ]; then echo -e "${GREEN}✓ 正常${NC}"; else echo -e "${RED}✗ 失败${NC}"; fi

printf "  %-30s : " "SSH端口可访问性"
if [ "$PORT_OK" = true ]; then echo -e "${GREEN}✓ 正常${NC}";
elif [ "$PORT_OK" = false ]; then echo -e "${RED}✗ 失败${NC}";
else echo -e "${YELLOW}○ 未测试${NC}"; fi

printf "  %-30s : " "SSH密钥配置"
if [ -n "$SSH_KEY" ]; then echo -e "${GREEN}✓ 已配置${NC}"; else echo -e "${YELLOW}○ 未配置${NC}"; fi

printf "  %-30s : " "SSH连接"
if [ "$SSH_OK" = true ]; then echo -e "${GREEN}✓ 成功${NC}"; else echo -e "${RED}✗ 失败${NC}"; fi

echo ""

# 根据诊断结果给出建议
if [ "$SSH_OK" = true ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 SSH连接正常！可以正常使用服务器          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    print_info "现在可以运行服务器状态检查脚本："
    echo "  bash check_server_status.sh"
else
    echo -e "${RED}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ⚠️  SSH连接失败，需要进一步处理              ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════╝${NC}"
    echo ""

    print_info "建议的解决步骤："
    echo ""

    if [ "$PORT_OK" = false ]; then
        echo -e "${YELLOW}问题: SSH端口无法访问${NC}"
        echo "  解决方案："
        echo "    1. 登录DigitalOcean控制台 (https://cloud.digitalocean.com)"
        echo "    2. 进入 Networking → Firewalls"
        echo "    3. 添加SSH规则: Port 22, Source: 你的IP或 0.0.0.0/0 (所有IP)"
        echo "    4. 或者使用DigitalOcean的Web Console直接访问服务器"
        echo ""
    fi

    if [ -z "$SSH_KEY" ]; then
        echo -e "${YELLOW}问题: 未找到SSH密钥${NC}"
        echo "  解决方案："
        echo "    1. 生成新的SSH密钥:"
        echo "       ssh-keygen -t ed25519 -C 'your_email@example.com'"
        echo "    2. 将公钥添加到服务器:"
        echo "       通过DigitalOcean控制台或Web Console添加"
        echo ""
    fi

    echo -e "${CYAN}可选: 尝试密码登录${NC}"
    echo "  如果你有root密码，可以尝试："
    echo "    ssh root@$SERVER_IP"
    echo "  然后输入密码"
    echo ""
fi

# ==================== 第6步: 生成SSH配置 ====================
print_step "6/6: 生成SSH配置建议"

echo -e "${CYAN}为了简化以后的连接，建议添加SSH配置${NC}"
echo ""

SSH_CONFIG_ENTRY="Host ai-news-bot
    HostName $SERVER_IP
    User $SERVER_USER
    Port $SERVER_PORT"

if [ -n "$SSH_KEY" ]; then
    SSH_CONFIG_ENTRY="${SSH_CONFIG_ENTRY}
    IdentityFile $SSH_KEY"
fi

SSH_CONFIG_ENTRY="${SSH_CONFIG_ENTRY}
    AddKeysToAgent yes
    ServerAliveInterval 60
    ServerAliveCountMax 3"

echo -e "${YELLOW}建议添加到 ~/.ssh/config 的配置:${NC}"
echo ""
echo "$SSH_CONFIG_ENTRY" | sed 's/^/  /'
echo ""

read -p "是否自动添加此配置到 ~/.ssh/config？(yes/no): " ADD_CONFIG

if [ "$ADD_CONFIG" = "yes" ] || [ "$ADD_CONFIG" = "y" ]; then
    # 备份现有配置
    if [ -f "$HOME/.ssh/config" ]; then
        cp "$HOME/.ssh/config" "$HOME/.ssh/config.backup.$(date +%Y%m%d_%H%M%S)"
        print_info "已备份现有配置到 ~/.ssh/config.backup.*"
    else
        touch "$HOME/.ssh/config"
        chmod 600 "$HOME/.ssh/config"
    fi

    # 检查是否已存在配置
    if grep -q "Host ai-news-bot" "$HOME/.ssh/config" 2>/dev/null; then
        print_warn "配置已存在，跳过添加"
    else
        echo "" >> "$HOME/.ssh/config"
        echo "# AI News Bot Server" >> "$HOME/.ssh/config"
        echo "$SSH_CONFIG_ENTRY" >> "$HOME/.ssh/config"
        print_success "SSH配置已添加到 ~/.ssh/config"
        print_info "现在可以使用简化命令连接: ssh ai-news-bot"
    fi
else
    print_info "跳过自动配置"
fi

# ==================== 诊断报告 ====================
echo ""
print_header "📄 诊断报告"

REPORT_FILE="/tmp/ssh_diagnostic_$(date +%Y%m%d_%H%M%S).txt"

cat > $REPORT_FILE << EOF
========================================
SSH连接诊断报告
========================================
诊断时间: $(date '+%Y-%m-%d %H:%M:%S')
目标服务器: $SERVER_USER@$SERVER_IP:$SERVER_PORT

诊断结果:
  - 网络可达性: $PING_OK
  - SSH端口访问: $PORT_OK
  - SSH密钥: $([ -n "$SSH_KEY" ] && echo "已配置 ($SSH_KEY)" || echo "未配置")
  - SSH连接: $SSH_OK

建议的SSH配置:
$SSH_CONFIG_ENTRY

详细日志:
$(cat $SSH_OUTPUT 2>/dev/null || echo "无")

========================================
EOF

print_info "完整报告已保存到: $REPORT_FILE"

# ==================== 后续步骤 ====================
echo ""
print_header "🎯 下一步操作"

if [ "$SSH_OK" = true ]; then
    echo "1️⃣  运行服务器状态检查:"
    echo "   bash check_server_status.sh"
    echo ""
    echo "2️⃣  手动连接到服务器:"
    if grep -q "Host ai-news-bot" "$HOME/.ssh/config" 2>/dev/null; then
        echo "   ssh ai-news-bot"
    else
        echo "   ssh $SERVER_USER@$SERVER_IP"
    fi
    echo ""
    echo "3️⃣  查看服务器日志:"
    echo "   ssh ai-news-bot 'tail -50 /var/log/ai-news.log'"
else
    echo "1️⃣  检查DigitalOcean控制台:"
    echo "   https://cloud.digitalocean.com/droplets"
    echo "   确认Droplet状态和IP地址"
    echo ""
    echo "2️⃣  使用Web Console访问:"
    echo "   在Droplet页面点击 'Access' → 'Launch Droplet Console'"
    echo ""
    echo "3️⃣  检查防火墙设置:"
    echo "   Networking → Firewalls → 添加SSH规则"
    echo ""
    echo "4️⃣  如果有密码，尝试密码登录:"
    echo "   ssh root@$SERVER_IP"
fi

echo ""
print_info "如需帮助，请查看诊断报告: $REPORT_FILE"
echo ""
