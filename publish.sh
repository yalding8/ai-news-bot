#!/bin/bash
# 一键发布脚本：提交到GitHub + 部署到云服务器
# 使用方法: bash publish.sh "提交信息"

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取提交信息（如果没有提供，使用默认信息）
COMMIT_MSG="${1:-Update: Auto publish $(date +%Y-%m-%d\ %H:%M:%S)}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🚀 一键发布流程${NC}"
echo -e "${GREEN}========================================${NC}"

# 步骤1: 提交到GitHub
echo -e "\n${YELLOW}📝 步骤1: 提交到GitHub...${NC}"
git add .
git commit -m "$COMMIT_MSG"
git push

echo -e "${GREEN}✅ GitHub推送成功${NC}"

# 步骤2: 部署到云服务器
echo -e "\n${YELLOW}🚀 步骤2: 部署到云服务器...${NC}"
yes | bash deploy_quick.sh

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 发布完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "提交信息: $COMMIT_MSG"
echo -e "GitHub: ✅ 已推送"
echo -e "云服务器: ✅ 已部署"
