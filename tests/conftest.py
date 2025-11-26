"""
Test configuration and fixtures for deployment script testing.

This module provides shared fixtures and utilities for testing the
deploy-app.sh script and related deployment functionality.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any
import pytest


@pytest.fixture
def temp_test_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for testing that mimics /opt/apps structure.
    
    Yields:
        Path: Temporary directory path
        
    Cleanup:
        Removes the temporary directory after test completion
    """
    temp_dir = tempfile.mkdtemp(prefix="test_deploy_")
    temp_path = Path(temp_dir)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_apps_dir(temp_test_dir: Path) -> Path:
    """
    Create a mock /opt/apps directory structure for testing.
    
    Args:
        temp_test_dir: Temporary directory fixture
        
    Returns:
        Path: Mock apps directory path
    """
    apps_dir = temp_test_dir / "apps"
    apps_dir.mkdir(parents=True, exist_ok=True)
    return apps_dir


@pytest.fixture
def sample_app_structure(mock_apps_dir: Path) -> Dict[str, Path]:
    """
    Create a sample application directory structure.
    
    Args:
        mock_apps_dir: Mock apps directory fixture
        
    Returns:
        Dict containing paths to app directories
    """
    app_name = "test-app"
    app_dir = mock_apps_dir / app_name
    
    # Create directory structure
    code_dir = app_dir / "code"
    venv_dir = app_dir / "venv"
    logs_dir = app_dir / "logs"
    
    for directory in [code_dir, venv_dir, logs_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create sample files
    env_file = app_dir / ".env"
    env_file.write_text("# Test environment variables\nTEST_VAR=test_value\n")
    env_file.chmod(0o600)
    
    requirements_file = code_dir / "requirements.txt"
    requirements_file.write_text("requests==2.31.0\n")
    
    main_script = code_dir / "main.py"
    main_script.write_text('#!/usr/bin/env python3\nprint("Hello from test app")\n')
    
    return {
        "app_dir": app_dir,
        "code_dir": code_dir,
        "venv_dir": venv_dir,
        "logs_dir": logs_dir,
        "env_file": env_file,
        "app_name": app_name
    }


@pytest.fixture
def mock_git_repo(temp_test_dir: Path) -> Path:
    """
    Create a mock Git repository for testing.
    
    Args:
        temp_test_dir: Temporary directory fixture
        
    Returns:
        Path: Git repository path
    """
    repo_dir = temp_test_dir / "mock_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=repo_dir,
        capture_output=True,
        check=True
    )
    
    # Configure git user for commits
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        capture_output=True,
        check=True
    )
    
    # Create sample files
    requirements_file = repo_dir / "requirements.txt"
    requirements_file.write_text("requests==2.31.0\npython-dotenv==1.0.0\n")
    
    main_script = repo_dir / "bot_wecom.py"
    main_script.write_text('#!/usr/bin/env python3\nprint("Bot running")\n')
    
    # Commit files
    subprocess.run(
        ["git", "add", "."],
        cwd=repo_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        capture_output=True,
        check=True
    )
    
    return repo_dir


@pytest.fixture
def deploy_script_path() -> Path:
    """
    Get the path to the deploy-app.sh script.
    
    Returns:
        Path: Deployment script path
    """
    script_path = Path(__file__).parent.parent / "deploy-app.sh"
    
    if not script_path.exists():
        pytest.skip("deploy-app.sh not found")
    
    # Ensure script is executable
    script_path.chmod(0o755)
    
    return script_path


