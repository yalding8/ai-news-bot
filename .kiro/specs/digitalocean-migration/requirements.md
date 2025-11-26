# Requirements Document

## Introduction

本文档定义了将 AI 新闻机器人从阿里云迁移到 DigitalOcean 服务器的 MVP 需求。目标是用最简单的方式实现应用迁移，支持多应用部署的基本隔离，确保核心功能正常运行。

## Glossary

- **Target Server**: 目标 DigitalOcean 服务器，将承载多个应用程序
- **Application**: 独立的应用程序实例，如 AI 新闻机器人
- **Deployment Script**: 部署脚本，负责应用程序的部署和更新
- **Virtual Environment**: Python 虚拟环境，用于隔离应用依赖

## Requirements

### Requirement 1

**User Story:** 作为系统管理员，我希望在 DigitalOcean 服务器上建立简单的目录结构，以便组织多个应用程序。

#### Acceptance Criteria

1. WHEN 服务器初始化完成 THEN the Deployment Script SHALL create directory structure /opt/apps/{app_name} for each application
2. WHEN 应用程序部署 THEN the Deployment Script SHALL create subdirectories for code and logs within the application directory
3. WHEN 多个应用程序部署 THEN the Deployment Script SHALL ensure each application has its own isolated directory

### Requirement 2

**User Story:** 作为开发者，我希望每个应用程序拥有独立的 Python 虚拟环境，以便避免依赖冲突。

#### Acceptance Criteria

1. WHEN 应用程序部署 THEN the Deployment Script SHALL create a Python virtual environment in /opt/apps/{app_name}/venv
2. WHEN 安装依赖包 THEN the Deployment Script SHALL install dependencies from requirements.txt into the virtual environment
3. WHEN 应用程序运行 THEN the Deployment Script SHALL use the virtual environment's Python interpreter

### Requirement 3

**User Story:** 作为系统管理员，我希望使用 cron 定时任务运行应用程序，以便实现自动化执行。

#### Acceptance Criteria

1. WHEN 应用程序部署完成 THEN the Deployment Script SHALL create a cron job entry for the application
2. WHEN cron 任务执行 THEN the Deployment Script SHALL activate the virtual environment before running the application
3. WHEN 应用程序执行 THEN the Deployment Script SHALL redirect output to the application's log file
4. WHEN 查看定时任务 THEN the Deployment Script SHALL allow listing all configured cron jobs

### Requirement 4

**User Story:** 作为系统管理员，我希望有一个简单的部署脚本，以便快速部署和更新应用程序。

#### Acceptance Criteria

1. WHEN 执行部署脚本 THEN the Deployment Script SHALL clone or pull the latest code from Git repository
2. WHEN 代码更新完成 THEN the Deployment Script SHALL install or update dependencies in the virtual environment
3. WHEN 依赖安装完成 THEN the Deployment Script SHALL copy the .env file to the application directory
4. WHEN 配置完成 THEN the Deployment Script SHALL update the cron job with the correct paths

### Requirement 5

**User Story:** 作为系统管理员，我希望安全地管理环境变量，以便保护 API 密钥等敏感信息。

#### Acceptance Criteria

1. WHEN 应用程序部署 THEN the Deployment Script SHALL create a .env file in the application directory
2. WHEN .env 文件创建 THEN the Deployment Script SHALL set file permissions to 600
3. WHEN 应用程序运行 THEN the Application SHALL load environment variables from the .env file

### Requirement 6

**User Story:** 作为系统管理员，我希望迁移现有的 AI 新闻机器人到 DigitalOcean 服务器，以便验证部署流程。

#### Acceptance Criteria

1. WHEN 执行迁移 THEN the Deployment Script SHALL deploy the ai-news-bot application to /opt/apps/ai-news-bot
2. WHEN 应用部署完成 THEN the Deployment Script SHALL configure environment variables from the existing .env file
3. WHEN 配置完成 THEN the Deployment Script SHALL set up a cron job to run daily at 9:00 AM
4. WHEN cron 任务首次执行 THEN the Application SHALL successfully fetch news and send messages to WeChat
5. WHEN 验证完成 THEN the Deployment Script SHALL log the deployment success message

### Requirement 7

**User Story:** 作为系统管理员，我希望能够查看应用程序日志，以便排查问题。

#### Acceptance Criteria

1. WHEN 应用程序运行 THEN the Deployment Script SHALL write logs to /opt/apps/{app_name}/logs/app.log
2. WHEN 查看日志 THEN the Deployment Script SHALL provide a command to tail the log file
3. WHEN 日志文件过大 THEN the Deployment Script SHALL implement basic log rotation to keep only recent 10 log files
