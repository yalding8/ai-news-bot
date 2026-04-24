---
title: 运维部署通知标准化工具包（ops-deploy-kit）PRD
date: 2026-04-24
author: neilding
version: 0.3
status: Draft v0.3（针对 Gate-1 v0.2 复评 7.9/10 的 8 项残留做补强，目标 ≥ 8.5）
reviewers: TBD
prior_reviews:
  - docs/AUDIT_2026-04-24_PRD_OPS_KIT_GATE1.md    (v0.1: 6.3/10 不通过)
  - docs/AUDIT_2026-04-24_PRD_OPS_KIT_GATE1_V2.md (v0.2: 7.9/10 条件通过)
---

> **v0.3 改动摘要**（v0.2 → v0.3）
>
> 针对 v0.2 复评残留的 🟡 中项 + 🟢 低项做收尾补强：
> - 新增 §5.9 upgrade-kit.sh 设计（A6）、§5.10 凭证生命周期（S4）、§14 附录 C 离线接入（A5）、§15 附录 D 已知限制（T4）
> - §5.6 末尾加版本兼容条款（T2）
> - §7 Phase 2 按项目细化工作量（O5）
> - §12.5 L3 加跨发行版强制要求（T5）、§12.4 加 I6 bootstrap 回滚测试（T3）、§12.4 加 I7 log 脱敏断言（S5）
>
> **v0.2 改动摘要**（v0.1 → v0.2）
>
> 针对 `AUDIT_2026-04-24_PRD_OPS_KIT_GATE1.md` 指出的 3 🔴 必须项 + 4 🟡 中项：
> - 新增 §1.3 需求调研（C1）、§5.6 版本化策略（A3）、§5.7 供应链保护（S1）、§5.8 自监控心跳（S2）、§12 测试方案（T1）
> - 修正 §2.1 / §6 "3-10 分钟" 矛盾（A1）、§5.1 / §2.2 disk_alert 前后矛盾（A2）、§7 补入脚本拆分工作量（A4）、§8 R5 fallback（O1）

# PRD：运维部署通知标准化工具包（ops-deploy-kit）

## 可信度声明

本 PRD 由 AI 辅助撰写（Claude Opus 4.7）。文中所有"多专家评估""方案对比"均是同一模型的多个推理分支，**不等于真人专家独立交叉审查**。评分、优先级、工作量估算都是 AI 初判，最终决策由项目负责人拍板。

- 方案选型、兼容性判断：`[AI 初判]`
- 代码片段、服务器路径、已有项目现状：`[已核实]`（本会话内通过 ssh 日志 / git log / find 等命令核实）
- 工作量估算、实施周期：`[AI 估算]`，未经 POC

---

## 1. 背景与动机

### 1.1 事件触发

2026-04-24 给 ai-news-bot 接入服务器自动部署 + 运维群通知时，发现：

| 问题 | 暴露点 |
|---|---|
| 每个项目**各自实现**部署脚本 + 通知逻辑 | uhomes-workorder 的 `deploy-notify.sh` 和 ai-news-bot 的 `auto_pull_deploy.sh` 有 60% 代码重复 |
| 配置文件路径**各项目不一致** | uhomes-workorder 读 `/opt/dootask/.deploy.env`（该文件在 dingning 上**不存在**，导致通知早就失效但无人发现）；ai-news-bot 今天新建了 `/home/ops/ai-news-bot/.deploy.env` |
| **wecom markdown 限制踩坑要反复学习** | 本次会话中两次方向错误：① 误以为裸 URL 会 auto-link（不会）；② 误以为 `[text](url)` 会显色（可点但不显色）。每个新项目接入时都可能重学 |
| 格式迭代需要 **N+2 次 commit** 才能看到效果 | 因 `bash 进程读磁盘脚本`的时差规律，每次改格式后至少推 2 个 trigger commit 才能验证 |
| **静默失败**难以诊断 | uhomes-workorder 的部署通知从 `/opt/dootask/.deploy.env` 缺失那天起就没再发过，但脚本 `wecom_notify.sh` 始终 `exit 0`，运维群没人察觉 |

### 1.2 预期未来项目

根据对话透露，接下来还会有多个项目需要这套能力：
- 已在跑：uhomes-workorder、ai-news-bot、aifx、dootask、dianping、xhs-monitor、uhomespay-\* 等（共 10+ 个 Projects 目录）
- 未来会加：留学生就业网站、上线审核工具等

按今天手工接入 ai-news-bot 的工作量估算：**每个新项目接入成本约 2-3 小时**（踩坑 + 配置 + 验证）。如果 10 个项目都这样，累计 20-30 小时，且每次都有不同的出错方式。

### 1.3 目标

把这套**样板化**，新项目 10 分钟内接入，统一踩坑一次以后不再重踩。

### 1.4 需求调研：预期受益项目（v0.2 新增，补强 C1）

用户已确认"未来会有很多项目需要"（2026-04-24 session）。基于 `~/Projects/` 目录当前
存在的项目做初筛（待项目负责人 review 确认）：

| 项目 | 类型 | 当前通知现状 | Kit 接入意愿 |
|---|---|---|---|
| ai-news-bot | Python · 爬虫+推送 | 已接入（本 session） | 🔴 高（dogfood 样板） |
| uhomes-workorder | PHP · Laravel 工单 | 已有但因 `.deploy.env` 缺失失效 | 🔴 高（一次性修复通知 + 迁移） |
| aifx | Python · 汇率数据 | 已有 `auto_pull_deploy.sh` 雏形 | 🟡 中（现有脚本可改造） |
| dianping | Python · 数据采集 | 无 | 🟡 中 |
| uhomes-inventory-ai | Python · ML 库存 | 待评估 | 🟡 中 |
| xhs-monitor | Python · 监控 | 无 | 🟡 中 |
| up-dailyreport / 其他 | 多样 | 多数无 | 🟢 按需 |

**Phase 1 直接受益估算**：3 个（ai-news-bot + uhomes-workorder + aifx）
**Phase 2 潜在接入**：4-5 个
**总计目标**：6 个月内接入 6+ 个项目

**ROI 重算**：若有 6 个项目受益 × 3h 节省（PRD v0.1 的 2-3h 估算偏保守，加上踩坑） = **18 h 净节省**；Kit 首版实施 5d + 维护 3-5h/月 × 6 个月 ≈ 25-35h。**第 6-12 个月之间回本**（而非 v0.1 乐观预期的 3 个月）。

---

## 2. 目标 / 非目标

### 2.1 目标（本 PRD 范围）

✅ **G1**：提供单一"运维部署通知"脚本包，让任意 Python/Node/其他项目**在 10 分钟内接入完毕**（v0.1 的 "3 分钟" 不含 README 阅读时间，不切实际，v0.2 统一口径为 10 分钟）
✅ **G2**：统一 wecom 群机器人通知格式（成功/失败/告警），跨项目视觉一致
✅ **G3**：统一敏感凭证管理约定（`.deploy.env` 位置 + 权限 + 加载顺序）
✅ **G4**：把今天踩到的所有 wecom markdown 限制 / bash 时差规律 / 失败限频规则**一次性文档化**
✅ **G5**：提供一键 bootstrap 脚本，新项目接入只需 3 条命令

