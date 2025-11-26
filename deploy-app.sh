#!/bin/bash
# deploy-app.sh - Universal Python application deployment script
# Usage: deploy-app.sh <app_name> <git_repo_url> [cron_schedule]

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error handling function
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Success message function
success_msg() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Info message function
info_msg() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Validate application name format (alphanumeric and hyphens only)
validate_app_name() {
    local app_name="$1"
    
    if [[ -z "$app_name" ]]; then
        error_exit "Application name cannot be empty"
    fi
    
    if [[ ! "$app_name" =~ ^[a-zA-Z0-9-]+$ ]]; then
        error_exit "Application name must contain only letters, numbers, and hyphens"
    fi
    
    success_msg "Application name validated: $app_name"
}

# Validate Git URL format
validate_git_url() {
    local git_url="$1"
    
    if [[ -z "$git_url" ]]; then
        error_exit "Git repository URL cannot be empty"
    fi
    
    # Check for common Git URL patterns (https, git, ssh)
    if [[ ! "$git_url" =~ ^(https?://|git@|ssh://|git://) ]]; then
        error_exit "Invalid Git URL format. Must start with https://, git@, ssh://, or git://"
    fi
    
    success_msg "Git URL validated: $git_url"
}

# Validate cron expression format (basic validation)
validate_cron_schedule() {
    local cron_schedule="$1"
    
    if [[ -z "$cron_schedule" ]]; then
        return 0  # Optional parameter, empty is OK
    fi
    
    # Basic cron format validation: 5 fields separated by spaces
    # Format: minute hour day month weekday
    local field_count=$(echo "$cron_schedule" | awk '{print NF}')
    
    if [[ "$field_count" -ne 5 ]]; then
        error_exit "Invalid cron schedule format. Expected 5 fields (minute hour day month weekday), got $field_count"
    fi
    
    success_msg "Cron schedule validated: $cron_schedule"
}

# Main validation function
validate_inputs() {
    local app_name="$1"
    local git_url="$2"
    local cron_schedule="${3:-}"
    
    info_msg "Validating inputs..."
    validate_app_name "$app_name"
    validate_git_url "$git_url"
    validate_cron_schedule "$cron_schedule"
}

# Setup directory structure
setup_directories() {
    local app_name="$1"
    local app_dir="/opt/apps/$app_name"
    local code_dir="$app_dir/code"
    local venv_dir="$app_dir/venv"
    local logs_dir="$app_dir/logs"
    
    info_msg "Setting up directory structure..."
    
    # Create main application directory
    if [[ ! -d "$app_dir" ]]; then
        mkdir -p "$app_dir" || error_exit "Failed to create application directory: $app_dir"
        success_msg "Created application directory: $app_dir"
    else
        info_msg "Application directory already exists: $app_dir"
    fi
    
    # Create subdirectories
    for dir in "$code_dir" "$venv_dir" "$logs_dir"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir" || error_exit "Failed to create directory: $dir"
            success_msg "Created directory: $dir"
        else
            info_msg "Directory already exists: $dir"
        fi
    done
    
    # Set appropriate permissions (755 for directories)
    chmod 755 "$app_dir" || error_exit "Failed to set permissions on $app_dir"
    chmod 755 "$code_dir" || error_exit "Failed to set permissions on $code_dir"
    chmod 755 "$venv_dir" || error_exit "Failed to set permissions on $venv_dir"
    chmod 755 "$logs_dir" || error_exit "Failed to set permissions on $logs_dir"
    
    success_msg "Directory structure setup complete"
}

# Manage Git repository (clone or pull)
manage_git_repo() {
    local app_name="$1"
    local git_url="$2"
    local code_dir="/opt/apps/$app_name/code"
    
    info_msg "Managing Git repository..."
    
    # Check if code directory has a Git repository
    if [[ -d "$code_dir/.git" ]]; then
        info_msg "Git repository exists, pulling latest changes..."
        cd "$code_dir" || error_exit "Failed to change directory to $code_dir"
        
        # Pull latest changes
        if git pull; then
            success_msg "Successfully pulled latest changes"
        else
            error_exit "Failed to pull latest changes from Git repository"
        fi
    else
        info_msg "No Git repository found, cloning..."
        
        # Remove code directory if it exists but is not a Git repo
        if [[ -d "$code_dir" ]] && [[ ! -d "$code_dir/.git" ]]; then
            rm -rf "$code_dir" || error_exit "Failed to remove existing code directory"
            mkdir -p "$code_dir" || error_exit "Failed to recreate code directory"
        fi
        
        # Clone the repository
        if git clone "$git_url" "$code_dir"; then
            success_msg "Successfully cloned repository"
        else
            error_exit "Failed to clone Git repository from $git_url"
        fi
    fi
    
    # Return to original directory
    cd - > /dev/null || true
}

# Setup Python virtual environment
setup_virtualenv() {
    local app_name="$1"
    local venv_dir="/opt/apps/$app_name/venv"
    local code_dir="/opt/apps/$app_name/code"
    local requirements_file="$code_dir/requirements.txt"
    
    info_msg "Setting up Python virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "$venv_dir/bin" ]]; then
        info_msg "Creating new virtual environment..."
        if python3 -m venv "$venv_dir"; then
            success_msg "Virtual environment created"
        else
            error_exit "Failed to create virtual environment"
        fi
    else
        info_msg "Virtual environment already exists"
    fi
    
    # Upgrade pip
    info_msg "Upgrading pip..."
    if "$venv_dir/bin/pip" install --upgrade pip > /dev/null 2>&1; then
        success_msg "Pip upgraded to latest version"
    else
        error_exit "Failed to upgrade pip"
    fi
    
    # Install dependencies from requirements.txt
    if [[ -f "$requirements_file" ]]; then
        info_msg "Installing dependencies from requirements.txt..."
        if "$venv_dir/bin/pip" install -r "$requirements_file"; then
            success_msg "Dependencies installed successfully"
        else
            error_exit "Failed to install dependencies from $requirements_file"
        fi
    else
        info_msg "No requirements.txt found, skipping dependency installation"
    fi
}

# Configure environment variable file
configure_env_file() {
    local app_name="$1"
    local env_file="/opt/apps/$app_name/.env"
    
    info_msg "Configuring environment variable file..."
    
    # Check if .env file exists
    if [[ -f "$env_file" ]]; then
        info_msg ".env file already exists, preserving existing configuration"
        success_msg "Existing .env file preserved"
    else
        info_msg "Creating .env template..."
        
        # Create .env template with common variables
        cat > "$env_file" << 'EOF'
# Environment variables for application
# Edit this file and add your configuration

# Example variables (uncomment and set as needed):
# API_KEY=your_api_key_here
# DATABASE_URL=your_database_url_here
# DEBUG=false

EOF
        
        if [[ $? -eq 0 ]]; then
            success_msg ".env template created"
        else
            error_exit "Failed to create .env template"
        fi
    fi
    
    # Set file permissions to 600 (read/write for owner only)
    if chmod 600 "$env_file"; then
        success_msg ".env file permissions set to 600"
    else
        error_exit "Failed to set permissions on .env file"
    fi
}

# Setup cron job
setup_cron_job() {
    local app_name="$1"
    local cron_schedule="$2"
    local code_dir="/opt/apps/$app_name/code"
    local venv_dir="/opt/apps/$app_name/venv"
    local logs_dir="/opt/apps/$app_name/logs"
    
    # Skip if no cron schedule provided
    if [[ -z "$cron_schedule" ]]; then
        info_msg "No cron schedule provided, skipping cron job setup"
        return 0
    fi
    
    info_msg "Setting up cron job..."
    
    # Find the main Python script (look for common entry points)
    local entry_script=""
    for script in "bot_wecom.py" "start.py" "main.py" "app.py"; do
        if [[ -f "$code_dir/$script" ]]; then
            entry_script="$script"
            break
        fi
    done
    
    if [[ -z "$entry_script" ]]; then
        info_msg "No standard entry point found (bot_wecom.py, start.py, main.py, app.py)"
        info_msg "Skipping cron job setup - please configure manually"
        return 0
    fi
    
    # Generate cron entry
    local cron_comment="# $app_name - Automated task"
    local cron_entry="$cron_schedule cd $code_dir && $venv_dir/bin/python3 $entry_script >> $logs_dir/app.log 2>&1"
    
    # Check if cron entry already exists
    if crontab -l 2>/dev/null | grep -F "$code_dir" | grep -F "$entry_script" > /dev/null; then
        info_msg "Cron job already exists for this application"
        
        # Update existing cron job
        local temp_cron=$(mktemp)
        crontab -l 2>/dev/null | grep -v -F "$code_dir" | grep -v -F "$entry_script" > "$temp_cron" || true
        echo "$cron_comment" >> "$temp_cron"
        echo "$cron_entry" >> "$temp_cron"
        
        if crontab "$temp_cron"; then
            success_msg "Cron job updated"
        else
            rm -f "$temp_cron"
            error_exit "Failed to update cron job"
        fi
        rm -f "$temp_cron"
    else
        info_msg "Adding new cron job..."
        
        # Add new cron entry
        local temp_cron=$(mktemp)
        crontab -l 2>/dev/null > "$temp_cron" || true
        echo "" >> "$temp_cron"
        echo "$cron_comment" >> "$temp_cron"
        echo "$cron_entry" >> "$temp_cron"
        
        if crontab "$temp_cron"; then
            success_msg "Cron job added: $entry_script at schedule '$cron_schedule'"
        else
            rm -f "$temp_cron"
            error_exit "Failed to add cron job"
        fi
        rm -f "$temp_cron"
    fi
}

# Setup log rotation
setup_log_rotation() {
    local app_name="$1"
    local logs_dir="/opt/apps/$app_name/logs"
    local logrotate_config="/etc/logrotate.d/$app_name"
    
    info_msg "Setting up log rotation..."
    
    # Check if we have permission to write to /etc/logrotate.d
    if [[ ! -w "/etc/logrotate.d" ]]; then
        info_msg "No write permission to /etc/logrotate.d, skipping log rotation setup"
        info_msg "Run this script with sudo to enable log rotation"
        return 0
    fi
    
    # Create logrotate configuration
    cat > "$logrotate_config" << EOF
$logs_dir/app.log {
    daily
    rotate 10
    compress
    missingok
    notifempty
    create 0644 $(whoami) $(whoami)
}
EOF
    
    if [[ $? -eq 0 ]]; then
        success_msg "Log rotation configured: keeping 10 daily logs"
    else
        error_exit "Failed to create logrotate configuration"
    fi
}

# Verify deployment
verify_deployment() {
    local app_name="$1"
    local app_dir="/opt/apps/$app_name"
    local code_dir="$app_dir/code"
    local venv_dir="$app_dir/venv"
    local logs_dir="$app_dir/logs"
    local env_file="$app_dir/.env"
    
    info_msg "Verifying deployment..."
    
    local verification_failed=0
    
    # Verify directories exist
    for dir in "$app_dir" "$code_dir" "$venv_dir" "$logs_dir"; do
        if [[ -d "$dir" ]]; then
            success_msg "Directory exists: $dir"
        else
            echo -e "${RED}✗ Directory missing: $dir${NC}"
            verification_failed=1
        fi
    done
    
    # Verify virtual environment is functional
    if [[ -x "$venv_dir/bin/python3" ]]; then
        local python_version=$("$venv_dir/bin/python3" --version 2>&1)
        success_msg "Virtual environment functional: $python_version"
    else
        echo -e "${RED}✗ Virtual environment not functional${NC}"
        verification_failed=1
    fi
    
    # Verify .env file exists with correct permissions
    if [[ -f "$env_file" ]]; then
        local env_perms=$(stat -c "%a" "$env_file" 2>/dev/null || stat -f "%A" "$env_file" 2>/dev/null)
        if [[ "$env_perms" == "600" ]]; then
            success_msg ".env file exists with correct permissions (600)"
        else
            echo -e "${YELLOW}⚠ .env file has permissions $env_perms (expected 600)${NC}"
        fi
    else
        echo -e "${RED}✗ .env file missing${NC}"
        verification_failed=1
    fi
    
    # Verify cron job (if applicable)
    if crontab -l 2>/dev/null | grep -F "$code_dir" > /dev/null; then
        success_msg "Cron job configured"
    else
        info_msg "No cron job configured (this is OK if not needed)"
    fi
    
    if [[ $verification_failed -eq 1 ]]; then
        error_exit "Deployment verification failed"
    fi
    
    success_msg "Deployment verification passed"
}

# Print deployment summary
print_summary() {
    local app_name="$1"
    local app_dir="/opt/apps/$app_name"
    local code_dir="$app_dir/code"
    local venv_dir="$app_dir/venv"
    local logs_dir="$app_dir/logs"
    local env_file="$app_dir/.env"
    
    echo ""
    echo "=========================================="
    echo "  Deployment Summary"
    echo "=========================================="
    echo "Application Name: $app_name"
    echo "Application Directory: $app_dir"
    echo "Code Directory: $code_dir"
    echo "Virtual Environment: $venv_dir"
    echo "Logs Directory: $logs_dir"
    echo "Environment File: $env_file"
    echo ""
    echo "Next Steps:"
    echo "1. Edit environment variables: nano $env_file"
    echo "2. Test the application manually:"
    echo "   cd $code_dir"
    echo "   $venv_dir/bin/python3 <your_script.py>"
    echo "3. View logs: tail -f $logs_dir/app.log"
    echo "4. Check cron jobs: crontab -l"
    echo "=========================================="
    echo ""
}

# Display usage information
usage() {
    cat << EOF
Usage: $0 <app_name> <git_repo_url> [cron_schedule]

Arguments:
  app_name        Application name (alphanumeric and hyphens only)
  git_repo_url    Git repository URL
  cron_schedule   Optional cron schedule (e.g., "0 9 * * *")

Examples:
  $0 ai-news-bot https://github.com/user/repo.git "0 9 * * *"
  $0 my-app https://github.com/user/my-app.git

EOF
    exit 1
}

# Main execution
main() {
    # Check arguments
    if [[ $# -lt 2 ]]; then
        usage
    fi
    
    local app_name="$1"
    local git_url="$2"
    local cron_schedule="${3:-}"
    
    echo ""
    echo "=========================================="
    echo "  Universal Python App Deployment"
    echo "=========================================="
    echo ""
    
    # Execute deployment steps
    validate_inputs "$app_name" "$git_url" "$cron_schedule"
    setup_directories "$app_name"
    manage_git_repo "$app_name" "$git_url"
    setup_virtualenv "$app_name"
    configure_env_file "$app_name"
    setup_cron_job "$app_name" "$cron_schedule"
    setup_log_rotation "$app_name"
    verify_deployment "$app_name"
    
    # Print summary
    print_summary "$app_name"
    
    echo -e "${GREEN}=========================================="
    echo -e "  ✓ Deployment completed successfully!"
    echo -e "==========================================${NC}"
    echo ""
}

# Run main function
main "$@"
