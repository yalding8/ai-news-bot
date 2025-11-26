# Deploy Script Usage Guide

## Overview

`deploy-app.sh` is a universal deployment script for Python applications on Linux servers. It automates the entire deployment process including directory setup, Git repository management, Python virtual environment configuration, cron job scheduling, and log rotation.

**Key Features:**
- ✅ Automated directory structure creation
- ✅ Git repository cloning and updates
- ✅ Python virtual environment management
- ✅ Dependency installation from requirements.txt
- ✅ Environment variable file management
- ✅ Cron job configuration
- ✅ Log rotation setup
- ✅ Idempotent operations (safe to run multiple times)

## Installation

### Prerequisites

Ensure your server has the following installed:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git logrotate
```

### Install the Script

1. **Download the script to your server:**

```bash
# Option 1: Using scp from your local machine
scp deploy-app.sh root@your-server-ip:/usr/local/bin/

# Option 2: Using wget (if hosted online)
sudo wget -O /usr/local/bin/deploy-app.sh https://your-url/deploy-app.sh

# Option 3: Create manually
sudo nano /usr/local/bin/deploy-app.sh
# Paste the script content and save
```

2. **Make the script executable:**

```bash
sudo chmod +x /usr/local/bin/deploy-app.sh
```

3. **Verify installation:**

```bash
deploy-app.sh
# Should display usage information
```

## Usage

### Basic Syntax

```bash
deploy-app.sh <app_name> <git_repo_url> [cron_schedule]
```

### Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `app_name` | Yes | Application name (alphanumeric and hyphens only) | `ai-news-bot` |
| `git_repo_url` | Yes | Git repository URL (https, git, or ssh) | `https://github.com/user/repo.git` |
| `cron_schedule` | No | Cron expression for scheduled execution | `"0 9 * * *"` |

### Parameter Details

#### app_name
- Must contain only letters, numbers, and hyphens
- Used to create directory structure at `/opt/apps/{app_name}`
- Examples: `my-app`, `news-bot`, `data-processor`

#### git_repo_url
- Supports multiple Git URL formats:
  - HTTPS: `https://github.com/user/repo.git`
  - SSH: `git@github.com:user/repo.git`
  - Git protocol: `git://github.com/user/repo.git`
- Repository must be accessible from the server
- For private repositories, ensure SSH keys are configured

#### cron_schedule
- Optional parameter for automated execution
- Standard cron format: `minute hour day month weekday`
- If omitted, no cron job will be created
- Examples:
  - `"0 9 * * *"` - Daily at 9:00 AM
  - `"*/30 * * * *"` - Every 30 minutes
  - `"0 0 * * 0"` - Weekly on Sunday at midnight
  - `"0 */6 * * *"` - Every 6 hours

## Deployment Examples

### Example 1: Deploy AI News Bot with Daily Schedule

```bash
deploy-app.sh ai-news-bot https://github.com/yalding8/ai-news-bot.git "0 9 * * *"
```

This will:
- Create `/opt/apps/ai-news-bot/` directory structure
- Clone the repository to `/opt/apps/ai-news-bot/code/`
- Set up virtual environment in `/opt/apps/ai-news-bot/venv/`
- Install dependencies from requirements.txt
- Create `.env` template file
- Configure cron job to run daily at 9:00 AM
- Set up log rotation

### Example 2: Deploy Web Scraper without Cron

```bash
deploy-app.sh web-scraper https://github.com/user/scraper.git
```

This will deploy the application without setting up a cron job. You can run it manually or configure scheduling later.

### Example 3: Deploy Data Processor with Hourly Schedule

```bash
deploy-app.sh data-processor git@github.com:company/processor.git "0 * * * *"
```

Uses SSH Git URL and runs every hour on the hour.

### Example 4: Deploy API Service (Manual Execution)

```bash
deploy-app.sh api-service https://github.com/user/api.git
```

For services that run continuously (like web servers), deploy without cron and manage with systemd or run manually.

### Example 5: Update Existing Application