### 2.2 非目标（明确排除）

❌ **不做中心化通知服务**（需要堡垒机管理员权限，用户当前权限边界做不到——见 2026-04-24 讨论记录）
❌ **不重写 wecom API 接入**（就用现成的 webhook 群机器人）
❌ **不做多通道路由**（短信、邮件、企微应用 API 等重服务——未来需求再说）
❌ **不做通知的内容聚合 / 去重**（每次 deploy 一条消息，简单可靠）
❌ **不覆盖非部署场景**的通知（业务告警、用户通知等由各项目自行实现）

**未来扩展点（不在本 PRD 范围，但仓库预留结构位）**：
- `disk_alert.sh` —— 磁盘空间告警（Phase 3 可能引入）
- `health_check.sh` —— HTTP 健康检查（Phase 3 可能引入）
- 这些**不是本 PRD 的交付物**，仅在 §5.1 仓库结构说明时提及

### 2.3 可逆性评分

**3 分 — 可逆但有摩擦**

此方案本质是"共享脚本库 + 项目各自引用"。若将来想换方向（比如拿到堡垒机权限后升级为中心服务），各项目的 `.deploy.env` 和 cron 结构**都能继续用**，只需改 `wecom_notify.sh` 的内部实现指向中心服务。迁移成本可控。

---

## 3. 用户画像

| 角色 | 使用场景 | 对 Kit 的期望 |
|---|---|---|
| 🧑‍💻 **项目 owner（你）** | 新建一个项目，想接入部署通知 | `bootstrap.sh` 一键搞定，不用读多页文档 |
| 🛠️ **运维工程师（你）** | 在群里看到部署失败通知，要快速定位 | 通知含 host/时间/退出码/日志路径；能点进 GitHub compare |
| 🤖 **AI 助手（未来 session 的我 / Claude Code）** | 给一个新项目接入时 | 有明确的 bootstrap 流程 + 踩坑清单，不重走弯路 |

---

## 4. 方案选型

### 4.1 候选方案

#### 方案 A：共享 Git 仓库（submodule / curl bootstrap）⭐ 推荐

- 开一个 `github.com/neilding/ops-deploy-kit` 仓库
- 里面放 `wecom_notify.sh` / `auto_pull_deploy.sh.tpl` / `bootstrap.sh`
- 各项目**克隆**或 **curl 下载**这些脚本到自己的 `scripts/` 目录
- 配置（webhook）各项目自己的 `.deploy.env`

**成本**：1-2 天搞定首版 [AI 估算]
**优点**：零新基础设施；和用户当前权限完全匹配；版本可追踪（git tag）
**缺点**：webhook URL 每台服务器各自存一份；脚本更新需要各项目手工 `git pull / curl`

#### 方案 B：堡垒机中心服务（HTTP 监听）

- 堡垒机跑 HTTP 监听服务，各项目 POST 事件 → 转发 webhook
- **前提**：堡垒机访问权（用户已确认**没有**）

**成本**：3-5 天 + 持续维护
**优点**：webhook URL 只在一处；全局审计日志
**缺点**：**不符合用户当前权限**，此方案现阶段不可行。未来拿到权限再考虑。

#### 方案 C：企微自建应用 API + 消息路由

- 不用群机器人，走企微自建应用 + 按值班表路由
- **成本**：1-2 周 + 企微 agent 创建权 [AI 估算]
- **只有当 5+ 人运维组有值班制度时才值得**

### 4.2 选定方案

**方案 A**。理由：
1. 匹配当前权限边界（用户非管理员）
2. 本次 ai-news-bot 接入的两个脚本（`wecom_notify.sh` + `auto_pull_deploy.sh`）已经是现成素材，抽取成本最低
3. 未来升级方案 B 时，只需改 `wecom_notify.sh` 内部实现，接入方式保持不变

---

## 5. 详细设计（方案 A）

### 5.1 仓库结构

```
github.com/neilding/ops-deploy-kit/
├── README.md                  接入指南（含所有已知 wecom 限制）
├── bootstrap.sh               新项目一键接入入口
├── scripts/
│   ├── wecom_notify.sh        通用 curl 包装器
│   ├── auto_pull_deploy.sh    标准 git-pull 自动部署模板
│   └── (Phase 3 扩展位：disk_alert.sh / health_check.sh 等)
├── templates/
│   ├── .deploy.env.example    配置模板
│   └── crontab.example        cron 配置模板
├── docs/
│   ├── WECOM_MARKDOWN_QUIRKS.md  踩坑大全
│   ├── BASH_TIME_SHIFT.md        N+2 commit 时差规律
│   └── TROUBLESHOOTING.md        故障排查手册
├── CHANGELOG.md               版本变更日志
└── VERSION                    当前版本号（语义化：vMAJOR.MINOR.PATCH）
```

### 5.2 脚本接口契约

#### `wecom_notify.sh`

```bash
./wecom_notify.sh "<标题>" "<markdown 正文>"
```

**读环境变量**：
- `WECOM_BOT_WEBHOOK_URL`（必需；未配置静默 exit 0）

**退出码**：始终 0（不阻塞调用方）

**不变契约**：
- 标题前缀建议用 emoji（✅ / ⚠️ / 🚨）做视觉 triage
- 正文用 markdown 格式
- 链接用 `[文字 + emoji/箭头提示](url)` 格式（弥补 wecom 不显色的限制）

#### `auto_pull_deploy.sh`

```bash
# 通过环境变量注入项目信息
APP_DIR=/home/ops/<project-name>
PROJECT_NAME=<project-name>            # 用于通知标题
POST_PULL_HOOK=./scripts/post_pull.sh  # 可选：项目自定义的"拉完代码后要做什么"
```

**默认行为**：
1. fetch origin → 无新 commit 秒退
2. flock 并发锁
3. 备份 `.env` + `.deploy.env`（如存在）
4. `git reset --hard origin/main`
5. 恢复备份
6. 调用 `POST_PULL_HOOK`（如设置）—— 项目自己决定装依赖 / 跑 migration / 重启服务
7. 推送通知

**POST_PULL_HOOK 合约**：
- 非 0 退出 → 视为部署失败，触发失败通知
- 0 退出 → 触发成功通知

#### `bootstrap.sh`

```bash
curl -sL https://raw.githubusercontent.com/neilding/ops-deploy-kit/main/bootstrap.sh \
  | bash -s <project-name> <app-dir>
```

**动作**：
1. 检查 `<app-dir>` 是 git 仓库
2. 拉取最新 Kit 脚本到 `<app-dir>/scripts/` 下（可选：用 submodule 或直接 curl + 写 SHA 校验）
3. 生成 `<app-dir>/.deploy.env.template` 提示用户填 webhook URL
4. 打印 cron 配置建议

