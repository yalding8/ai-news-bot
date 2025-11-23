#!/bin/bash
# 云服务器代码同步脚本
# 使用方法: ./sync_to_server.sh [服务器IP]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务器配置
SERVER_IP=${1:-"your_server_ip"}
SERVER_USER="root"
PROJECT_PATH="/opt/apps/ai-news-bot"

echo -e "${BLUE}🚀 开始同步代码到云服务器...${NC}"
echo "服务器: ${SERVER_IP}"
echo "路径: ${PROJECT_PATH}"
echo "=" * 50

# 检查服务器IP参数
if [ "$SERVER_IP" = "your_server_ip" ]; then
    echo -e "${RED}❌ 请提供服务器IP地址${NC}"
    echo "使用方法: ./sync_to_server.sh 你的服务器IP"
    exit 1
fi

# 1. 连接服务器并拉取最新代码
echo -e "${YELLOW}📡 1. 拉取最新代码...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
cd /opt/apps/ai-news-bot
echo "当前目录: $(pwd)"
echo "拉取前的提交: $(git log --oneline -1)"

# 拉取最新代码
git pull origin main

echo "拉取后的提交: $(git log --oneline -1)"
EOF

# 2. 更新Python依赖
echo -e "${YELLOW}📦 2. 更新Python依赖...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
cd /opt/apps/ai-news-bot
source venv/bin/activate

# 安装新依赖
pip install -r requirements.txt --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "✅ 依赖更新完成"
EOF

# 3. 检查配置文件
echo -e "${YELLOW}⚙️ 3. 检查配置文件...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
cd /opt/apps/ai-news-bot

if [ -f .env ]; then
    echo "✅ .env 配置文件存在"
    echo "配置项数量: $(grep -c "=" .env)"
else
    echo "❌ .env 配置文件不存在，请创建配置文件"
    echo "参考 .env.example 创建 .env 文件"
fi
EOF

# 4. 测试运行
echo -e "${YELLOW}🧪 4. 测试运行...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
cd /opt/apps/ai-news-bot
source venv/bin/activate

# 测试新闻获取功能
echo "测试新闻缓存模块..."
python3 -c "
import sys
sys.path.append('.')
from news_cache import news_cache
stats = news_cache.get_cache_stats()
print(f'缓存统计: {stats[\"total_records\"]} 条记录')
"

echo "✅ 测试完成"
EOF

# 5. 重启定时任务（如果需要）
echo -e "${YELLOW}⏰ 5. 检查定时任务...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
echo "当前定时任务:"
crontab -l | grep ai-news-bot || echo "未找到相关定时任务"
EOF

echo -e "${GREEN}🎉 代码同步完成！${NC}"
echo ""
echo "📋 同步内容:"
echo "  ✅ 新闻获取优化（AI + 教育新闻源扩展）"
echo "  ✅ 智能缓存去重系统"
echo "  ✅ 时间过滤机制"
echo "  ✅ 新增python-dateutil依赖"
echo ""
echo "💡 下一步:"
echo "  1. 检查 .env 配置文件是否完整"
echo "  2. 测试运行: python3 bot_wecom.py"
echo "  3. 查看日志: tail -f /var/log/ai-news.log"
echo ""
echo "🔗 远程连接:"
echo "  ssh ${SERVER_USER}@${SERVER_IP}"
echo "  cd ${PROJECT_PATH}"