```bash
# Run the same command again to update
deploy-app.sh ai-news-bot https://github.com/yalding8/ai-news-bot.git "0 9 * * *"
```

The script is idempotent - running it again will:
- Pull latest code from Git
- Update dependencies
- Preserve existing `.env` file
- Update cron job if schedule changed

## Directory Structure

After deployment, your application will have the following structure:

```
/opt/apps/{app_name}/
├── code/                 # Git repository (all source code)
│   ├── *.py             # Python scripts
│   ├── requirements.txt # Dependencies
│   ├── .git/            # Git metadata
│   └── ...
├── venv/                # Python virtual environment
│   ├── bin/
│   │   ├── python3      # Python interpreter
│   │   ├── pip          # Package installer
│   │   └── ...
│   ├── lib/
│   └── ...
├── logs/                # Application logs
│   ├── app.log          # Current log file
│   ├── app.log.1.gz     # Rotated logs
│   └── ...
└── .env                 # Environment variables (600 permissions)
```

## Post-Deployment Configuration

### 1. Configure Environment Variables

After deployment, edit the `.env` file to add your configuration:

```bash
# Edit the .env file
nano /opt/apps/ai-news-bot/.env
```

Example `.env` content:

```bash
# API Keys
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
TIANAPI_KEY=xxxxxxxxxxxxx

# WeChat Configuration
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx

# Application Settings
ACTIVE_TOPICS=ai,education,technology
DEBUG=false
```

**Important:** The `.env` file has 600 permissions (read/write for owner only) for security.

### 2. Test Manual Execution

Before relying on cron, test your application manually:

```bash
# Navigate to code directory
cd /opt/apps/ai-news-bot/code

# Run using the virtual environment
/opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py

# Check for errors
echo $?  # Should return 0 for success
```

### 3. Verify Cron Job

Check that the cron job was created:

```bash
# List all cron jobs
crontab -l

# You should see something like:
# ai-news-bot - Automated task
# 0 9 * * * cd /opt/apps/ai-news-bot/code && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /opt/apps/ai-news-bot/logs/app.log 2>&1
```

### 4. Monitor Logs

View application logs in real-time:

```bash
# Follow log file
tail -f /opt/apps/ai-news-bot/logs/app.log

# View last 100 lines
tail -n 100 /opt/apps/ai-news-bot/logs/app.log

# Search for errors
grep -i "error\|failed\|exception" /opt/apps/ai-news-bot/logs/app.log
```

## Common Operations

### Update Application Code

To update an existing application with the latest code:

```bash
# Re-run the deployment script
deploy-app.sh ai-news-bot https://github.com/yalding8/ai-news-bot.git "0 9 * * *"
```

Or manually:

```bash
cd /opt/apps/ai-news-bot/code
git pull
/opt/apps/ai-news-bot/venv/bin/pip install -r requirements.txt --upgrade
```

### Modify Cron Schedule

To change the execution schedule:

```bash
# Edit crontab
crontab -e

# Or re-run deployment with new schedule
deploy-app.sh ai-news-bot https://github.com/yalding8/ai-news-bot.git "0 */6 * * *"
```

### Remove Cron Job

```bash
# Edit crontab and delete the relevant lines
crontab -e
```

### View Application Status

```bash
# Check if virtual environment is working
/opt/apps/ai-news-bot/venv/bin/python3 --version

# Check installed packages
/opt/apps/ai-news-bot/venv/bin/pip list

# Check Git status
cd /opt/apps/ai-news-bot/code
git status
git log -1  # View last commit
```

### Backup Application

```bash
# Backup entire application directory
tar -czf ai-news-bot-backup-$(date +%Y%m%d).tar.gz /opt/apps/ai-news-bot/

# Backup only .env file
cp /opt/apps/ai-news-bot/.env ~/ai-news-bot-env-backup
```

## Troubleshooting

### Issue 1: Script Permission Denied

**Symptom:**
```
bash: deploy-app.sh: Permission denied
```

**Solution:**
```bash
sudo chmod +x /usr/local/bin/deploy-app.sh
```