### 5.3 配置约定

| 路径 | 权限 | 作用 |
|---|---|---|
| `<app-dir>/.deploy.env` | `0600 ops:ops` | webhook URL + 项目级环境变量 |
| `<app-dir>/scripts/auto_pull_deploy.sh` | `0755` | 标准部署脚本（从 Kit 下载） |
| `<app-dir>/scripts/wecom_notify.sh` | `0755` | 通用通知包装器（从 Kit 下载） |
| `<app-dir>/scripts/post_pull.sh` | `0755` | **项目自己写**的部署后钩子 |
| `<app-dir>/deploy.log` | `0644 ops:ops` | 部署日志 |
| `<app-dir>/.deploy-fail-count` | `0644 ops:ops` | 失败限频计数器（运行时产生） |

### 5.4 通知格式约定（跨项目统一）

**成功**：
```markdown
## ✅ <PROJECT_NAME> 部署成功

**时间**：2026-04-24 18:38:03
**主机**：dingning
**作者**：neilding
**版本**：`abc12345` → `def67890` · N 个提交
**Diff**：[🔗 点击查看 diff ↗](https://github.com/.../compare/...)

**变更**：
- commit 标题 1
- commit 标题 2
- ... 还有 N 条
```

**失败**：
```markdown
## ⚠️ <PROJECT_NAME> 部署失败

**时间**：2026-04-24 18:38:03
**主机**：dingning
**退出码**：1
**连续失败**：5 次 (已达告警阈值 5)  ← 仅 git 网络类失败到阈值时出现
**脚本**：`<app-dir>/scripts/auto_pull_deploy.sh`
**日志**：`tail -50 <app-dir>/deploy.log`
```

### 5.5 约束（Kit 设计哲学）

1. **Kit 脚本只管"部署 + 通知"**，业务逻辑（装依赖 / migration / 服务重启）交给 `post_pull.sh`
2. **Kit 不读项目代码**，只通过环境变量/钩子暴露扩展点
3. **Kit 无 Python/Node 依赖**，纯 bash + curl + git，跨语言项目通吃
4. **向后兼容承诺**：vMAJOR 版本号内 API 不破坏性变更

### 5.6 版本化策略（v0.2 新增，补强 A3）

**版本号**：语义化 `vMAJOR.MINOR.PATCH`（遵循 SemVer）

- **MAJOR** 破坏性：改 `post_pull.sh` 调用协议、改 `.deploy.env` 变量名、改脚本文件结构
- **MINOR** 新增：新增脚本（如 `heartbeat.sh`）、新增可选 env 变量
- **PATCH** 修复：bugfix、文档更新、内部重构（对接入方零感知）

**发布流程**：

1. 改动合并到 `main` 分支
2. 在 dogfood 项目（ai-news-bot）试跑 3 天
3. 打 annotated tag：`git tag -a v1.2.3 -m "特性摘要 + 破坏性变更清单"`
4. 更新 `CHANGELOG.md`（按 Keep a Changelog 格式）
5. `git push origin v1.2.3` + 在 GitHub 开 Release + 写 release notes
6. 运维群公告：@all 通报新版本 + 是否需要各项目主动升级

**各项目 pin 版本**：

- `bootstrap.sh` 创建 `<app-dir>/scripts/.kit-version` 记录当前 pin 的 **commit SHA**（不是 tag name，tag 可能被强制移动）
- `.kit-version` 内容格式：
  ```
  # Kit version metadata
  KIT_TAG=v1.2.3
  KIT_COMMIT=abc1234567890...  # 被 pin 的具体 commit SHA
  KIT_INSTALLED_AT=2026-04-24T18:00:00+08:00
  ```

**升级流程**：

- 查看当前版本：`cat scripts/.kit-version`
- 查看可用新版：`curl -s https://api.github.com/repos/neilding/ops-deploy-kit/releases/latest | grep tag_name`
- 升级：`./scripts/upgrade-kit.sh v1.2.3`（下载该 tag → 比对 SHA → 原子替换 → 更新 .kit-version）
- 回滚：`./scripts/upgrade-kit.sh v1.1.0`（逆向操作即可）

**版本共存**（v0.3 补强 T2）：
- **同一项目**：不支持并存多版本。任何时刻 `scripts/.kit-version` 只记录一个 commit SHA
- **不同项目**：完全独立，项目 A 用 v0.5、项目 B 用 v1.2、项目 C 用 v2.0 互不影响（Kit 无全局状态）
- **MAJOR 跨版本兼容性**：v1.x 项目升级到 v2.x 必须走"迁移指南"（Kit 每个 MAJOR 发版同步发迁移文档）；不支持 skip（不能 v1.x 直接跳 v3.x，必须 v1→v2→v3 逐版迁移）
- **测试保障**：CI 在 Kit 发新版时对 v(N-1) 和 v(N) 跑一遍完整 E2E，确保升级路径不破坏

### 5.7 供应链保护（v0.2 新增，补强 S1）

**PRD v0.1 的风险**：`curl -sL ... | bash` 是公认的供应链攻击面，无任何验证手段。

**v0.2 方案**：

**🔴 生产接入（推荐）—— clone + checksum + review**：

```bash
# 1. clone 指定 tag（不是 main，避免 TOCTOU）
git clone --depth=1 --branch=v1.0.0 https://github.com/neilding/ops-deploy-kit /tmp/kit-v1.0.0
cd /tmp/kit-v1.0.0

# 2. 验证 bootstrap.sh 的 SHA256（预期值在 Kit README 顶部公布）
sha256sum bootstrap.sh
# 期望: <Kit 官方公布的 v1.0.0 checksum>

# 3. （可选但推荐）手工 review 脚本内容
less bootstrap.sh
less scripts/wecom_notify.sh
less scripts/auto_pull_deploy.sh

# 4. 执行
./bootstrap.sh <project-name> /home/ops/<project-name>
```

**🟡 快速试用模式**（仅非生产 / 个人工具 / 试水）：

保留 `curl | bash` 作为单行脚本路径，但 README 必须醒目标注：

> ⚠️ 快速路径**仅适用于开发/试用/个人环境**；任何生产项目**必须**走上面的 clone+checksum 方式。

**Kit 自身防护**：

- Kit 仓库启用 GitHub Branch Protection + Required PR reviews
- `main` 分支所有 commit 必须 signed（`git commit -S`）
- Release tag 必须 annotated（`git tag -a`，不用 lightweight tag）
- 每次 Release 在 GitHub Release 页面公布所有脚本的 SHA256 清单

### 5.8 自监控：心跳机制（v0.2 新增，补强 S2）

**痛点实证**（本 session 发现）：uhomes-workorder 的 `deploy-notify.sh` 因
`/opt/dootask/.deploy.env` 缺失**持续静默失效**（不知何时失效的），
`wecom_notify.sh` 始终 `exit 0`，运维群完全无感知。

