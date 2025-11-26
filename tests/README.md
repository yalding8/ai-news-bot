# Testing Framework Documentation

## Overview

This testing framework provides comprehensive testing infrastructure for the deployment script (`deploy-app.sh`) using pytest and hypothesis for property-based testing.

## Setup

### Install Dependencies

```bash
pip install -r requirements-dev.txt
```

This installs:
- `pytest` - Testing framework
- `hypothesis` - Property-based testing library
- `pytest-cov` - Code coverage plugin

### Configuration

The testing framework is configured via `pytest.ini` in the project root:

- **Test discovery**: Automatically finds `test_*.py` files
- **Markers**: Categorize tests (unit, property, integration, slow)
- **Hypothesis**: Configured to run 100 examples per property test
- **Output**: Verbose mode with short tracebacks

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_deployment_framework.py
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only property-based tests
pytest -m property

# Run integration tests
pytest -m integration
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html
```

### Verbose Output

```bash
pytest -v
```

## Test Structure

### Test Files

- `conftest.py` - Shared fixtures and utilities
- `test_deployment_framework.py` - Framework validation tests
- `test_deployment_*.py` - Property-based tests for deployment (to be created)

### Fixtures

#### `temp_test_dir`
Creates a temporary directory for testing, automatically cleaned up after tests.

```python
def test_example(temp_test_dir):
    # temp_test_dir is a Path object
    test_file = temp_test_dir / "test.txt"
    test_file.write_text("content")
```

#### `mock_apps_dir`
Creates a mock `/opt/apps` directory structure.

```python
def test_example(mock_apps_dir):
    # mock_apps_dir mimics /opt/apps
    app_dir = mock_apps_dir / "my-app"
```

#### `sample_app_structure`
Creates a complete application directory structure with all subdirectories and files.

```python
def test_example(sample_app_structure):
    app_dir = sample_app_structure["app_dir"]
    code_dir = sample_app_structure["code_dir"]
    venv_dir = sample_app_structure["venv_dir"]
    logs_dir = sample_app_structure["logs_dir"]
    env_file = sample_app_structure["env_file"]
```

#### `mock_git_repo`
Creates a mock Git repository with sample files and commits.

```python
def test_example(mock_git_repo):
    # mock_git_repo is a Path to a git repository
    assert (mock_git_repo / ".git").exists()
```

#### `deployment_helper`
Provides a `DeploymentHelper` instance with utility methods.

```python
def test_example(deployment_helper):
    assert deployment_helper.validate_app_name("my-app")
```

## DeploymentHelper Utilities

The `DeploymentHelper` class provides utility methods for testing:

### Validation Methods

```python
helper = DeploymentHelper()

# Validate application name
helper.validate_app_name("my-app")  # Returns True/False

# Validate Git URL
helper.validate_git_url("https://github.com/user/repo.git")  # Returns True/False

# Validate cron schedule
helper.validate_cron_schedule("0 9 * * *")  # Returns True/False
```

### Verification Methods

```python
# Verify directory structure
helper.verify_directory_structure(app_dir)  # Returns True/False

# Verify .env file permissions
helper.verify_env_file_permissions(env_file)  # Returns True/False

# Verify virtual environment
helper.verify_virtualenv(venv_dir)  # Returns True/False
```

### Cron Management

```python
# Get current cron jobs
cron_jobs = helper.get_cron_jobs()

# Check if cron job exists for app
exists = helper.check_cron_job_exists("my-app", code_dir)
```

## Hypothesis Strategies

The framework provides custom Hypothesis strategies for generating test data:

### `app_name_strategy()`
Generates valid application names (alphanumeric and hyphens).

```python
from hypothesis import given
from conftest import app_name_strategy

@given(app_name_strategy())
def test_property(app_name):
    # app_name is a valid application name
    assert validate_app_name(app_name)
```

### `git_url_strategy()`
Generates valid Git URLs with various protocols.

```python
@given(git_url_strategy())
def test_property(git_url):
    # git_url is a valid Git URL
    assert validate_git_url(git_url)
```

### `cron_schedule_strategy()`
Generates valid cron schedules (5 fields).

```python
@given(cron_schedule_strategy())
def test_property(cron_schedule):
    # cron_schedule is a valid cron expression
    assert validate_cron_schedule(cron_schedule)
```

## Writing Property-Based Tests

Property-based tests verify that properties hold across many randomly generated inputs.

### Example Property Test

```python
from hypothesis import given
from conftest import app_name_strategy, DeploymentHelper

@pytest.mark.property
@given(app_name_strategy())
def test_property_directory_isolation(app_name):
    """
    Feature: digitalocean-migration, Property 1: Directory Isolation
    
    For any application name, deploying creates isolated directories.
    """
    helper = DeploymentHelper()
    
    # Test implementation
    # ...
    
    assert condition_holds
```

### Property Test Requirements

1. **Annotation**: Mark with `@pytest.mark.property`
2. **Documentation**: Include feature name and property number
3. **Validation**: Reference requirements being validated
4. **Iterations**: Configured to run 100 examples (in pytest.ini)

## Best Practices

### Test Organization

- Group related tests in classes
- Use descriptive test names
- Add docstrings explaining what is tested
- Mark tests with appropriate markers

### Fixtures

- Use fixtures for setup/teardown
- Keep fixtures focused and reusable
- Document fixture behavior

### Property Tests

- Test universal properties, not specific examples
- Use appropriate strategies for input generation
- Ensure properties are meaningful and testable
- Document which requirements are validated

### Assertions

- Use clear, specific assertions
- Provide helpful error messages
- Test one concept per test

## Troubleshooting

### Tests Not Found

Ensure test files start with `test_` and are in the `tests/` directory.

### Import Errors

Use relative imports from `conftest`:
```python
from conftest import DeploymentHelper
```

### Hypothesis Failures

If Hypothesis finds a counterexample, it will show the failing input:
```
Falsifying example: test_name(value='problematic_input')
```

Use this to debug and fix the issue.

### Permission Errors

Some tests may require elevated permissions (e.g., cron management). Run with appropriate permissions or mock system calls.

## Next Steps

After setting up the framework:

1. Implement property-based tests for each correctness property
2. Run tests regularly during development
3. Maintain high test coverage
4. Update tests when requirements change
