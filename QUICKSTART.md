# 🚀 快速开始指南

> 1分钟了解如何发布代码更新

---

## 📦 标准发布流程（推荐）

```bash
# 一键发布：本地 -> GitHub -> 服务器
bash publish.sh "feat: 你的更新描述"
```

**就这么简单！** 脚本会自动完成：
1. ✅ Git提交并推送到GitHub
2. ✅ 打包代码并上传到服务器
3. ✅ 在服务器上部署更新
4. ✅ 验证部署结果

---

## 📝 提交信息规范

使用统一的提交格式：

```bash
# 新功能
bash publish.sh "feat: 添加新闻源"

# Bug修复
bash publish.sh "fix: 修复重复推送"

# 文档更新
bash publish.sh "docs: 更新README"

# 性能优化
bash publish.sh "perf: 优化AI总结"
```

---

## 🔍 常用命令

### 查看服务器日志
```bash
ssh root@157.245.51.54 'tail -50 /var/log/ai-news.log'
```

### 手动测试运行
```bash
ssh root@157.245.51.54 'cd /opt/apps/ai-news-bot/code && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py'
```

### 查看定时任务
```bash
ssh root@157.245.51.54 'crontab -l'
```

### 检查服务器状态
```bash
ssh root@157.245.51.54 'ls -lh /opt/apps/ai-news-bot/code/'
```

---

## ⚠️ 注意事项

1. **发布前测试**：确保代码在本地测试通过
2. **清晰描述**：提交信息要简洁明了
3. **确认目标**：确认要部署到生产环境
4. **查看日志**：发布后检查执行日志

---

## 📚 详细文档

需要更多信息？查看：
- [RELEASE.md](RELEASE.md) - 完整发布流程规范
- [README.md](README.md) - 项目总览和部署指南

---

**最后更新**: 2025-11-27
