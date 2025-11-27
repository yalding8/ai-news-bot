# 📦 AI News Bot - 发布流程规范

> **必读**：所有代码更新必须按照本流程执行，确保发布的一致性和可追溯性。

---

## 📋 目录

- [发布流程概览](#发布流程概览)
- [标准发布命令](#标准发布命令)
- [Git提交规范](#git提交规范)
- [故障排查](#故障排查)
- [最佳实践](#最佳实践)

---

## 🎯 发布流程概览

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   本地开发   │  →  │   GitHub    │  →  │  服务器部署  │
│  (macOS)    │      │  (代码仓库)  │      │(DigitalOcean)│
└─────────────┘      └─────────────┘      └─────────────┘
      ↓                     ↓                     ↓
  编写代码              版本控制             自动化部署
  本地测试              代码备份             定时执行
```

**完整流程**：
1. ✅ **本地开发** → 编写代码、本地测试
2. ✅ **Git提交** → 提交到GitHub、版本控制
3. ✅ **自动部署** → 打包上传、服务器部署
4. ✅ **验证确认** → 检查部署、确认运行

---

## 🚀 标准发布命令

### 方法1: 一键发布（推荐）⭐

```bash
# 基本用法
bash publish.sh "feat: 添加新功能"

# 示例
bash publish.sh "feat: 添加教育新闻源"
bash publish.sh "fix: 修复新闻去重bug"
bash publish.sh "docs: 更新README"
```

**执行步骤**：
1. 检查本地修改
2. 提交到GitHub
3. 部署到服务器
4. 验证部署结果

### 方法2: 分步执行

如果需要更细粒度的控制：

```bash
# 步骤1: 提交到GitHub
git add .
git commit -m "feat: 添加新功能"
git push

# 步骤2: 部署到服务器
bash deploy_quick.sh
```

---

## 📝 Git提交规范

### 提交信息格式

```
<类型>: <简短描述>

[可选的详细说明]
```

### 提交类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加财经新闻源` |
| `fix` | Bug修复 | `fix: 修复新闻重复推送问题` |
| `docs` | 文档更新 | `docs: 更新部署文档` |
| `refactor` | 代码重构 | `refactor: 优化新闻获取逻辑` |
| `perf` | 性能优化 | `perf: 优化AI总结速度` |
| `test` | 测试相关 | `test: 添加新闻获取测试` |
| `chore` | 构建/工具 | `chore: 更新依赖包` |
| `style` | 代码格式 | `style: 格式化代码` |

### 提交示例

```bash
# ✅ 好的提交
git commit -m "feat: 添加Google AI博客RSS源"
git commit -m "fix: 修复新闻缓存过期时间错误"
git commit -m "docs: 更新DigitalOcean部署文档"

# ❌ 不好的提交
git commit -m "update"
git commit -m "修改"
git commit -m "fix bug"
```

---

## 🔧 服务器架构

### 目录结构

```
/opt/apps/ai-news-bot/
├── code/                    # 源代码目录
│   ├── bot_wecom.py        # 主程序
│   ├── news_fetcher.py     # 新闻获取模块
│   ├── ai_summarizer.py    # AI总结模块
│   └── config.py           # 配置文件
├── venv/                    # Python虚拟环境
├── logs/                    # 日志目录
└── .env                     # 环境变量配置

/opt/backups/ai-news-bot/   # 备份目录
└── backup_YYYYMMDD_HHMMSS/ # 按时间戳备份
```

### 定时任务

```bash
# 查看定时任务
ssh root@157.245.51.54 'crontab -l'

# 输出示例
0 9 * * * cd /opt/apps/ai-news-bot/code && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /var/log/ai-news.log 2>&1
```

**说明**：
- 时间：每天早上 9:00（北京时间）
- 工作目录：`/opt/apps/ai-news-bot/code`
- Python解释器：虚拟环境中的python3
- 日志输出：`/var/log/ai-news.log`

---

## 🐛 故障排查

### 问题1: 发布失败 - 无法连接服务器

**症状**：
```
[ERROR] 无法连接到服务器
```

**解决方案**：
1. 检查服务器IP配置：
   ```bash
   cat .deployrc | grep SERVER_IP
   # 应该显示: SERVER_IP="157.245.51.54"
   ```

2. 测试SSH连接：
   ```bash
   ssh root@157.245.51.54
   ```

3. 检查SSH密钥配置

### 问题2: 定时任务未执行

**检查步骤**：

1. 确认定时任务存在：
   ```bash
   ssh root@157.245.51.54 'crontab -l | grep bot_wecom'
   ```

2. 检查时区设置：
   ```bash
   ssh root@157.245.51.54 'timedatectl'
   # 应该显示: Time zone: Asia/Shanghai (CST, +0800)
   ```

3. 查看执行日志：
   ```bash
   ssh root@157.245.51.54 'tail -50 /var/log/ai-news.log'
   ```

4. 手动执行测试：
   ```bash
   ssh root@157.245.51.54 'cd /opt/apps/ai-news-bot/code && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py'
   ```

### 问题3: Git推送失败

**症状**：
```
! [rejected] main -> main (fetch first)
```

**解决方案**：
```bash
# 先拉取远程更新
git pull origin main

# 解决冲突后再推送
git push origin main
```

---

## ✅ 最佳实践

### 1. 发布前检查清单

- [ ] 代码已在本地测试通过
- [ ] 提交信息清晰、符合规范
- [ ] 确认要部署到生产环境
- [ ] 备份重要数据（自动完成）

### 2. 发布频率建议

- **小改动**：随时发布
- **新功能**：充分测试后发布
- **紧急修复**：立即发布
- **大版本**：选择低峰时段发布

### 3. 回滚策略

如果发布后发现问题：

```bash
# 1. SSH连接到服务器
ssh root@157.245.51.54

# 2. 查看备份列表
ls -lt /opt/backups/ai-news-bot/

# 3. 恢复到之前的版本
cd /opt/apps/ai-news-bot
rm -rf code
cp -r /opt/backups/ai-news-bot/backup_YYYYMMDD_HHMMSS/code .

# 4. 重启服务
cd code
source ../venv/bin/activate
python3 bot_wecom.py
```

### 4. 安全建议

- ✅ 不要将 `.env` 文件提交到Git
- ✅ 定期更新依赖包
- ✅ 保持服务器系统更新
- ✅ 定期检查日志文件

---

## 📊 发布记录模板

建议在每次重要发布后记录：

```markdown
## 发布记录 - YYYY-MM-DD

**版本**: v1.x.x
**发布人**: 你的名字
**发布时间**: 2025-11-27 10:00

### 更新内容
- feat: 添加教育新闻源
- fix: 修复新闻重复问题
- docs: 更新部署文档

### 测试情况
- [x] 本地测试通过
- [x] 服务器部署成功
- [x] 定时任务正常

### 备注
无特殊说明
```

---

## 🔗 相关文档

- [README.md](README.md) - 项目总览
- [.deployrc](.deployrc) - 部署配置
- [server_deploy.sh](server_deploy.sh) - 服务器端部署脚本

---

## 📞 获取帮助

遇到问题时：

1. 查看本文档的故障排查章节
2. 检查服务器日志
3. 查看GitHub Issues
4. 联系项目维护者

---

**最后更新**: 2025-11-27
**维护者**: AI News Bot Team
