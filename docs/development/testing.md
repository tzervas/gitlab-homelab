# Testing Guide

## Overview

This guide covers testing practices and requirements for the GitLab Homelab infrastructure project. All code changes must be accompanied by appropriate tests following these guidelines.

## Testing Principles

### 1. Test Structure

- No conditionals in tests
- Use parametrized tests
- Keep tests simple and focused
- One assertion per test
- Clear test naming

### 2. Test Coverage

- Minimum 90% code coverage
- Cover edge cases
- Test error conditions
- Include integration tests

### 3. Test Organization

- Group related tests
- Use fixtures effectively
- Maintain test isolation
- Clear test hierarchy

## Test Types

### 1. Unit Tests

```python
# Example unit test
def test_validate_network_cidr():
    valid_cidrs = [
        "10.0.0.0/16",
        "192.168.1.0/24",
        "172.16.0.0/12",
    ]
    for cidr in valid_cidrs:
        result = validate_cidr(cidr)
        assert result.is_valid
        assert not result.errors

def test_validate_network_cidr_invalid():
    invalid_cidrs = [
        "256.0.0.0/16",  # Invalid IP
        "10.0.0.0/33",   # Invalid mask
        "not-a-cidr",    # Invalid format
    ]
    for cidr in invalid_cidrs:
        result = validate_cidr(cidr)
        assert not result.is_valid
        assert result.errors
```

### 2. Integration Tests

```python
# Example integration test
def test_configuration_validation_flow():
    # Prepare test configuration
    config = {
        "network": {
            "cidr_block": "10.0.0.0/16",
            "subnets": {
                "public": {
                    "cidr": "10.0.1.0/24",
                    "availability_zone": "us-east-1a"
                }
            }
        }
    }
    
    # Run validation
    validator = ConfigValidator(schema_path="schema.json")
    result = validator.validate(config)
    
    # Check results
    assert result.is_valid
    assert result.validated_config == config
    assert not result.errors
```

### 3. Parametrized Tests

```python
@pytest.mark.parametrize("config_file,expected_valid", [
    ("network.yaml", True),
    ("email.yaml", True),
    ("domains.yaml", True),
    ("sso.yaml", True),
])
def test_configuration_files(config_file: str, expected_valid: bool):
    config = load_yaml_config(f"configs/templates/{config_file}")
    validator = ConfigValidator()
    result = validator.validate(config)
    assert result.is_valid == expected_valid
```

## Test Fixtures

### 1. Configuration Fixtures

```python
@pytest.fixture
def valid_network_config():
    return {
        "network": {
            "cidr_block": "10.0.0.0/16",
            "subnets": {
                "public": {
                    "cidr": "10.0.1.0/24",
                    "availability_zone": "us-east-1a"
                },
                "private": {
                    "cidr": "10.0.2.0/24",
                    "availability_zone": "us-east-1a"
                }
            }
        }
    }

@pytest.fixture
def valid_email_config():
    return {
        "smtp": {
            "host": "smtp.example.com",
            "port": 587,
            "encryption": "tls",
            "auth": {
                "username": "test-user",
                "password": "test-password"
            }
        }
    }
```

### 2. Validator Fixtures

```python
@pytest.fixture
def config_validator():
    return ConfigValidator(
        schema_path="configs/validation/schema/config.schema.json"
    )

@pytest.fixture
def mock_file_system(tmp_path):
    # Set up temporary test files
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    
    # Create test files
    (config_dir / "network.yaml").write_text("...")
    (config_dir / "email.yaml").write_text("...")
    
    return config_dir
```

## Test Categories

### 1. Schema Validation Tests

```python
def test_schema_validation():
    # Schema structure tests
    test_schema_required_fields()
    test_schema_field_types()
    test_schema_enums()
    
    # Schema validation tests
    test_schema_network_validation()
    test_schema_email_validation()
    test_schema_domain_validation()
    test_schema_sso_validation()
```

### 2. Configuration Tests

```python
def test_config_loading():
    # File loading tests
    test_load_yaml_config()
    test_load_json_config()
    
    # Config validation tests
    test_validate_network_config()
    test_validate_email_config()
    test_validate_domain_config()
    test_validate_sso_config()
```

### 3. Error Handling Tests

```python
def test_error_handling():
    # Validation error tests
    test_required_field_errors()
    test_type_validation_errors()
    test_pattern_validation_errors()
    
    # Error aggregation tests
    test_error_collection()
    test_error_formatting()
    test_error_reporting()
```

## Running Tests

### 1. Basic Test Execution

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config_validation.py

# Run specific test
pytest tests/test_config_validation.py::test_validate_network_config
```

### 2. Coverage Testing

```bash
# Run tests with coverage
pytest --cov=.

# Generate coverage report
pytest --cov=. --cov-report=html

# Check coverage thresholds
pytest --cov=. --cov-fail-under=90
```

### 3. Test Organization

```
tests/
├── unit/
│   ├── test_config_validation.py
│   ├── test_error_handling.py
│   └── test_schema_validation.py
├── integration/
│   ├── test_config_flow.py
│   └── test_validation_system.py
└── conftest.py
```

## Best Practices

### 1. Test Writing

- Write tests before code (TDD)
- Keep tests simple and focused
- Use clear, descriptive names
- Document test requirements

### 2. Test Maintenance

- Update tests with code changes
- Remove obsolete tests
- Keep test data current
- Regular test review

### 3. Test Quality

- Follow style guidelines
- Maintain test independence
- Avoid test duplication
- Regular refactoring

## References

- [Development Guide](index.md)
- [Configuration Guide](../configuration/index.md)
- [pytest Documentation](https://docs.pytest.org/)
- [Test Coverage Tools](https://coverage.readthedocs.io/)
