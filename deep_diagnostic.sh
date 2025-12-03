#!/bin/bash
# 深度SSH连接诊断
# 排查防火墙之外的连接问题

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source .deployrc

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════╗${NC}"
    printf "${BLUE}║${NC} %-46s ${BLUE}║${NC}\n" "$1"
    echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}\n"
}

print_section() {
    echo -e "\n${CYAN}▶ $1${NC}"
    echo -e "${CYAN}$(printf '─%.0s' {1..50})${NC}"
}

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_fail() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${CYAN}ℹ${NC} $1"; }

print_header "🔬 深度SSH连接诊断"
echo "服务器: ${GREEN}$SERVER_IP${NC}"
echo "诊断时间: $(date '+%Y-%m-%d %H:%M:%S')"

# ===== 测试1: 网络连通性详细测试 =====
print_section "1. 网络连通性详细测试"

echo "测试ICMP (ping)..."
if ping -c 3 -W 2 $SERVER_IP > /dev/null 2>&1; then
    print_success "ICMP响应正常"

    # 显示延迟信息
    PING_RESULT=$(ping -c 3 $SERVER_IP 2>&1 | tail -1)
    echo "  延迟信息: $PING_RESULT"
else
    print_fail "ICMP无响应（服务器可能禁用了ping）"
fi

# ===== 测试2: SSH端口详细测试 =====
print_section "2. SSH端口详细测试"

echo "测试端口22是否开放..."
if command -v nc > /dev/null 2>&1; then
    # 使用netcat测试，显示详细输出
    echo "执行: nc -v -z -w 5 $SERVER_IP 22"
    NC_OUTPUT=$(nc -v -z -w 5 $SERVER_IP 22 2>&1)
    NC_EXIT=$?

    echo "$NC_OUTPUT"

    if [ $NC_EXIT -eq 0 ]; then
        print_success "端口22可以访问"
    else
        print_fail "端口22无法访问"
        echo ""
        echo "可能的原因："
        echo "  1. SSH服务未启动"
        echo "  2. SSH服务监听在其他端口"
        echo "  3. 网络路径被阻断"
    fi
else
    print_info "nc命令不可用"
fi

# 尝试telnet测试
if command -v telnet > /dev/null 2>&1; then
    echo ""
    echo "使用telnet测试端口22..."
    (echo "quit"; sleep 1) | telnet $SERVER_IP 22 2>&1 | head -5
fi

# ===== 测试3: SSH详细连接尝试 =====
print_section "3. SSH详细连接测试"

echo "尝试SSH连接并保存详细日志..."
SSH_LOG="/tmp/ssh_debug_$(date +%s).log"

# 测试1: 使用密钥连接
echo ""
echo -e "${YELLOW}[测试A] 使用SSH密钥连接${NC}"
ssh -vvv -i ~/.ssh/id_ed25519 \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o BatchMode=yes \
    root@$SERVER_IP \
    "echo 'SSH Key Auth Success'" \
    > $SSH_LOG 2>&1 &
SSH_PID=$!

# 等待最多10秒
for i in {1..10}; do
    if ! ps -p $SSH_PID > /dev/null; then
        break
    fi
    sleep 1
    echo -n "."
done

# 如果进程还在运行，终止它
if ps -p $SSH_PID > /dev/null; then
    kill $SSH_PID 2>/dev/null || true
    print_fail "SSH连接超时"
else
    if grep -q "SSH Key Auth Success" $SSH_LOG; then
        print_success "SSH密钥认证成功！"
        SSH_KEY_OK=true
    else
        print_fail "SSH密钥认证失败"
        SSH_KEY_OK=false
    fi
fi

echo ""
echo -e "${YELLOW}SSH详细日志分析:${NC}"

# 分析SSH日志中的关键错误
if [ -f "$SSH_LOG" ]; then
    # 检查连接阶段
    if grep -q "Connection timed out" $SSH_LOG; then
        print_fail "连接超时 - 网络路径被阻断或SSH服务未运行"
    fi

    if grep -q "Connection refused" $SSH_LOG; then
        print_fail "连接被拒绝 - SSH服务未在端口22监听"
    fi

    if grep -q "Permission denied" $SSH_LOG; then
        print_fail "权限被拒绝 - SSH密钥不匹配或服务器不接受密钥认证"
    fi

    if grep -q "No route to host" $SSH_LOG; then
        print_fail "无路由到主机 - 网络配置问题"
    fi

    # 显示TCP连接状态
    echo ""
    echo "TCP连接尝试:"
    grep -i "connecting to\|connected to\|connection timed out\|connection refused" $SSH_LOG | head -5 | sed 's/^/  /'

    # 显示SSH协议交互
    echo ""
    echo "SSH协议交互:"
    grep -i "remote protocol version\|ssh protocol\|kex_exchange_identification" $SSH_LOG | head -5 | sed 's/^/  /'

    # 显示认证尝试
    echo ""
    echo "认证尝试:"
    grep -i "authentication\|publickey\|password" $SSH_LOG | head -5 | sed 's/^/  /'
fi

# ===== 测试4: 检查本地SSH密钥 =====
print_section "4. 本地SSH密钥检查"