### Issue 2: Git Clone Fails

**Symptom:**
```
ERROR: Failed to clone Git repository
```

**Possible Causes & Solutions:**

1. **Network connectivity:**
   ```bash
   ping github.com
   ```

2. **Invalid Git URL:**
   ```bash
   # Test Git URL manually
   git ls-remote https://github.com/user/repo.git
   ```

3. **Private repository without SSH keys:**
   ```bash
   # Generate SSH key
   ssh-keygen -t ed25519 -C "your_email@example.com"
   
   # Add to GitHub
   cat ~/.ssh/id_ed25519.pub
   # Copy and add to GitHub Settings > SSH Keys
   ```

### Issue 3: Dependency Installation Fails

**Symptom:**
```
ERROR: Failed to install dependencies
```

**Solution:**
```bash
# Check requirements.txt exists
ls -la /opt/apps/ai-news-bot/code/requirements.txt

# Try manual installation with verbose output
/opt/apps/ai-news-bot/venv/bin/pip install -r /opt/apps/ai-news-bot/code/requirements.txt -v

# Update pip first
/opt/apps/ai-news-bot/venv/bin/pip install --upgrade pip
```

### Issue 4: Cron Job Not Executing

**Symptom:**
Cron job is configured but application doesn't run at scheduled time.

**Diagnosis:**

1. **Check cron service status:**
   ```bash
   systemctl status cron
   ```

2. **Check cron logs:**
   ```bash
   grep CRON /var/log/syslog
   ```

3. **Verify timezone:**
   ```bash
   timedatectl
   # Cron uses system timezone
   ```

4. **Test cron entry manually:**
   ```bash
   # Copy the command from crontab -l and run it
   cd /opt/apps/ai-news-bot/code && /opt/apps/ai-news-bot/venv/bin/python3 bot_wecom.py >> /opt/apps/ai-news-bot/logs/app.log 2>&1
   ```

**Solutions:**

```bash
# Restart cron service
sudo systemctl restart cron

# Check for syntax errors in crontab
crontab -l

# Ensure cron has correct PATH
# Add to crontab:
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

### Issue 5: Environment Variables Not Loading

**Symptom:**
Application fails with missing API keys or configuration.

**Solution:**

1. **Verify .env file exists:**
   ```bash
   ls -la /opt/apps/ai-news-bot/.env
   ```

2. **Check file permissions:**
   ```bash
   stat /opt/apps/ai-news-bot/.env
   # Should show 600 permissions
   ```

3. **Verify content:**
   ```bash
   cat /opt/apps/ai-news-bot/.env
   ```

4. **Ensure application loads .env:**
   ```python
   # Your Python code should include:
   from dotenv import load_dotenv
   load_dotenv()
   ```

5. **Install python-dotenv if missing:**
   ```bash
   /opt/apps/ai-news-bot/venv/bin/pip install python-dotenv
   ```

### Issue 6: Log Files Not Created

**Symptom:**
No log files appear in `/opt/apps/{app_name}/logs/`

**Solution:**

1. **Check directory permissions:**
   ```bash
   ls -ld /opt/apps/ai-news-bot/logs/
   # Should be writable
   ```

2. **Manually create log file:**
   ```bash
   touch /opt/apps/ai-news-bot/logs/app.log
   chmod 644 /opt/apps/ai-news-bot/logs/app.log
   ```

3. **Verify cron redirects output:**
   ```bash
   crontab -l
   # Should end with: >> /opt/apps/ai-news-bot/logs/app.log 2>&1
   ```

### Issue 7: "Invalid Application Name" Error

**Symptom:**
```
ERROR: Application name must contain only letters, numbers, and hyphens
```

**Solution:**
Use only alphanumeric characters and hyphens in application names:

```bash
# ✅ Valid names
deploy-app.sh my-app ...
deploy-app.sh app123 ...
deploy-app.sh data-processor-v2 ...