**Kit 必须解决这个问题**——通知链路断了要能在 25 小时内被发现。

**方案**：

1. **Kit 提供 `scripts/heartbeat.sh`**（v1.0 Phase 1 必交付项）

   功能：加载 `.deploy.env` → 调 `wecom_notify.sh` 推一条低调心跳：
   ```
   ## 💓 <PROJECT_NAME> 心跳
   **时间**：2026-04-25 10:00:00
   **主机**：dingning
   **最近部署**：`abc12345` · 2026-04-24 09:15:23（16 小时前）
   **Kit 版本**：v1.0.0
   ```

2. **bootstrap.sh 自动加 cron 行**：
   ```
   0 10 * * * /home/ops/<project>/scripts/heartbeat.sh
   ```

3. **运维群约定 SLA**（Kit README 第一段强制要求）：
   > "每个接入 Kit 的项目，每天早 10:00 必有一条💓 心跳消息。如果某项目 > 25 小时无心跳 → 立即排查 `.deploy.env` / webhook 是否失效。"

4. **频率控制**：1 天 1 条/项目。如果 10 个项目接入，运维群每天早 10:00 集中收到 10 条心跳，不吵。

**监控升级路径（Phase 3 再做）**：

- 在某台有权限的服务器起一个定时任务（每天 11:00 巡检）
- 扫描心跳群里最近 24h 出现的项目名，对照已接入项目清单
- 缺失则自动 `@ 运维值班` 升级告警

**代价**：每个项目多一条 cron 行；群里每天多 N 条消息。相比"通知链路静默失效未知时长"的代价，完全可接受。

### 5.9 `upgrade-kit.sh` 详细设计（v0.3 新增，补强 A6）

Kit 升级的具体协议 —— 由 Phase 1 P1.9 交付。

#### 5.9.1 目录结构

```
<app-dir>/scripts/
├── .kit-version              当前 pin 版本元数据（见 §5.6）
├── .kit-backup/              每次升级前自动备份旧版本
│   └── <timestamp>/          例：2026-04-24_180301/
│       ├── wecom_notify.sh
│       ├── auto_pull_deploy.sh
│       ├── heartbeat.sh
│       └── .kit-version
└── upgrade-kit.sh            升级入口脚本（v0.3 新增）
```

#### 5.9.2 命令接口

```bash
./scripts/upgrade-kit.sh <target-version>    # 升级到指定版本（tag 或 commit SHA）
./scripts/upgrade-kit.sh --dry-run v1.2.3    # 预览不实际改动
./scripts/upgrade-kit.sh --rollback          # 回滚到最近一次升级前的状态
./scripts/upgrade-kit.sh --list              # 列出本地已备份的所有版本
./scripts/upgrade-kit.sh --current           # 显示当前版本
```

#### 5.9.3 升级执行流程（原子性保证）

1. **预检**：`$target-version` 存在于远端？
2. **下载到 tempdir**：`git clone --depth=1 --branch=$target $KIT_REMOTE /tmp/kit-$target`
3. **校验 checksum**：读取 target 版本 README 里的 SHA256，和 tempdir 里的文件比对。失败立即 abort，清理 tempdir
4. **快照现有版本**：`cp -r scripts/ scripts/.kit-backup/$(date +%Y-%m-%d_%H%M%S)/`
5. **原子替换**：`mv` 每个脚本（`mv` 在同 FS 是原子操作）
   - 严格列表，只替换 Kit 拥有的文件（`wecom_notify.sh`, `auto_pull_deploy.sh`, `heartbeat.sh`, `upgrade-kit.sh`）
   - **不碰** `post_pull.sh`、`.deploy.env`（项目自己的）
6. **更新 .kit-version** → 新 commit SHA + tag name + timestamp
7. **冒烟验证**：`bash -n` 新脚本（语法正确）+ `./wecom_notify.sh "🔧 Kit 已升级到 $target" "..."` 推一条验证消息
8. **成功 ≈ 清理 tempdir**；**失败 ≈ 自动 `--rollback`**

#### 5.9.4 `--rollback` 逻辑

- 找 `.kit-backup/` 下最新目录
- 把其中文件原子 `mv` 回 `scripts/`
- 恢复 `.kit-version` 到备份版本
- 推一条通知：`↩️ Kit 已回滚到 vX.Y.Z`

**失败场景**：如果 tempdir 下载一半断网，脚本 trap EXIT 清理 tempdir 保证幂等；如果 mv 操作中断（极低概率），备份目录还在，人工 rollback 仍可恢复。

#### 5.9.5 安全性

- `upgrade-kit.sh` 本身也遵循供应链保护：target 版本必须先 checksum 验证才会被 mv 到生产
- 不允许 `main` 分支直升（防止 HEAD 不稳定）—— 强制传 tag 或明确 commit SHA

#### 5.9.6 测试覆盖

在 §12 测试方案里：
- L1 U6-U9：upgrade-kit.sh 的 4 个场景（正常升级 / checksum 失败 / rollback / dry-run）
- L2 I8：真实 Kit v0.1 → v0.2 升级场景 + 失败回滚

### 5.10 凭证生命周期（v0.3 新增，补强 S4）

`.deploy.env` 里的 `WECOM_BOT_WEBHOOK_URL` 是长期凭证。建议如下生命周期管理：

#### 5.10.1 轮换周期

- **建议周期**：每 6 个月主动轮换一次
- **强制轮换触发**：有任何下列事件时立即换
  - ops 账号疑似被攻破
  - 某项目服务器被淘汰 / 换手
  - 运维群结构调整（机器人更换）

#### 5.10.2 轮换流程

1. 企微群设置 → 删除旧机器人 → 添加新机器人 → 复制新 URL
2. 在 Kit 仓库的 README 或运维群置顶留一份"当前 webhook 活跃项目"清单
3. 遍历清单上每台机器：`nano /home/ops/<project>/.deploy.env` → 替换 URL → `chmod 600`
4. 各项目触发一次心跳（`./scripts/heartbeat.sh`）验证新 URL 工作
5. 全部验证通过后，旧机器人才能删除

#### 5.10.3 记录凭证创建时间

`.deploy.env` 模板增加一行注释：
```
# WECOM_BOT_WEBHOOK_URL 创建日期：2026-04-24（建议 2026-10-24 前轮换）
WECOM_BOT_WEBHOOK_URL=https://qyapi.weixin.qq.com/...
```

轮换时在 heartbeat.sh 里加一行检查：如果 `.deploy.env` 里的创建日期 > 6 个月，在心跳消息末尾加"⏰ webhook 已超 6 个月未轮换"的提示。

---

## 6. 接入流程（生产 10 分钟，含阅读）

> v0.2 已统一：不再宣称 "3 分钟"。加上阅读 README 与验证的时间，**10 分钟是实际上限**。
> 熟练用户实际命令执行 ~3 分钟，但**首次接入必须读 README** 了解 SLA 和配置约定。

