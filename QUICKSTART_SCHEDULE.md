# ⚡ 定时推送快速开始指南

5分钟配置自动推送！

## 🎯 目标

让机器人每天自动在固定时间推送新闻到企业微信群。

---

## 📝 第一步：确认配置

### 1. 确保 `.env` 文件已配置

```bash
cat .env
```

应该包含：
```env
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
```

如果没有，参考 [企业微信接入指南](WECOM_GUIDE.md)

### 2. 查看当前配置的任务

```bash
python3 scheduler.py --list
```

---

## 🧪 第二步：测试运行

在配置定时之前，先测试一下：

```bash
# 立即推送一次AI新闻（测试用）
python3 scheduler.py --now --name "早间AI新闻"
```

如果成功，你会在企业微信群里看到新闻推送！

---

## ⏰ 第三步：配置定时任务

### macOS/Linux用户

#### 方式1: 每分钟检查（简单推荐）

```bash
# 编辑 crontab
crontab -e

# 添加这一行（把路径改成你的）
* * * * * cd /Users/ningding/ai-news-bot && /usr/bin/python3 scheduler.py --check >> scheduler.log 2>&1

# 保存退出（vim: Esc + :wq，nano: Ctrl+X + Y）
```

#### 方式2: 指定时间（高效推荐）

```bash
# 编辑 crontab
crontab -e

# 每天早上9点推送AI新闻
0 9 * * * cd /Users/ningding/ai-news-bot && /usr/bin/python3 scheduler.py --now --name "早间AI新闻" >> scheduler.log 2>&1
```

#### 验证配置

```bash
# 查看 crontab
crontab -l

# 等待执行，查看日志
tail -f scheduler.log
```

### Windows用户

#### 方式1: 自动配置（最简单）

```powershell
# 以管理员身份打开 PowerShell，运行
python setup_windows_task.py
```

按提示操作即可。

#### 方式2: 手动配置

1. 按 `Win + R`，输入 `taskschd.msc`
2. 右侧点击 `创建基本任务`
3. 名称：`AI新闻推送-早间`
4. 触发器：每天，9:00
5. 操作：启动程序
   - 程序：`C:\Python39\python.exe`
   - 参数：`scheduler.py --now --name "早间AI新闻"`
   - 起始于：`C:\path\to\ai-news-bot`
6. 完成

---

## ✅ 第四步：验证

### 查看日志

```bash
# 实时查看日志
tail -f scheduler.log

# 查看最近的推送记录
tail -n 20 scheduler.log
```

### 测试 cron 任务

不想等到设定时间？手动触发测试：

```bash
# macOS/Linux
cd /Users/ningding/ai-news-bot && /usr/bin/python3 scheduler.py --check

# Windows：在任务计划程序中，右键任务 → 运行
```

---

## 🎨 第五步：自定义配置

编辑 `schedule_config.json`：

```json
{
  "schedules": [
    {
      "name": "早间AI新闻",
      "enabled": true,        // 改成 false 可以禁用
      "time": "09:00",        // 修改推送时间
      "topics": ["ai"],       // 添加更多主题，如 ["ai", "finance"]
      "description": "每天早上9点推送AI领域新闻"
    }
  ]
}
```

**不需要重启任何服务**，下次执行时会自动读取新配置！

---

## 🔧 常用场景

### 场景1: 早中晚三次推送

```json
{
  "schedules": [
    {
      "name": "早间AI",
      "enabled": true,
      "time": "08:00",
      "topics": ["ai"]
    },
    {
      "name": "午间财经",
      "enabled": true,
      "time": "12:00",
      "topics": ["finance", "startup"]
    },
    {
      "name": "晚间综合",
      "enabled": true,
      "time": "18:00",
      "topics": ["ai", "finance", "education"]
    }
  ]
}
```

对应的 crontab：
```bash
0 8 * * * cd /path/to/ai-news-bot && python3 scheduler.py --check >> scheduler.log 2>&1
0 12 * * * cd /path/to/ai-news-bot && python3 scheduler.py --check >> scheduler.log 2>&1
0 18 * * * cd /path/to/ai-news-bot && python3 scheduler.py --check >> scheduler.log 2>&1
```

或者简单点，每小时检查一次：
```bash
0 * * * * cd /path/to/ai-news-bot && python3 scheduler.py --check >> scheduler.log 2>&1
```

### 场景2: 只在工作日推送

crontab 配置：
```bash
# 工作日（周一到周五）早上9点
0 9 * * 1-5 cd /path/to/ai-news-bot && python3 scheduler.py --now --name "早间AI新闻" >> scheduler.log 2>&1
```

### 场景3: 每周一推送周报

```json
{
  "name": "每周周报",
  "enabled": true,
  "time": "09:00",
  "weekday": 0,              // 0=周一
  "topics": ["ai", "finance", "startup", "education"]
}
```

crontab：
```bash
0 9 * * 1 cd /path/to/ai-news-bot && python3 scheduler.py --check >> scheduler.log 2>&1
```

---

## 🐛 故障排查

### 问题：cron 没有执行

**检查步骤：**

1. 确认 crontab 已保存
   ```bash
   crontab -l
   ```

2. 检查 Python 路径
   ```bash
   which python3
   # 输出：/usr/bin/python3
   # 在 crontab 中使用这个完整路径
   ```

3. 手动测试命令
   ```bash
   cd /Users/ningding/ai-news-bot && /usr/bin/python3 scheduler.py --check
   ```

4. 查看系统日志
   ```bash
   # macOS
   log show --predicate 'process == "cron"' --last 1h

   # Linux
   grep CRON /var/log/syslog
   ```

### 问题：执行了但没推送

1. 查看 scheduler.log
   ```bash
   tail -n 50 scheduler.log
   ```

2. 检查 .env 文件
   ```bash
   cat .env
   ```

3. 手动测试推送
   ```bash
   python3 scheduler.py --now --name "早间AI新闻"
   ```

---

## 💡 小贴士

1. **日志管理**：定期清理 `scheduler.log`，避免文件过大
   ```bash
   # 只保留最近100行
   tail -n 100 scheduler.log > scheduler.log.tmp && mv scheduler.log.tmp scheduler.log
   ```

2. **测试新配置**：修改配置后，先用 `--now` 测试，确认无误再等定时执行

3. **多群推送**：在不同群添加机器人，获取多个 Webhook URL，配置环境变量

4. **成本控制**：DeepSeek 很便宜（$0.14/1M tokens），日常使用成本几乎可以忽略

5. **备份配置**：定期备份 `schedule_config.json` 和 `.env` 文件

---

## 📚 更多资料

- **完整文档**: [SCHEDULE_GUIDE.md](SCHEDULE_GUIDE.md) - 详细的配置指南
- **企业微信接入**: [WECOM_GUIDE.md](WECOM_GUIDE.md) - 企业微信机器人配置
- **项目说明**: [README.md](README.md) - 项目总览

---

## 🎉 完成！

现在你的AI新闻机器人已经可以自动推送了！

有问题随时查看日志：
```bash
tail -f scheduler.log
```

⭐ 如果觉得有用，给个Star吧！