# ❌ Invalid names
deploy-app.sh my_app ...      # Underscores not allowed
deploy-app.sh my.app ...      # Dots not allowed
deploy-app.sh "my app" ...    # Spaces not allowed
```

### Issue 8: Disk Space Full

**Symptom:**
```
ERROR: No space left on device
```

**Solution:**

1. **Check disk usage:**
   ```bash
   df -h
   ```

2. **Find large files:**
   ```bash
   du -sh /opt/apps/* | sort -h
   ```

3. **Clean old logs:**
   ```bash
   # Remove old compressed logs
   find /opt/apps/*/logs/ -name "*.gz" -mtime +30 -delete
   ```

4. **Clean pip cache:**
   ```bash
   /opt/apps/ai-news-bot/venv/bin/pip cache purge
   ```

## Advanced Usage

### Deploy Multiple Applications

You can deploy multiple applications on the same server:

```bash
# Deploy first application
deploy-app.sh app1 https://github.com/user/app1.git "0 9 * * *"

# Deploy second application
deploy-app.sh app2 https://github.com/user/app2.git "0 10 * * *"

# Deploy third application
deploy-app.sh app3 https://github.com/user/app3.git "*/15 * * * *"
```

Each application is completely isolated with its own:
- Directory structure
- Virtual environment
- Dependencies
- Environment variables
- Logs
- Cron schedule

### Custom Entry Points

The script automatically detects common entry points in this order:
1. `bot_wecom.py`
2. `start.py`
3. `main.py`
4. `app.py`

If your application uses a different entry point, you can:

**Option 1: Rename your script**
```bash
cd /opt/apps/my-app/code
mv custom_script.py main.py
```

**Option 2: Manually configure cron**
```bash
crontab -e
# Add your custom entry point:
# 0 9 * * * cd /opt/apps/my-app/code && /opt/apps/my-app/venv/bin/python3 custom_script.py >> /opt/apps/my-app/logs/app.log 2>&1
```

### Using with Private Git Repositories

For private repositories, set up SSH authentication:

```bash
# Generate SSH key (if not already done)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Display public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub/GitLab:
# GitHub: Settings > SSH and GPG keys > New SSH key
# GitLab: Preferences > SSH Keys

# Test connection
ssh -T git@github.com

# Deploy using SSH URL
deploy-app.sh my-app git@github.com:user/private-repo.git "0 9 * * *"
```

### Running as Non-Root User

For better security, you can run applications as a non-root user:

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash appuser

# Create apps directory with proper ownership
sudo mkdir -p /opt/apps
sudo chown appuser:appuser /opt/apps

# Switch to appuser
sudo su - appuser

# Deploy as appuser
deploy-app.sh my-app https://github.com/user/repo.git "0 9 * * *"
```

**Note:** Log rotation requires root access, so you may need to configure it separately.

### Integration with CI/CD

You can integrate the deployment script with CI/CD pipelines:

**GitHub Actions Example:**

```yaml
name: Deploy to Server

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to DigitalOcean
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_IP }}
          username: root
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            deploy-app.sh my-app https://github.com/user/repo.git "0 9 * * *"
```

## Cron Schedule Reference

Quick reference for common cron schedules:

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Every minute | `* * * * *` | Runs every minute |
| Every 5 minutes | `*/5 * * * *` | Runs every 5 minutes |
| Every 15 minutes | `*/15 * * * *` | Runs every 15 minutes |
| Every 30 minutes | `*/30 * * * *` | Runs every 30 minutes |
| Every hour | `0 * * * *` | Runs at minute 0 of every hour |
| Every 6 hours | `0 */6 * * *` | Runs at 00:00, 06:00, 12:00, 18:00 |
| Daily at 9 AM | `0 9 * * *` | Runs at 9:00 AM every day |
| Daily at midnight | `0 0 * * *` | Runs at 12:00 AM every day |
| Weekly (Sunday) | `0 0 * * 0` | Runs at midnight every Sunday |
| Monthly (1st day) | `0 0 1 * *` | Runs at midnight on the 1st of each month |
| Weekdays at 9 AM | `0 9 * * 1-5` | Runs at 9:00 AM Monday-Friday |
| Weekends at 10 AM | `0 10 * * 0,6` | Runs at 10:00 AM Saturday-Sunday |