**🔴 生产接入（clone + checksum）**：

```bash
# 0. 在业务机登录项目目录
ssh ops@<business-machine>
cd /home/ops/<project>

# 1. clone 指定 tag（不用 main，避免供应链问题）
git clone --depth=1 --branch=v1.0.0 https://github.com/neilding/ops-deploy-kit /tmp/kit-v1.0.0

# 2. 验证 bootstrap.sh 的 SHA256（预期值在 Kit README）
sha256sum /tmp/kit-v1.0.0/bootstrap.sh
# 和 README 公布的 checksum 比对，一致才继续

# 3.（可选）review 关键脚本
less /tmp/kit-v1.0.0/bootstrap.sh

# 4. 执行 bootstrap
/tmp/kit-v1.0.0/bootstrap.sh <project-name> $(pwd)

# 5. 填 webhook URL
nano .deploy.env
# 内容：WECOM_BOT_WEBHOOK_URL=https://qyapi.weixin.qq.com/...
chmod 600 .deploy.env

# 6. bootstrap 会提示你选 cron 方式（详见 §8 R5 fallback）

# 7.（可选）写项目专属 post_pull.sh
cat > scripts/post_pull.sh <<'EOF'
#!/bin/bash
set -e
source venv/bin/activate
pip install -q -r requirements.txt
# 项目特有的重启逻辑...
EOF
chmod +x scripts/post_pull.sh

# 8. 清理临时 clone
rm -rf /tmp/kit-v1.0.0
```

**🟡 快速试用模式**（仅非生产）：

```bash
curl -sL https://raw.githubusercontent.com/neilding/ops-deploy-kit/main/bootstrap.sh \
  | bash -s <project-name> $(pwd)
```

> ⚠️ 无 checksum 验证、无 review 机会。**仅用于个人工具 / 开发环境**。生产严禁。

完成。

---

## 7. 实施路线图

### Phase 1：从 ai-news-bot + uhomes-workorder 抽取 Kit（3-5 天）

| Task | 输出 | 估时 |
|---|---|---|
| P1.1 新建 `ops-deploy-kit` 仓库 | GitHub repo | 0.5d |
| P1.2 把 ai-news-bot 的 `wecom_notify.sh` / `auto_pull_deploy.sh` 抽取 + 参数化 | Kit v0.1 | 1d |
| P1.3 写 `bootstrap.sh` + `README.md` | 接入指南 | 0.5d |
| P1.4 写 `docs/WECOM_MARKDOWN_QUIRKS.md` 等踩坑文档 | 3 份 doc | 1d |
| P1.5 在**空白测试项目**上验证 bootstrap 流程 | 测试日志 | 0.5d |
| **P1.6 从 ai-news-bot 脚本拆分通用/特有部分**（v0.2 新增，补强 A4） | pip/playwright 剥到 `post_pull.sh` 示例 | 1d |
| **P1.7 编写心跳脚本 + SLA 文档**（v0.2 新增，补强 S2） | `heartbeat.sh` + README SLA 章节 | 0.5d |
| **P1.8 §12 测试方案中 L1 + L2**（v0.2 新增，补强 T1） | bats-core 单测 + docker 集测 | 1.5d |
| **P1.9 编写 upgrade-kit.sh**（v0.3 新增，补强 A6） | 见 §5.9 详设，含 dry-run/rollback/冒烟验证 | 0.5d |
| **Phase 1 小计** | | **7-8 d**（v0.3 再上修） |

### Phase 2：迁移存量项目（v0.3 细化，补强 O5）

不同项目复杂度差异很大，按具体工作量估算：

| 项目 | 当前状态 | 迁移工作量 [AI 估算] | 关键风险 |
|---|---|---|---|
| **ai-news-bot** | Kit 的 dogfood，已有新脚本 | **1d**（拆 post_pull.sh + L4 回归对比） | 迁移期间可能中断日报 → 选周末执行 |
| **uhomes-workorder** | 有 deploy-notify.sh + rollback tag + dry-run + rsync 部署 | **3-5d**（Kit 无 rsync 能力，需分 phase 1 支持 rsync hook 或保留原脚本只替换通知） | 复杂度远超 ai-news-bot。可能需**先扩 Kit 能力再迁** |
| **aifx** | 已有 auto_pull_deploy.sh 雏形（和 ai-news-bot 相似） | **1d**（模式相同） | 低 |
| **dianping / uhomes-inventory-ai / xhs-monitor** | 无 | **0.5d × N**（从零接入） | 低 |

**Phase 2 总工作量**：3 + uhomes-workorder(3-5) + 0.5×3 = **7.5-9.5 d** [AI 估算]（v0.1/v0.2 笼统"每项目 1-2d"严重低估 uhomes-workorder）

**迁移策略**：
- **保留旧脚本作 `.legacy` 备份**，切换后观察一周，稳定再删
- **先 ai-news-bot → 再 aifx**（相似 pattern，低风险验证）
- **uhomes-workorder 先解耦再迁**：Kit 暂只替换其通知模块，保留原部署脚本；等 Kit v1.1 支持 rsync hook 后再全迁



### Phase 3：扩展能力（未来，按需）

- `disk_alert.sh`：磁盘空间 > 85% 推告警
- `health_check.sh`：HTTP 健康检查失败推告警
- `systemd_watchdog.sh`：服务 oom / restart 过多推告警

这些不在本 PRD 范围内，只预留仓库结构扩展位。

---

## 8. 风险与缓解

| 风险 | 影响 | 概率 [AI 估算] | 缓解 |
|---|---|---|---|
| R1: Kit 升级时破坏存量项目 | 所有用 Kit 的项目部署挂 | 中 | 语义化版本；新版先在 ai-news-bot 试跑 1 周再发广播；各项目 pin 到具体 tag |
| R2: webhook URL 泄露（Kit 仓库不当存储） | 运维群被恶意发帖 | 低 | Kit 仓库**不存**任何真实 webhook，只给 `.env.example`；配置强制 `chmod 600` |
| R3: 用户复制 Kit 后未 pin 版本，Kit 改动反向影响 | 无感知断裂 | 中 | bootstrap.sh 默认 pin 到 Kit 最新稳定 tag，而非 main |
| R4: 不同操作系统（Ubuntu/Debian/CentOS）bash 差异 | 部分 bash 语法在某些发行版失效 | 低 | README 明确要求 `bash >= 4.0`；脚本头加 `#!/bin/bash`；在 Ubuntu 20.04 + 22.04 先验证 |
| R5: ops 用户在某些服务器**没有 crontab 权限** | Kit 不能自启部署 | 中 | **v0.2 补强**：`bootstrap.sh` 检测权限，3 条 fallback 路径（见下方） |
| R6: 项目使用自定义部署流程（不是 cron-pull） | Kit 的 `auto_pull_deploy.sh` 不适用 | 高 | Kit 拆分为"通知模块"（`wecom_notify.sh` 独立可用）+ "部署模板"（可选替换）；仅使用通知的项目无需 `auto_pull_deploy.sh` |