class DeploymentHelper:
    """
    Helper class for testing deployment operations.
    
    Provides utilities for running deployment scripts, checking directory
    structures, validating permissions, and verifying deployment state.
    """
    
    @staticmethod
    def run_deploy_script(
        script_path: Path,
        app_name: str,
        git_url: str,
        cron_schedule: str = "",
        env: Dict[str, str] = None
    ) -> subprocess.CompletedProcess:
        """
        Run the deployment script with given parameters.
        
        Args:
            script_path: Path to deploy-app.sh
            app_name: Application name
            git_url: Git repository URL
            cron_schedule: Optional cron schedule
            env: Optional environment variables
            
        Returns:
            CompletedProcess: Result of script execution
        """
        cmd = [str(script_path), app_name, git_url]
        if cron_schedule:
            cmd.append(cron_schedule)
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env or os.environ.copy()
        )
    
    @staticmethod
    def verify_directory_structure(app_dir: Path) -> bool:
        """
        Verify that application directory structure is correct.
        
        Args:
            app_dir: Application directory path
            
        Returns:
            bool: True if structure is valid
        """
        required_dirs = ["code", "venv", "logs"]
        
        if not app_dir.exists():
            return False
        
        for subdir in required_dirs:
            if not (app_dir / subdir).is_dir():
                return False
        
        return True
    
    @staticmethod
    def verify_env_file_permissions(env_file: Path) -> bool:
        """
        Verify .env file has correct permissions (600).
        
        Args:
            env_file: Path to .env file
            
        Returns:
            bool: True if permissions are correct
        """
        if not env_file.exists():
            return False
        
        stat_info = env_file.stat()
        permissions = oct(stat_info.st_mode)[-3:]
        
        return permissions == "600"
    
    @staticmethod
    def verify_virtualenv(venv_dir: Path) -> bool:
        """
        Verify virtual environment is properly set up.
        
        Args:
            venv_dir: Virtual environment directory path
            
        Returns:
            bool: True if venv is valid
        """
        python_bin = venv_dir / "bin" / "python3"
        pip_bin = venv_dir / "bin" / "pip"
        
        return python_bin.exists() and pip_bin.exists()
    
    @staticmethod
    def get_cron_jobs() -> str:
        """
        Get current user's cron jobs.
        
        Returns:
            str: Cron job listing
        """
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout if result.returncode == 0 else ""
        except Exception:
            return ""
    
    @staticmethod
    def check_cron_job_exists(app_name: str, code_dir: Path) -> bool:
        """
        Check if cron job exists for given application.
        
        Args:
            app_name: Application name
            code_dir: Code directory path
            
        Returns:
            bool: True if cron job exists
        """
        cron_jobs = DeploymentHelper.get_cron_jobs()
        return str(code_dir) in cron_jobs
    
    @staticmethod
    def validate_app_name(app_name: str) -> bool:
        """
        Validate application name format.
        
        Args:
            app_name: Application name to validate
            
        Returns:
            bool: True if name is valid
        """
        import re
        return bool(re.match(r'^[a-zA-Z0-9-]+$', app_name))
    
    @staticmethod
    def validate_git_url(git_url: str) -> bool:
        """
        Validate Git URL format.
        
        Args:
            git_url: Git URL to validate
            
        Returns:
            bool: True if URL is valid
        """
        import re
        pattern = r'^(https?://|git@|ssh://|git://)'
        return bool(re.match(pattern, git_url))
    
    @staticmethod
    def validate_cron_schedule(cron_schedule: str) -> bool:
        """
        Validate cron schedule format.
        
        Args:
            cron_schedule: Cron schedule to validate
            
        Returns:
            bool: True if schedule is valid
        """
        if not cron_schedule:
            return True  # Empty is valid (optional)
        
        parts = cron_schedule.split()
        return len(parts) == 5


@pytest.fixture
def deployment_helper() -> DeploymentHelper:
    """
    Provide deployment helper instance for tests.
    
    Returns:
        DeploymentHelper: Helper instance
    """
    return DeploymentHelper()


# Hypothesis strategies for property-based testing
from hypothesis import strategies as st


def app_name_strategy():
    """
    Generate valid application names for property-based testing.
    
    Returns:
        Strategy: Hypothesis strategy for app names
    """
    # Generate alphanumeric strings with optional hyphens
    # Ensure it starts and ends with alphanumeric
    alphanumeric = st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        min_size=1,
        max_size=20
    )
    
    # Optionally add hyphens in the middle
    return st.builds(
        lambda start, middle, end: f"{start}{middle}{end}",
        alphanumeric,
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-', max_size=28),
        st.just('')
    ).filter(lambda x: len(x) <= 50 and '--' not in x and not x.endswith('-'))


def git_url_strategy():
    """
    Generate valid Git URLs for property-based testing.
    
    Returns:
        Strategy: Hypothesis strategy for Git URLs
    """
    protocols = st.sampled_from(['https://', 'git@', 'ssh://', 'git://'])
    
    # Simple domain generation
    domain_parts = st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=10),
        min_size=2,
        max_size=3
    ).map(lambda parts: '.'.join(parts))
    
    # Simple path generation
    path_parts = st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_', min_size=1, max_size=15),
        min_size=1,
        max_size=3
    ).map(lambda parts: '/'.join(parts))
    
    return st.builds(
        lambda p, d, path: f"{p}{d}/{path}.git",
        protocols,
        domain_parts,
        path_parts
    )


def cron_schedule_strategy():
    """
    Generate valid cron schedules for property-based testing.
    
    Returns:
        Strategy: Hypothesis strategy for cron schedules
    """
    minute = st.integers(min_value=0, max_value=59).map(str) | st.just('*')
    hour = st.integers(min_value=0, max_value=23).map(str) | st.just('*')
    day = st.integers(min_value=1, max_value=31).map(str) | st.just('*')
    month = st.integers(min_value=1, max_value=12).map(str) | st.just('*')
    weekday = st.integers(min_value=0, max_value=6).map(str) | st.just('*')
    
    return st.builds(
        lambda m, h, d, mo, w: f"{m} {h} {d} {mo} {w}",
        minute, hour, day, month, weekday
    )