**Cron Format:**
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, 0 and 7 are Sunday)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

## Security Best Practices

1. **Protect .env files:**
   - Never commit .env files to Git
   - Always verify 600 permissions
   - Rotate API keys regularly

2. **Use SSH keys for Git:**
   - Avoid storing passwords in scripts
   - Use SSH agent for key management

3. **Run as non-root when possible:**
   - Create dedicated user accounts
   - Use sudo only when necessary

4. **Keep software updated:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

5. **Monitor logs regularly:**
   ```bash
   # Check for suspicious activity
   grep -i "error\|failed\|unauthorized" /opt/apps/*/logs/app.log
   ```

6. **Backup regularly:**
   ```bash
   # Automated backup script
   tar -czf /backup/apps-$(date +%Y%m%d).tar.gz /opt/apps/
   ```

## FAQ

### Q: Can I deploy the same application multiple times?

**A:** No, each application name must be unique. If you need multiple instances, use different names:
```bash
deploy-app.sh app-prod https://github.com/user/app.git "0 9 * * *"
deploy-app.sh app-staging https://github.com/user/app.git "0 10 * * *"
```

### Q: How do I remove a deployed application?

**A:** Manually remove the directory and cron job:
```bash
# Remove cron job
crontab -e
# Delete the relevant lines

# Remove application directory
sudo rm -rf /opt/apps/my-app

# Remove logrotate config
sudo rm /etc/logrotate.d/my-app
```

### Q: Can I use this script on other Linux distributions?

**A:** Yes, but you may need to adjust package installation commands:
- **CentOS/RHEL:** Use `yum` instead of `apt`
- **Arch Linux:** Use `pacman` instead of `apt`
- **macOS:** Some commands may differ (e.g., `stat` syntax)

### Q: Does this work with Python 2?

**A:** No, the script uses `python3` explicitly. Python 2 is deprecated and should not be used.

### Q: Can I deploy non-Python applications?

**A:** The script is designed for Python applications. For other languages, you would need to modify the virtual environment and dependency installation sections.

### Q: How do I change the Python version?

**A:** Install the desired Python version and modify the script to use it:
```bash
# Install Python 3.11
sudo apt install python3.11 python3.11-venv

# Modify script to use python3.11 instead of python3
```

### Q: What if my application needs system-level dependencies?

**A:** Install them before running the deployment script:
```bash
# Example: Install system dependencies for image processing
sudo apt install -y libpng-dev libjpeg-dev

# Then deploy
deploy-app.sh my-app https://github.com/user/app.git
```

### Q: Can I run the application as a service instead of cron?

**A:** Yes, you can create a systemd service after deployment:
```bash
# Create service file
sudo nano /etc/systemd/system/my-app.service

# Add configuration (see systemd documentation)
# Then enable and start
sudo systemctl enable my-app
sudo systemctl start my-app
```

### Q: How do I handle database migrations?

**A:** Run migrations manually after deployment:
```bash
cd /opt/apps/my-app/code
/opt/apps/my-app/venv/bin/python3 manage.py migrate
```

Or add a migration step to your application's entry point.

## Support and Contributing

### Getting Help

If you encounter issues not covered in this guide:

1. Check application logs: `tail -f /opt/apps/{app_name}/logs/app.log`
2. Check system logs: `grep CRON /var/log/syslog`
3. Verify all prerequisites are installed
4. Test each component manually

### Reporting Issues

When reporting issues, include:
- Operating system and version
- Python version
- Complete error message
- Steps to reproduce
- Relevant log excerpts

## Changelog

### Version 1.0.0
- Initial release
- Basic deployment functionality
- Git repository management
- Virtual environment setup
- Cron job configuration
- Log rotation
- Environment variable management

## License

This deployment script is provided as-is for use in deploying Python applications.

---

**Last Updated:** November 2025
**Script Version:** 1.0.0