if [ -f ~/.ssh/id_ed25519 ]; then
    print_success "SSH私钥存在: ~/.ssh/id_ed25519"

    # 检查密钥权限
    KEY_PERMS=$(stat -f "%Lp" ~/.ssh/id_ed25519 2>/dev/null || stat -c "%a" ~/.ssh/id_ed25519 2>/dev/null)
    if [ "$KEY_PERMS" = "600" ]; then
        print_success "密钥权限正确 (600)"
    else
        print_fail "密钥权限不正确: $KEY_PERMS (应该是600)"
        echo "  修复命令: chmod 600 ~/.ssh/id_ed25519"
    fi

    # 显示公钥
    if [ -f ~/.ssh/id_ed25519.pub ]; then
        echo ""
        echo "本地公钥内容:"
        cat ~/.ssh/id_ed25519.pub | sed 's/^/  /'
        echo ""
        echo -e "${YELLOW}重要:${NC} 请确认这个公钥已添加到服务器的 ~/.ssh/authorized_keys"
    fi
else
    print_fail "SSH私钥不存在"
fi

# ===== 测试5: 尝试其他常见SSH端口 =====
print_section "5. 检查SSH是否在其他端口"

echo "测试常见的SSH端口..."
for port in 2222 22022 2200; do
    if nc -z -w 2 $SERVER_IP $port 2>/dev/null; then
        print_success "端口 $port 开放！SSH可能在此端口"
    fi
done

# ===== 测试6: DNS解析检查 =====
print_section "6. DNS解析检查"

echo "检查IP地址解析..."
RESOLVED_IP=$(host $SERVER_IP 2>/dev/null | grep "has address" | awk '{print $4}' || echo $SERVER_IP)
echo "目标IP: $SERVER_IP"
echo "解析结果: $RESOLVED_IP"

if [ "$SERVER_IP" = "$RESOLVED_IP" ]; then
    print_success "IP地址无需解析"
else
    print_info "IP地址经过了解析"
fi

# ===== 测试7: 路由追踪 =====
print_section "7. 网络路径追踪"

echo "追踪到服务器的网络路径（前10跳）..."
echo ""
if command -v traceroute > /dev/null 2>&1; then
    traceroute -m 10 -w 2 $SERVER_IP 2>&1 | head -12 | sed 's/^/  /'
else
    print_info "traceroute命令不可用"
fi

# ===== 诊断总结 =====
print_header "📋 诊断总结和建议"

echo -e "${YELLOW}可能的问题原因:${NC}"
echo ""

# 根据日志分析给出具体建议
if [ -f "$SSH_LOG" ]; then
    if grep -q "Connection timed out" $SSH_LOG; then
        echo "❌ ${RED}最可能原因: 网络连接超时${NC}"
        echo ""
        echo "可能的解决方案："
        echo "  1. 使用DigitalOcean Web Console直接访问服务器"
        echo "  2. 检查DigitalOcean Droplet是否正在运行"
        echo "  3. 重启SSH服务: sudo systemctl restart ssh"
        echo "  4. 检查服务器的网络配置"
        echo ""
    elif grep -q "Connection refused" $SSH_LOG; then
        echo "❌ ${RED}最可能原因: SSH服务未运行${NC}"
        echo ""
        echo "通过Web Console登录后执行："
        echo "  sudo systemctl status ssh"
        echo "  sudo systemctl start ssh"
        echo ""
    elif grep -q "Permission denied" $SSH_LOG; then
        echo "❌ ${RED}最可能原因: SSH密钥认证失败${NC}"
        echo ""
        echo "解决方案："
        echo "  1. 通过Web Console登录服务器"
        echo "  2. 将你的公钥添加到服务器:"
        echo "     echo '$(cat ~/.ssh/id_ed25519.pub)' >> ~/.ssh/authorized_keys"
        echo "  3. 设置正确的权限:"
        echo "     chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
        echo ""
    fi
else
    echo "❌ ${RED}无法生成SSH日志，连接可能在网络层就失败了${NC}"
    echo ""
    echo "建议："
    echo "  1. 检查你的网络连接"
    echo "  2. 尝试使用VPN或其他网络"
    echo "  3. 检查DigitalOcean控制台中Droplet的状态"
    echo ""
fi

# ===== 推荐操作 =====
echo -e "${CYAN}推荐的下一步操作:${NC}"
echo ""
echo "1️⃣  访问DigitalOcean控制台:"
echo "   https://cloud.digitalocean.com/droplets"
echo ""
echo "2️⃣  使用Web Console访问服务器:"
echo "   在Droplet页面 → Access → Launch Droplet Console"
echo ""
echo "3️⃣  在Web Console中执行以下命令检查SSH服务:"
echo "   sudo systemctl status ssh"
echo "   sudo netstat -tlnp | grep :22"
echo "   sudo journalctl -u ssh -n 50"
echo ""
echo "4️⃣  检查服务器的authorized_keys:"
echo "   cat ~/.ssh/authorized_keys"
echo ""
echo "5️⃣  如果SSH服务正常，添加你的公钥:"
echo "   mkdir -p ~/.ssh"
echo "   echo '$(cat ~/.ssh/id_ed25519.pub 2>/dev/null)' >> ~/.ssh/authorized_keys"
echo "   chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
echo ""

echo -e "${BLUE}详细日志已保存到: $SSH_LOG${NC}"
echo "如需帮助，请将日志内容发送给我分析"
echo ""