### 8.1 R5 fallback 详细方案（v0.2 新增，补强 O1）

`bootstrap.sh` 检测 crontab 写权限后按优先级选择：

**路径 A — 普通用户 crontab 可用（最常见）**
```bash
(crontab -l 2>/dev/null; echo "*/2 * * * * /home/ops/<project>/scripts/auto_pull_deploy.sh") | crontab -
```
bootstrap.sh 自动添加，用户无感知。

**路径 B — 用户级 systemd timer**（无 crontab 写权但有 systemd user 支持）
```bash
# bootstrap.sh 生成两个文件：
~/.config/systemd/user/ops-deploy-<project>.service
~/.config/systemd/user/ops-deploy-<project>.timer

# 用户一条命令启用：
systemctl --user enable --now ops-deploy-<project>.timer
```
Ubuntu/Debian 默认支持 user systemd；免 sudo。

**路径 C — 生成 /etc/cron.d snippet，让管理员 copy-paste**（兜底）
```bash
# bootstrap.sh 输出：
# ========== 请联系服务器管理员执行以下 1 条命令 ==========
sudo cp /tmp/ops-deploy-<project>.cron /etc/cron.d/<project>
# =====================================================
```
管理员只需 1 行 `cp`，不需要理解 Kit 内部。

**决策逻辑**：bootstrap.sh 自动检测 → 默认用 A；A 失败试 B；B 失败输出 C 的操作提示。

---

## 9. 成功指标

- **接入时间**：新项目接入从**当前 2-3 小时**缩短到 **≤ 30 分钟**（含阅读 README）
- **一致性**：存量项目（ai-news-bot + uhomes-workorder）在 1 个月内迁移完毕，通知格式统一
- **踩坑率**：新接入项目 **0 次**重现本次 session 的 wecom markdown / 时差类问题
- **可维护性**：Kit 月度维护 ≤ 2 小时

---

## 10. 关键决策点（需项目负责人拍板）

| 决策 | 选项 | 默认 | 理由 |
|---|---|---|---|
| D1: Kit 仓库是 public 还是 private | public / private | **private** | 脚本本身不含敏感信息但路径/命名约定暴露内部架构 |
| D2: 各项目用 git submodule 还是 curl 下载 | submodule / curl | **curl + 版本 pin** | submodule 对新手不友好，升级流程复杂；curl 简单直观 |
| D3: `bootstrap.sh` 是否固化 webhook 加载路径 | 是 / 否 | **否** | 保持方案 A 的灵活性——未来切堡垒机服务时只需改一处 |
| D4: Kit 是否纳入本项目（ai-news-bot）子目录起步 | 是 / 否 | **否** | ai-news-bot 是业务项目，Kit 是基础设施，分开演进 |

---

## 11. Gate-1 评审准备

本 PRD 完成后，按 CLAUDE.md §Gate-Review 要求，需要 5 位专家评审（均分 ≥ 8 分才能进入编码）。

### 11.1 建议评审维度

| 专家视角 | 关注点 | 最低分 |
|---|---|---|
| 🏗️ 架构师 | 是否符合单一职责 / 是否过度抽象 | 8 |
| 🔐 安全 | 凭证管理 / 权限边界 / 最小暴露面 | 8 |
| 🛠️ 运维 | 接入成本 / 可回滚性 / 故障隔离 | 8 |
| 🧪 测试 | 跨项目回归 / 发布流程 / 版本兼容 | 8 |
| 💰 成本/ROI | 抽象 vs 复制的 ROI 是否成立 | 8 |

### 11.2 评审前需补充（作者 TODO）

- [ ] 测试计划（Gate-1 要求"先测试方案再开发"）
- [ ] POC：在测试项目上跑通 bootstrap 流程的录屏/日志
- [ ] `ops-deploy-kit` 的 `README.md` 初稿（定义接口契约，评审据此给 feedback）

---

## 12. 测试方案（v0.2 新增，补强 T1）

### 12.1 测试层级总览

| 层级 | 目的 | 工具 | 通过标准 | 自动化 |
|---|---|---|---|---|
| **L1 单元** | 单脚本行为断言 | bats-core | 10 case 全绿 | 必须自动化 (CI) |
| **L2 集成** | 脚本组合流程 | docker compose + mock webhook | 5 关键 case 全绿 | 必须自动化 |
| **L3 E2E** | 完整流水线真跑 | staging 项目 + 真实 webhook | 通知格式符合 §5.4 | 半自动（人工核对） |
| **L4 回归** | 存量迁移前后对比 | diff | 字节级一致（除声明差异） | 手工 |

### 12.2 L1 单元测试 · `wecom_notify.sh`

| # | 场景 | 输入 | 期望行为 |
|---|---|---|---|
| U1 | webhook URL 未配置 | env 无 `WECOM_BOT_WEBHOOK_URL` | stderr 警告信息 + `exit 0` + **不发任何 HTTP 请求** |
| U2 | webhook URL 无效 | HTTP 返回 !=200 | stderr 含 HTTP code + exit 0 |
| U3 | HTTP 200 但企微 errcode != 0 | 模拟响应 `{"errcode":40001,"errmsg":"invalid key"}` | stderr 含 errmsg + exit 0 |
| U4 | 完全成功 | HTTP 200 + errcode 0 | 无 stderr + exit 0 |
| U5 | curl 网络超时 | mock 不响应 | stderr 含 "000" + exit 0 |

### 12.3 L1 单元测试 · `auto_pull_deploy.sh`

| # | 场景 | 前置条件 | 期望行为 |
|---|---|---|---|
| A1 | 无新 commit | LOCAL == REMOTE | 秒退，**不写 deploy.log**，不推通知 |
| A2 | 有新 commit + post_pull 成功 | mock post_pull.sh 返回 0 | 推成功通知，含 §5.4 所有字段 |
| A3 | post_pull 失败 | mock post_pull.sh 返回非 0 | 推失败通知，含退出码 |
| A4 | git fetch 网络失败（exit 128） | mock git fetch 返回 128 | 首 4 次不推；第 5 次累计触发告警；成功后重置计数 |
| A5 | 并发 flock 失败 | 模拟另一进程持锁 | 静默 exit 0，**不写日志** |

### 12.4 L2 集成测试

在 docker compose 中跑完整流水线：

**组件**：
- `mock-wecom`：nginx 容器模拟 webhook，把每次 POST 记录到 `/var/log/webhook.log`
- `test-project`：一个 fixture git 仓库 + 假的 post_pull.sh
- `test-kit`：挂载 Kit 脚本 + 调度器

**关键 case**：

