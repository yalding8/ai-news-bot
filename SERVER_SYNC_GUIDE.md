# 🚀 云服务器代码同步指南

## 📋 同步内容

本次更新包含以下重要改进：
- ✅ **智能缓存去重系统** - 避免24小时内重复推送
- ✅ **新闻源扩展** - AI新闻源从4个增加到9个，教育新闻源从3个增加到7个
- ✅ **时间过滤机制** - 只推送7天内的新闻
- ✅ **关键词优化** - 提高新闻匹配精度

## 🛠️ 方法一：自动同步脚本（推荐）

```bash
# 在本地运行
./sync_to_server.sh 你的服务器IP
```

## 🛠️ 方法二：手动同步

### 1. 连接服务器
```bash
ssh root@你的服务器IP
cd /opt/apps/ai-news-bot
```

### 2. 拉取最新代码
```bash
git pull origin main
```

### 3. 激活虚拟环境并更新依赖
```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 测试新功能
```bash
# 测试缓存系统
python3 -c "
from news_cache import news_cache
stats = news_cache.get_cache_stats()
print(f'缓存统计: {stats[\"total_records\"]} 条记录')
"

# 测试新闻获取
python3 -c "
from news_fetcher import get_real_news
news = get_real_news('ai', num=5)
print(f'获取到 {len(news)} 条AI新闻')
"
```

### 5. 运行测试
```bash
python3 bot_wecom.py
```

## 📊 验证同步结果

### 检查新文件
```bash
ls -la | grep -E "(news_cache|\.news_cache\.json)"
```
应该看到：
- `news_cache.py` - 缓存管理模块
- `.news_cache.json` - 缓存数据文件（运行后自动生成）

### 检查依赖
```bash
pip list | grep dateutil
```
应该看到：`python-dateutil 2.8.2`

### 检查新闻源
```bash
python3 -c "
from news_fetcher import NewsFetcher
fetcher = NewsFetcher()
print('AI新闻源数量:', len(fetcher.rss_feeds['ai']))
print('教育新闻源数量:', len(fetcher.rss_feeds['education']))
"
```
应该看到：
- AI新闻源数量: 8
- 教育新闻源数量: 7

## 🔧 故障排除

### 问题1：依赖安装失败
```bash
# 清理pip缓存
pip cache purge
pip install -r requirements.txt --upgrade --force-reinstall
```

### 问题2：权限问题
```bash
# 确保文件权限正确
chmod +x *.py
chown -R root:root /opt/apps/ai-news-bot
```

### 问题3：缓存文件问题
```bash
# 删除旧缓存（如果需要）
rm -f .news_cache.json
```

## 📝 运行日志

同步完成后，查看运行日志：
```bash
# 实时查看日志
tail -f /var/log/ai-news.log

# 查看最近的错误
grep -i "error\|失败" /var/log/ai-news.log | tail -10
```

## 🎯 预期改进效果

同步完成后，你应该看到：
1. **不再有重复推送** - 24小时内相同新闻不会重复推送
2. **新闻内容更丰富** - AI和教育新闻来源显著增加
3. **内容更及时** - 只推送最近7天的新闻
4. **智能提示** - 当没有新内容时会有友好提示

## 📞 技术支持

如果同步过程中遇到问题：
1. 检查网络连接
2. 确认Git仓库访问权限
3. 查看错误日志
4. 重新运行同步命令

---

**同步完成时间**: 2025-11-21  
**版本**: v2.1 - 智能去重优化版  
**状态**: ✅ 就绪部署