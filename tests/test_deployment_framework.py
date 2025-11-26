"""
Basic tests to verify the testing framework is properly configured.

This module contains simple tests to ensure pytest, hypothesis, and
all fixtures are working correctly before running property-based tests.
"""

import pytest
from pathlib import Path
from hypothesis import given, strategies as st
from conftest import (
    app_name_strategy,
    git_url_strategy,
    cron_schedule_strategy,
    DeploymentHelper
)


class TestFrameworkSetup:
    """Test that the testing framework is properly configured."""
    
    def test_pytest_working(self):
        """Verify pytest is functioning."""
        assert True
    
    def test_temp_dir_fixture(self, temp_test_dir):
        """Verify temp_test_dir fixture creates a directory."""
        assert temp_test_dir.exists()
        assert temp_test_dir.is_dir()
    
    def test_mock_apps_dir_fixture(self, mock_apps_dir):
        """Verify mock_apps_dir fixture creates apps directory."""
        assert mock_apps_dir.exists()
        assert mock_apps_dir.name == "apps"
    
    def test_sample_app_structure_fixture(self, sample_app_structure):
        """Verify sample_app_structure fixture creates complete structure."""
        assert sample_app_structure["app_dir"].exists()
        assert sample_app_structure["code_dir"].exists()
        assert sample_app_structure["venv_dir"].exists()
        assert sample_app_structure["logs_dir"].exists()
        assert sample_app_structure["env_file"].exists()
    
    def test_mock_git_repo_fixture(self, mock_git_repo):
        """Verify mock_git_repo fixture creates a git repository."""
        assert mock_git_repo.exists()
        assert (mock_git_repo / ".git").exists()
        assert (mock_git_repo / "requirements.txt").exists()
    
    def test_deployment_helper_fixture(self, deployment_helper):
        """Verify deployment_helper fixture provides helper instance."""
        assert isinstance(deployment_helper, DeploymentHelper)


class TestDeploymentHelper:
    """Test DeploymentHelper utility methods."""
    
    def test_verify_directory_structure_valid(self, sample_app_structure, deployment_helper):
        """Test directory structure verification with valid structure."""
        app_dir = sample_app_structure["app_dir"]
        assert deployment_helper.verify_directory_structure(app_dir)
    
    def test_verify_directory_structure_invalid(self, temp_test_dir, deployment_helper):
        """Test directory structure verification with invalid structure."""
        invalid_dir = temp_test_dir / "invalid_app"
        invalid_dir.mkdir()
        assert not deployment_helper.verify_directory_structure(invalid_dir)
    
    def test_verify_env_file_permissions(self, sample_app_structure, deployment_helper):
        """Test .env file permission verification."""
        env_file = sample_app_structure["env_file"]
        assert deployment_helper.verify_env_file_permissions(env_file)
    
    def test_validate_app_name_valid(self, deployment_helper):
        """Test app name validation with valid names."""
        assert deployment_helper.validate_app_name("my-app")
        assert deployment_helper.validate_app_name("app123")
        assert deployment_helper.validate_app_name("MyApp")
    
    def test_validate_app_name_invalid(self, deployment_helper):
        """Test app name validation with invalid names."""
        assert not deployment_helper.validate_app_name("my app")  # space
        assert not deployment_helper.validate_app_name("my_app")  # underscore
        assert not deployment_helper.validate_app_name("my@app")  # special char
        assert not deployment_helper.validate_app_name("")  # empty
    
    def test_validate_git_url_valid(self, deployment_helper):
        """Test Git URL validation with valid URLs."""
        assert deployment_helper.validate_git_url("https://github.com/user/repo.git")
        assert deployment_helper.validate_git_url("git@github.com:user/repo.git")
        assert deployment_helper.validate_git_url("ssh://git@github.com/user/repo.git")
        assert deployment_helper.validate_git_url("git://github.com/user/repo.git")
    
    def test_validate_git_url_invalid(self, deployment_helper):
        """Test Git URL validation with invalid URLs."""
        assert not deployment_helper.validate_git_url("github.com/user/repo.git")
        assert not deployment_helper.validate_git_url("ftp://github.com/user/repo.git")
        assert not deployment_helper.validate_git_url("")
    
    def test_validate_cron_schedule_valid(self, deployment_helper):
        """Test cron schedule validation with valid schedules."""
        assert deployment_helper.validate_cron_schedule("0 9 * * *")
        assert deployment_helper.validate_cron_schedule("*/5 * * * *")
        assert deployment_helper.validate_cron_schedule("0 0 1 1 0")
        assert deployment_helper.validate_cron_schedule("")  # empty is valid
    
    def test_validate_cron_schedule_invalid(self, deployment_helper):
        """Test cron schedule validation with invalid schedules."""
        assert not deployment_helper.validate_cron_schedule("0 9 * *")  # 4 fields
        assert not deployment_helper.validate_cron_schedule("0 9 * * * *")  # 6 fields
        assert not deployment_helper.validate_cron_schedule("invalid")


class TestHypothesisIntegration:
    """Test that Hypothesis property-based testing is working."""
    
    @given(st.integers())
    def test_hypothesis_basic(self, n):
        """Verify Hypothesis can generate integers."""
        assert isinstance(n, int)
    
    @given(app_name_strategy())
    def test_app_name_strategy_generates_valid_names(self, app_name):
        """Verify app_name_strategy generates valid application names."""
        helper = DeploymentHelper()
        assert helper.validate_app_name(app_name)
    
    @given(git_url_strategy())
    def test_git_url_strategy_generates_valid_urls(self, git_url):
        """Verify git_url_strategy generates valid Git URLs."""
        helper = DeploymentHelper()
        assert helper.validate_git_url(git_url)
    
    @given(cron_schedule_strategy())
    def test_cron_schedule_strategy_generates_valid_schedules(self, cron_schedule):
        """Verify cron_schedule_strategy generates valid cron schedules."""
        helper = DeploymentHelper()
        assert helper.validate_cron_schedule(cron_schedule)


@pytest.mark.unit
class TestValidationFunctions:
    """Unit tests for validation helper functions."""
    
    def test_app_name_alphanumeric_only(self, deployment_helper):
        """Test that app names accept only alphanumeric and hyphens."""
        valid_names = ["app", "my-app", "app123", "MyApp-2"]
        for name in valid_names:
            assert deployment_helper.validate_app_name(name), f"Failed for: {name}"
    
    def test_git_url_protocol_required(self, deployment_helper):
        """Test that Git URLs require valid protocol."""
        valid_protocols = [
            "https://github.com/user/repo.git",
            "git@github.com:user/repo.git",
            "ssh://git@server.com/repo.git",
            "git://server.com/repo.git"
        ]
        for url in valid_protocols:
            assert deployment_helper.validate_git_url(url), f"Failed for: {url}"
    
    def test_cron_schedule_five_fields(self, deployment_helper):
        """Test that cron schedules require exactly 5 fields."""
        assert deployment_helper.validate_cron_schedule("0 9 * * *")
        assert not deployment_helper.validate_cron_schedule("0 9 * *")
        assert not deployment_helper.validate_cron_schedule("0 9 * * * *")
