# Implementation Plan

- [x] 1. 创建通用部署脚本
  - 实现 deploy-app.sh 脚本，支持任意 Python 应用的部署
  - 包含参数验证、目录创建、Git 管理、虚拟环境配置、cron 设置等功能
  - _Requirements: 1.1, 1.2, 2.1, 4.1, 4.2_

- [x] 1.1 实现输入验证和错误处理
  - 验证应用名称格式（字母、数字、连字符）
  - 验证 Git URL 格式
  - 验证 cron 表达式格式（如果提供）
  - 实现 error_exit 函数统一处理错误
  - _Requirements: 4.1_

- [x] 1.2 实现目录结构创建
  - 创建 /opt/apps/{app_name} 主目录
  - 创建 code、venv、logs 子目录
  - 设置适当的目录权限
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 1.3 实现 Git 仓库管理
  - 检查 code 目录是否存在
  - 首次部署执行 git clone
  - 后续部署执行 git pull
  - 处理 Git 操作失败的情况
  - _Requirements: 4.1_

- [x] 1.4 实现 Python 虚拟环境管理
  - 创建 Python 虚拟环境在 venv 目录
  - 升级 pip 到最新版本
  - 从 requirements.txt 安装依赖
  - 处理依赖安装失败的情况
  - _Requirements: 2.1, 2.2, 4.2_

- [x] 1.5 实现环境变量文件管理
  - 检查 .env 文件是否存在
  - 如果不存在，创建 .env 模板
  - 设置文件权限为 600
  - 如果存在，保留现有配置
  - _Requirements: 5.1, 5.2, 6.2_

- [x] 1.6 实现 cron 任务配置
  - 生成 cron 条目（包含虚拟环境路径、日志重定向）
  - 检查 cron 条目是否已存在，避免重复
  - 添加 cron 条目到 crontab
  - 添加注释标识应用名称
  - _Requirements: 3.1, 3.2, 3.3, 4.4_

- [x] 1.7 实现日志轮转配置
  - 创建 logrotate 配置文件
  - 配置保留 10 个日志文件
  - 配置每日轮转和压缩
  - _Requirements: 7.1, 7.3_

- [x] 1.8 实现部署验证和输出
  - 验证所有目录已创建
  - 验证虚拟环境可用
  - 验证 cron 任务已添加
  - 输出部署摘要信息
  - 输出成功消息
  - _Requirements: 6.5_

- [-] 2. 创建测试框架和测试用例
  - 设置 pytest 和 hypothesis 测试环境
  - 创建测试辅助函数和 fixtures
  - _Requirements: All_

- [ ]* 2.1 编写属性测试：目录隔离
  - **Property 1: Directory Isolation**
  - **Validates: Requirements 1.1, 1.2, 1.3**
  - 使用 hypothesis 生成随机应用名称
  - 部署多个应用，验证目录完全隔离
  - 验证没有共享文件

- [ ]* 2.2 编写属性测试：虚拟环境独立性
  - **Property 2: Virtual Environment Independence**
  - **Validates: Requirements 2.1, 2.2, 2.3**
  - 生成随机依赖包列表
  - 验证依赖只安装在应用自己的 venv 中
  - 验证不影响其他应用或系统 Python

- [ ]* 2.3 编写属性测试：Cron 任务执行
  - **Property 3: Cron Job Execution**
  - **Validates: Requirements 3.1, 3.2, 3.3**
  - 验证 cron 条目包含正确的虚拟环境路径
  - 验证日志重定向到正确位置
  - 验证 cron 表达式格式正确

- [ ]* 2.4 编写属性测试：部署幂等性
  - **Property 4: Deployment Idempotence**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
  - 多次运行部署脚本
  - 验证最终状态一致
  - 验证没有错误或重复配置

- [ ]* 2.5 编写属性测试：环境变量安全
  - **Property 5: Environment Variable Security**
  - **Validates: Requirements 5.1, 5.2**
  - 验证 .env 文件权限为 600
  - 验证其他用户无法读取
  - 验证文件所有者正确

- [ ]* 2.6 编写属性测试：日志文件可访问性
  - **Property 6: Log File Accessibility**
  - **Validates: Requirements 7.1, 7.2**
  - 验证日志文件在正确目录
  - 验证日志文件可写入
  - 验证所有者可读取

- [x] 3. 创建 AI 新闻机器人迁移文档
  - 编写详细的迁移步骤文档
  - 包含服务器准备、部署执行、配置、测试等步骤
  - 提供故障排查指南
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 4. 准备部署脚本使用文档
  - 编写 README 说明脚本用法
  - 提供多个部署示例
  - 说明参数含义和可选项
  - 包含常见问题解答
  - _Requirements: All_

- [x] 5. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.