| # | 场景 | 断言 |
|---|---|---|
| I1 | 完整 bootstrap 一个新项目 | scripts/ 出现所有文件 + 权限正确 + `.deploy.env.template` 生成 |
| I2 | 推一个 commit，auto_pull 触发 | mock-wecom 收到 1 条符合 §5.4 格式的 markdown |
| I3 | post_pull 主动失败 | mock-wecom 收到失败通知 + deploy.log 记录退出码 |
| I4 | 连续 5 次 git fetch 失败 | mock-wecom 第 5 次才收到 1 条"连续失败 5 次"告警 |
| I5 | heartbeat.sh 触发 | mock-wecom 收到 💓 心跳消息 |
| **I6** (v0.3 新增，T3) | bootstrap 中途网络中断 | `scripts/` 保持干净（无半损坏文件）；再跑一次 bootstrap 幂等成功 |
| **I7** (v0.3 新增，S5) | wecom_notify.sh 遇 http 错误，stderr 写入 deploy.log | log 中**不含** `key=` / `token=` 等敏感字段（测试断言 grep 为空） |
| **I8** (v0.3 新增，A6) | upgrade-kit.sh 从 v0.1 升到 v0.2，checksum 失败 | 自动触发 `--rollback`，scripts/ 回到 v0.1 状态，推告警通知 |

### 12.5 L3 E2E 测试（真实环境）

新建 staging 项目 `/home/ops/kit-staging/` 走完整生产接入流程：

1. clone + checksum + bootstrap
2. 填真实 webhook URL
3. 推几个 commit，观察真实运维群
4. 人工核对：
   - 通知 markdown 格式（对比 §5.4 模板）
   - Diff 链接点击能跳 GitHub compare
   - 心跳消息每天 10:00 准时到达（至少观察 3 天）
   - 通知样式在企微 PC / 移动端都正常

**v0.3 补强 T5：跨发行版强制要求**：
- **最低要求**：Ubuntu 22.04 LTS + Debian 12 各跑 1 次 E2E，产出各自 log
- **推荐加强**：加一遍 CentOS Stream 9（或 Rocky Linux 9），确认 bash 4.x / systemd 差异不炸
- **Alpine 不保证**：musl libc 和 busybox 的差异超出 Kit 承诺（见 §15 附录 D 已知限制）

### 12.6 L4 回归测试（ai-news-bot 迁移）

**迁移前**（当前状态）：跑 3 次真实 deploy，把通知文本复制到 `tests/before.txt`
**迁移到 Kit v1.0.0 后**：同样跑 3 次 deploy，收集 `tests/after.txt`
**通过标准**：`diff before.txt after.txt` 只能有以下声明的差异：
- 版本号行（commit SHA 必然变化）
- 时间戳行
- **变更** 列表行（如果 commit 数不同）
- **任何其他字段的格式变化都视为回归缺陷**，必须修复

如果发现回归，开 blocker issue，不得合并。

### 12.7 测试执行矩阵

| 时机 | 执行层级 | 谁负责 |
|---|---|---|
| 每次 PR | L1 + L2 | GitHub Actions CI |
| 每次 Release 前 | L1 + L2 + L3 | 项目 owner 手工跑 L3 |
| 接入新项目时 | L4 | 该项目接入者（和 owner 一起 review diff） |
| 发生生产告警后 | 对应问题层级的回归 case | owner + 报告者 |

### 12.8 测试覆盖率目标

- L1 + L2 行覆盖率 ≥ 80%（bash 天花板就这样，剩下 20% 是错误路径 + shell 内置）
- L3 每次 Release 至少 1 次完整跑通
- L4 每次迁移项目必做



（本 PRD 初筛发现与核实差异，评审过程中补充）

### v0.1 → v0.2 修正（基于 AUDIT_2026-04-24_PRD_OPS_KIT_GATE1.md）

| # | v0.1 问题 | v0.2 修正 | 修正位置 | 状态 |
|---|---|---|---|---|
| A1 | "10 分钟" vs "3 分钟" 接入时间前后不一致 | 统一为 "10 分钟（含 README 阅读）" | §2.1 G1、§6 标题 | ✅ 已修 |
| A2 | disk_alert.sh 在 §5.1 出现但 §2.2 又排除 | §5.1 改成 "Phase 3 扩展位" ；§2.2 加"未来扩展点"说明 | §2.2、§5.1 | ✅ 已修 |
| A3 | 版本化策略只是口号，没具体流程 | 加 §5.6 完整 SemVer + pin SHA + upgrade/rollback 命令 | §5.6 | ✅ 已修 |
| A4 | 从现有脚本抽取通用部分工作量未列入 Phase 1 | 加 P1.6（1d） | §7 表格 | ✅ 已修 |
| S1 | `curl \| bash` 供应链风险 | 加 §5.7：生产必须 clone + checksum + review；`curl \| bash` 降级为"快速试用"明确标注 | §5.7、§6 接入流程 | ✅ 已修 |
| S2 | 通知系统自监控缺失（uhomes-workorder 实证教训） | 加 §5.8：heartbeat.sh + SLA 约定 > 25h 无心跳告警 | §5.8、§7 P1.7 | ✅ 已修 |
| T1 | 测试方案空白 | 加整个 §12：L1/L2/L3/L4 四层 + 具体 test case + 执行矩阵 | §12、§7 P1.8 | ✅ 已修 |
| O1 | R5 (无 crontab 权限) 仅"联系管理员" | 加 §8.1：路径 A/B/C 三层 fallback，含 systemd user timer | §8.1 | ✅ 已修 |
| C1 | "10 个项目 × 2-3h" 假设未核实 | 加 §1.4 需求调研清单 + ROI 重算（6-12 个月回本） | §1.4 | ✅ 已修 |

### v0.2 未修项（🟢 可延后，接受现状）

- S3 `.deploy.env` 严格解析（`set -a; source` → grep + eval）—— 本地 600 权限已足够，defense in depth 延后
- O2 logrotate 自动配置 —— 日志量当前够用，项目接入 6+ 个后再评估
- C2 Kit 维护成本更精细估算 —— 已在 §1.4 修正为 "3-5h/月"
- C3 机会成本讨论 —— 已在用户确认"假设 A"后过时

### v0.2 → v0.3 修正（基于 AUDIT v2 的 8 项残留）

