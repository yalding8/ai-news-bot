# ⏰ 定时推送配置指南（仅企业微信，scheduler 脚本暂未维护）

⚠️ 当前版本仅保留企业微信推送，建议直接用 crontab 调用 `bot_wecom.py`。历史的 `scheduler.py`/Telegram 说明已下线，本页仅作参考。

## 📋 目录

- [快速开始](#快速开始)
- [配置文件说明](#配置文件说明)
- [macOS/Linux 配置](#macoslinux-配置)
- [Windows 配置](#windows-配置)
- [进阶使用](#进阶使用)

---

## 🚀 快速开始

### 1. 查看当前配置的任务

```bash
python scheduler.py --list
```

你会看到类似这样的输出：

```
======================================================================
📋 定时推送任务列表
======================================================================

1. 早间AI新闻 [✅ 启用]
   ⏰ 时间: 09:00 (每天)
   📰 主题: ai
   📝 说明: 每天早上9点推送AI领域新闻

2. 午间财经快讯 [❌ 禁用]
   ⏰ 时间: 12:00 (每天)
   📰 主题: finance, startup
   📝 说明: 中午12点推送财经和创投新闻
```

### 2. 立即测试运行

在配置定时任务之前，先测试一下：

```bash
# 运行所有启用的任务
python scheduler.py --now

# 运行指定的任务
python scheduler.py --now --name "早间AI新闻"
```

### 3. 配置定时任务

根据你的操作系统选择：
- macOS/Linux → 使用 [crontab](#macoslinux-配置)
- Windows → 使用 [任务计划程序](#windows-配置)

---

## ⚙️ 配置文件说明

编辑 `schedule_config.json` 来自定义你的推送任务：

```json
{
  "schedules": [
    {
      "name": "早间AI新闻",           // 任务名称
      "enabled": true,                // 是否启用
      "time": "09:00",                // 推送时间 (24小时制)
      "topics": ["ai"],               // 推送的新闻主题
      "description": "每天早上9点推送AI领域新闻"
    },
    {
      "name": "每周学生公寓周报",
      "enabled": true,
      "time": "09:00",
      "weekday": 0,                   // 0=周一, 1=周二, ..., 6=周日
      "topics": ["pbsa", "uhomes"],
      "description": "每周一早上推送学生公寓行业周报"
    }
  ]
}
```

### 可用的新闻主题

| 主题代码 | 名称 | 说明 |
|---------|------|------|
| `ai` | AI科技 | AI领域最新动态 |
| `finance` | 财经新闻 | 金融市场和经济动态 |
| `startup` | 创业投资 | 创业公司和投资动态 |
| `education` | 国际教育 | 国际教育行业动态 |
| `pbsa` | 学生公寓 | PBSA学生公寓行业动态 |
| `uhomes` | 异乡好居 | 异乡好居企业动态 |

### 示例配置

#### 每天推送AI和财经新闻

```json
{
  "name": "早间科技财经",
  "enabled": true,
  "time": "08:30",
  "topics": ["ai", "finance"],
  "description": "每天早上8:30推送科技和财经新闻"
}
```

#### 工作日推送，周末不推送

需要创建两个 cron 任务，在配置 crontab 时指定工作日（见下文）

#### 每周一推送周报

```json
{
  "name": "每周周报",
  "enabled": true,
  "time": "09:00",
  "weekday": 0,
  "topics": ["ai", "finance", "startup", "education"],
  "description": "每周一早上推送各领域周报"
}
```

---

## 🍎 macOS/Linux 配置

### 方法1: 使用 crontab（推荐）

#### 1. 获取项目完整路径

```bash
cd /path/to/ai-news-bot
pwd
```

假设输出是：`/Users/ningding/ai-news-bot`

#### 2. 编辑 crontab

```bash
crontab -e
```

#### 3. 添加定时任务

在打开的编辑器中添加以下内容：

```bash
# 每分钟检查一次是否有任务需要执行
* * * * * cd /Users/ningding/ai-news-bot && /usr/bin/python3 scheduler.py --check >> scheduler.log 2>&1

# 或者：直接指定具体时间（推荐，更省资源）
# 每天早上9点推送
0 9 * * * cd /Users/ningding/ai-news-bot && /usr/bin/python3 scheduler.py --now --name "早间AI新闻" >> scheduler.log 2>&1

# 每天中午12点推送
0 12 * * * cd /Users/ningding/ai-news-bot && /usr/bin/python3 scheduler.py --now --name "午间财经快讯" >> scheduler.log 2>&1

# 每周一早上9点推送
0 9 * * 1 cd /Users/ningding/ai-news-bot && /usr/bin/python3 scheduler.py --now --name "每周学生公寓周报" >> scheduler.log 2>&1
```

#### 4. 保存并退出

- vim: 按 `Esc`，输入 `:wq`，回车
- nano: 按 `Ctrl+X`，按 `Y`，回车

#### 5. 验证 crontab

```bash
# 查看当前的 crontab
crontab -l

# 查看日志
tail -f /Users/ningding/ai-news-bot/scheduler.log
```

### Crontab 时间格式说明

```
* * * * * 命令
│ │ │ │ │
│ │ │ │ └─── 星期几 (0-7, 0和7都是周日)
│ │ │ └───── 月份 (1-12)
│ │ └─────── 日期 (1-31)
│ └───────── 小时 (0-23)
└─────────── 分钟 (0-59)
```

#### 常用示例

```bash
# 每天早上9点
0 9 * * *

# 每天早上9点和晚上6点
0 9,18 * * *

# 工作日早上9点 (周一到周五)
0 9 * * 1-5

# 每小时的第30分钟
30 * * * *

# 每天每隔2小时
0 */2 * * *
```

### 方法2: 使用 launchd (macOS 专用，更强大)

#### 1. 创建 plist 文件

创建文件 `~/Library/LaunchAgents/com.user.ainewsbot.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.ainewsbot</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/ningding/ai-news-bot/scheduler.py</string>
        <string>--check</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/ningding/ai-news-bot/scheduler.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/ningding/ai-news-bot/scheduler_error.log</string>
</dict>
</plist>
```

#### 2. 加载任务

```bash
launchctl load ~/Library/LaunchAgents/com.user.ainewsbot.plist
```

#### 3. 管理任务

```bash
# 停止任务
launchctl unload ~/Library/LaunchAgents/com.user.ainewsbot.plist

# 重新加载
launchctl unload ~/Library/LaunchAgents/com.user.ainewsbot.plist
launchctl load ~/Library/LaunchAgents/com.user.ainewsbot.plist

# 查看任务状态
launchctl list | grep ainewsbot
```

---

## 🪟 Windows 配置

### 方法1: 使用辅助脚本（推荐，最简单）

我们提供了一个自动配置脚本。

#### 1. 运行配置脚本

```powershell
# 以管理员身份打开 PowerShell
cd C:\path\to\ai-news-bot
python setup_windows_task.py
```

脚本会自动创建任务计划程序任务。

### 方法2: 手动配置任务计划程序

#### 1. 打开任务计划程序

- 按 `Win + R`
- 输入 `taskschd.msc`
- 回车

#### 2. 创建基本任务

1. 右侧点击 `创建基本任务`
2. 名称：`AI新闻推送 - 早间`
3. 描述：`每天早上9点推送AI新闻`
4. 点击 `下一步`

#### 3. 配置触发器

1. 选择 `每天`
2. 设置开始时间：`09:00:00`
3. 点击 `下一步`

#### 4. 配置操作

1. 选择 `启动程序`
2. 程序或脚本：`C:\Python39\python.exe` (你的Python路径)
3. 添加参数：`scheduler.py --now --name "早间AI新闻"`
4. 起始于：`C:\path\to\ai-news-bot`
5. 点击 `下一步`

#### 5. 完成

点击 `完成`

#### 6. 测试任务

在任务计划程序中，找到刚创建的任务，右键 → `运行`，检查是否正常工作。

### 方法3: 使用 PowerShell 脚本

创建文件 `schedule_task.ps1`：

```powershell
# 配置
$TaskName = "AI新闻推送-早间"
$PythonPath = "C:\Python39\python.exe"
$ScriptPath = "C:\path\to\ai-news-bot\scheduler.py"
$WorkingDir = "C:\path\to\ai-news-bot"
$Time = "09:00"

# 创建任务
$Action = New-ScheduledTaskAction -Execute $PythonPath `
    -Argument "scheduler.py --now --name '早间AI新闻'" `
    -WorkingDirectory $WorkingDir

$Trigger = New-ScheduledTaskTrigger -Daily -At $Time

Register-ScheduledTask -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Description "每天早上推送AI新闻"

Write-Host "✅ 任务创建成功！"
```

运行：

```powershell
# 以管理员身份运行
PowerShell -ExecutionPolicy Bypass -File schedule_task.ps1
```

---

## 🔥 进阶使用

### 1. 查看推送日志

```bash
# 实时查看日志
tail -f scheduler.log

# 查看最近20条
tail -n 20 scheduler.log

# 搜索错误
grep "ERROR" scheduler.log
```

### 2. 推送到多个企业微信群

编辑 `.env` 文件，添加多个 Webhook URL：

```env
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
WECOM_WEBHOOK_URL_2=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=yyy
WECOM_WEBHOOK_URL_3=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=zzz
```

修改 `bot_wecom.py` 的 `send_wecom_message()` 函数来支持多URL。

### 3. 失败重试机制

配置文件中已经包含重试设置：

```json
{
  "settings": {
    "retry_on_failure": true,
    "max_retries": 3,
    "retry_interval_seconds": 300
  }
}
```

### 4. 不同时间推送不同主题

在 `schedule_config.json` 中添加多个任务：

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
      "topics": ["finance"]
    },
    {
      "name": "晚间综合",
      "enabled": true,
      "time": "18:00",
      "topics": ["ai", "finance", "startup"]
    }
  ]
}
```

### 5. 动态调整推送时间

不需要重启服务，只需：

1. 编辑 `schedule_config.json`
2. 修改 `time` 字段
3. 保存即可

cron 会在下次执行时读取新配置。

### 6. 临时禁用某个任务

将任务的 `enabled` 字段设为 `false`：

```json
{
  "name": "午间财经快讯",
  "enabled": false,
  "time": "12:00",
  "topics": ["finance"]
}
```

### 7. 监控和告警

创建一个简单的监控脚本 `monitor.sh`：

```bash
#!/bin/bash
LOG_FILE="/path/to/ai-news-bot/scheduler.log"

# 检查最近10分钟的日志
if grep -q "ERROR\|失败" <(tail -n 100 "$LOG_FILE"); then
    echo "⚠️ 检测到推送失败！"
    # 可以在这里发送告警邮件或通知
fi
```

---

## 🐛 故障排查

### 问题1: crontab 任务没有执行

**检查步骤：**

1. 确认 crontab 已保存
   ```bash
   crontab -l
   ```

2. 检查路径是否正确
   ```bash
   which python3
   # 输出: /usr/bin/python3
   ```

3. 查看系统日志
   ```bash
   # macOS
   tail -f /var/log/system.log | grep cron

   # Linux
   tail -f /var/log/syslog | grep CRON
   ```

4. 检查权限
   ```bash
   ls -la scheduler.py
   chmod +x scheduler.py
   ```

### 问题2: 任务执行了但没有推送

**检查步骤：**

1. 查看 scheduler.log
   ```bash
   tail -n 50 scheduler.log
   ```

2. 手动运行测试
   ```bash
   python scheduler.py --now --name "早间AI新闻"
   ```

3. 检查环境变量
   ```bash
   # .env 文件是否存在
   cat .env
   ```

4. 检查网络连接
   ```bash
   ping qyapi.weixin.qq.com
   ```

### 问题3: Windows 任务计划程序任务失败

**检查步骤：**

1. 查看任务历史记录
   - 任务计划程序 → 选择任务 → 历史记录标签

2. 手动运行测试
   ```powershell
   cd C:\path\to\ai-news-bot
   python scheduler.py --now
   ```

3. 检查工作目录设置
   - 确保"起始于"字段正确设置

---

## 💡 实践建议

### 推荐的推送时间

- **早间新闻**: 8:00 - 9:00（上班前）
- **午间快讯**: 12:00 - 13:00（午休时）
- **晚间汇总**: 18:00 - 19:00（下班后）
- **周报**: 每周一早上 9:00

### 主题搭配建议

- **科技人士**: AI + 创业投资
- **金融从业者**: 财经 + 创业投资
- **教育行业**: 国际教育 + 学生公寓
- **综合资讯**: AI + 财经 + 创业投资

### 性能优化

- 避免同时推送过多主题（建议每次不超过3个）
- 推送间隔至少保持30秒
- 利用 DeepSeek 的低成本优势，多推送没问题

---

## 📚 相关文档

- [企业微信群机器人接入指南](WECOM_GUIDE.md)
- [README](README.md)

---

⭐ 如有问题，欢迎提Issue！
