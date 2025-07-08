# Development Documentation

## Overview

This guide provides comprehensive information for developers working on the GitLab Homelab infrastructure project. It covers development setup, coding standards, testing requirements, and contribution guidelines.

## Development Environment

### 1. Prerequisites

- Git with GPG signing configured
- Python 3.12+
- Docker for DevContainer development
- VS Code with DevContainers extension
- Optional: kubectl, microk8s, or k3s for testing

### 2. DevContainer Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/tzervas/gitlab-homelab.git
   cd gitlab-homelab
   ```

2. Open in VS Code:
   ```bash
   code .
   ```

3. Install DevContainers extension

4. Press `F1` and select "Dev Containers: Reopen in Container"

### 3. Local Development Setup

```bash
# Install Python dependencies
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y jq shellcheck
```

## Code Quality

### 1. Code Formatting

- Black for Python code formatting
- isort for import sorting
- Ruff for linting
- shellcheck for shell scripts

```bash
# Format Python code
black .

# Sort imports
isort .

# Run linter
ruff check .

# Check shell scripts
shellcheck scripts/*.sh
```

### 2. Type Checking

- mypy for static type checking
- Type hints required for all Python code

```bash
# Run type checker
mypy .
```

### 3. Security Scanning

- Bandit for Python security checks
- Gitleaks for secret detection
- Safety for dependency scanning

```bash
# Run security checks
bandit -r .
gitleaks detect
safety check
```

## Testing

### 1. Testing Framework

- pytest for Python tests
- Shell script tests
- Integration tests

```bash
# Run Python tests
pytest

# Run shell tests
bash scripts/test_detect_k8s.sh

# Run with coverage
pytest --cov=. tests/
```

### 2. Test Guidelines

- No conditionals in tests
- Use parametrized tests
- Maintain test fixtures
- Ensure high coverage

### 3. Test Examples

```python
# Example parametrized test
@pytest.mark.parametrize(
    "config_type,expected",
    [
        ("network", True),
        ("email", True),
        ("domains", True),
        ("sso", True),
    ],
)
def test_config_validation(config_type: str, expected: bool):
    config = load_yaml_config(f"configs/templates/{config_type}.yaml.template")
    schema = load_schema("configs/validation/schema/config.schema.json")
    is_valid, _ = validate_config(config, schema, config_type)
    assert is_valid == expected
```

## Configuration Validation

### 1. Schema Development

- JSON Schema based validation
- Strong typing
- Comprehensive error messages

### 2. Validation Features

- Error aggregation
- Summary reporting
- Progress indicators
- Color-coded output

### 3. Testing Framework

```bash
# Run validation tests
pytest tests/validation/

# Check specific configuration
./configs/validation/validate_config.py --config-type network
```

## Git Workflow

### 1. Branch Strategy

- Feature branches (`feature/*`)
- Fix branches (`fix/*`)
- Documentation branches (`docs/*`)

### 2. Commit Guidelines

- GPG signed commits required
- Conventional commit messages
- Linked issues/tickets

### 3. Pull Requests

- Comprehensive description
- Test coverage
- Documentation updates
- Code review process

## Documentation

### 1. Code Documentation

- Comprehensive docstrings
- Type hints
- Usage examples

### 2. Project Documentation

- Architecture docs
- Configuration guides
- Development guides
- Security guidelines

### 3. Documentation Updates

- Keep docs up to date
- Include examples
- Cross-reference

## Dependencies

### 1. Core Requirements

```toml
# pyproject.toml
[project]
dependencies = [
    "pyyaml>=6.0.1",
    "jsonschema>=4.20.0",
    "rich>=13.7.0",
    "typer>=0.9.0",
]
```

### 2. Development Dependencies

```toml
# pyproject.toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-cov>=4.1.0",
    "black>=23.11.0",
    "mypy>=1.7.1",
    "ruff>=0.1.6",
    "bandit>=1.7.5",
    "safety>=2.3.5",
]
```

### 3. Tool Configuration

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py312']

[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.ruff]
line-length = 88
target-version = 'py312'
select = ['E', 'F', 'B']
```

## References

- [Architecture Documentation](../architecture/index.md)
- [Configuration Guide](../configuration/index.md)
- [Security Guidelines](../security/index.md)
- [Testing Guide](testing.md)