| # | v0.2 问题 | v0.3 修正 | 修正位置 | 状态 |
|---|---|---|---|---|
| A5 | bootstrap 离线路径未述 | 加附录 C 含 tar.gz + SHA256SUMS 全流程 | 附录 C | ✅ 已修 |
| A6 | `upgrade-kit.sh` 未定义 | 加 §5.9 完整设计（dry-run/rollback/原子替换/冒烟验证）+ P1.9 | §5.9、§7 P1.9、附录 B | ✅ 已修 |
| S4 | webhook 轮换流程空缺 | 加 §5.10 凭证生命周期 + heartbeat 6 月提醒 | §5.10 | ✅ 已修 |
| S5 | log 脱敏规则 | §12.4 加 I7 集成测试断言 | §12.4 | ✅ 已修 |
| T2 | 版本兼容矩阵 | §5.6 末尾加"版本共存"明确条款 + MAJOR 跨版迁移约束 | §5.6 | ✅ 已修 |
| T3 | bootstrap 回滚测试 | §12.4 加 I6 集成测试 case | §12.4 | ✅ 已修 |
| T4 | NFS flock 兼容 | 附录 D 已知限制列出 + 建议（本地 FS / PID 文件替代） | 附录 D | ✅ 已修（列为已知限制，不强保证） |
| T5 | 跨发行版测试 | §12.5 L3 加强制要求：Ubuntu 22.04 + Debian 12 + 推荐 Rocky 9 | §12.5 | ✅ 已修 |
| O5 | uhomes-workorder 迁移复杂度 | Phase 2 按项目细化，uhomes-workorder 单独 3-5d | §7 Phase 2 | ✅ 已修 |

### v0.3 未修项（🟢 继续延后）

以下属于"定义清晰的 future work"，不阻塞 Phase 1 编码：

- S3（`.deploy.env` 严格解析）：除非出现内部威胁，defense in depth 可延后
- O2（logrotate 自动配置）：等项目接入 6+ 个后再评估日志体量
- Phase 3 扩展（`disk_alert.sh` / `health_check.sh`）：Phase 1/2 稳定后按需求重启设计



---

## 13. 责任声明

本 PRD 为 AI 辅助撰写的初稿。所有工作量估算为 AI 基于文件大小 + 同类任务对标得出，**未经 POC 验证**。评分、优先级、架构判断均为 AI 主观判断，**不等于真人专家独立审查**。

最终实施方案、工作量承诺、技术选型拍板责任人：**项目负责人（neilding）**

---

## 附录 A：本次 ai-news-bot 接入踩坑汇总（Kit 的 docs/WECOM_MARKDOWN_QUIRKS.md 蓝本）

### A.1 wecom 群机器人 markdown 限制

- ❌ 裸 URL **不会** auto-link（既不蓝也不可点）
- ✅ `[text](url)` **可点击** 但 **不显色**（视觉上和普通文字一致）
- ✅ **反引号 \`code\`** 渲染为 monospace
- ✅ `**bold**` 渲染加粗
- ✅ `- list` 渲染为无序列表
- ⚠️ emoji 是唯一的**视觉 affordance**——想让用户知道某处可点，必须加 🔗 / ↗ / 👉 等符号提示

### A.2 bash 时差规律（N+2 commit 法则）

修改部署脚本本身时：
- Commit 1（格式变更）：脚本改动落盘，但当次 deploy 的 bash 进程用的是**旧内容内存快照**
- Commit 2（trigger）：cron 新 tick 读取磁盘上的**新脚本**运行 —— **此时才生效**

所以每次改格式需要**推 2 个 commit**才能看到最终效果。解决方案：
1. 推 2 次 commit（1 次改动 + 1 次空 commit 触发）
2. 或本地 `bash -x scripts/auto_pull_deploy.sh` 手工跑一次

### A.3 失败限频规则

`git fetch` 网络类失败（退出码 128）：
- 单次失败**不推通知**（GitHub 短暂抖动常见）
- 连续 5 次累计失败 → 推一次 "连续失败已达阈值" 告警
- 然后**静默 mute** 直到恢复成功（避免风暴）
- 恢复成功时清空计数器

阈值可通过 `NET_FAIL_THRESHOLD` 环境变量覆盖。

---

## 附录 B：Kit 升级操作手册（对应 §5.9）

（Phase 1 P1.9 交付后将此附录独立迁到 Kit README。此处作为 PRD 一部分保留作为引用。）

```bash
# 查看当前版本
cat scripts/.kit-version

# 列出本机已备份的历史版本
./scripts/upgrade-kit.sh --list

# 预览将要升级的差异（不实际改动）
./scripts/upgrade-kit.sh --dry-run v1.2.3

# 正式升级（自动备份 + 原子替换 + 冒烟验证 + 失败回滚）
./scripts/upgrade-kit.sh v1.2.3

# 回滚到最近一次升级前状态
./scripts/upgrade-kit.sh --rollback
```

升级过程中有 `.kit-backup/<timestamp>/` 保留旧版本，保留期 30 天自动清理。

---

## 附录 C：离线接入方式（v0.3 新增，补强 A5）

适用场景：目标服务器无 GitHub 访问权（内网隔离 / 国内网络抖动 / 防火墙限制）。

### C.1 离线 tar.gz 下载

每次 Kit Release 同时在 GitHub Release 页发布 `ops-deploy-kit-v1.2.3.tar.gz`，含：
- `bootstrap.sh` / `scripts/*.sh` / `templates/*` / `docs/*`
- `SHA256SUMS` 文件（一次性校验所有文件）

用户在任意一台能上 GitHub 的机器（比如自己的 Mac）下载，然后通过 JumpServer 文件管理或 SFTP 上传到目标服务器的 `/tmp/`。

### C.2 离线接入命令序列

```bash
# 目标服务器上
cd /tmp
tar -xzf ops-deploy-kit-v1.2.3.tar.gz
cd ops-deploy-kit-v1.2.3

# 校验全部文件的 SHA256
sha256sum --check SHA256SUMS

# 执行 bootstrap
./bootstrap.sh <project-name> /home/ops/<project-name>
```

### C.3 离线升级

`upgrade-kit.sh` 新增 `--local-tarball <path>` 参数：
```bash
./scripts/upgrade-kit.sh --local-tarball /tmp/ops-deploy-kit-v1.2.3.tar.gz
```
跳过 git clone，直接从本地 tar 解压 + checksum 校验 + 替换。

---

## 附录 D：已知限制（v0.3 新增，补强 T4）

Kit **不保证**以下场景能正常工作，遇到时降级到手工运维：

| 场景 | 原因 | 建议 |
|---|---|---|
| NFS / SMB / 其他网络文件系统 | `flock` 在部分实现上语义不同；可能失败或卡住 | 将 `$APP_DIR` 放在本地 FS；若必须用网络 FS，禁用 flock 改用 PID 文件 |
| Alpine Linux / BusyBox | 部分 bash 语法 / date 选项 / find 选项差异 | 不保证。想在 Alpine 跑自行定制 |
| bash < 4.0（CentOS 6 及以下）| `${var:0:8}` 等现代语法要 4.0+ | 升级 bash 或操作系统 |
| SELinux 严格模式 | 可能阻挡脚本写 `/etc/cron.d/` 等路径 | 管理员设 exception 或走 §8.1 路径 B |
| 无 `curl`（极简容器） | bootstrap 依赖 curl | 手工下载 tar.gz 离线安装（附录 C） |
| 企微自建应用 API（不是群机器人） | Kit 只支持群机器人 webhook | 不在本 PRD 范围；可另做扩展 |

遇到已知限制导致失败时，Kit 尽量输出清晰的 stderr 提示（不要静默挂）。

---

*文档结束*
