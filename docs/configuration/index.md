# Configuration Documentation

## Overview

This section details the configuration system for the GitLab Homelab infrastructure. The configuration system is built around YAML templates with JSON Schema validation, providing type safety and comprehensive error checking.

## Configuration Components

### 1. Configuration Templates

#### Network Configuration
```yaml
network:
  cidr_block: "10.0.0.0/16"  # Main network CIDR
  subnets:
    public:
      cidr: "10.0.1.0/24"
      availability_zone: "us-east-1a"
    private:
      cidr: "10.0.2.0/24"
      availability_zone: "us-east-1a"
```

#### Email Configuration
```yaml
smtp:
  host: "smtp.example.com"
  port: 587
  encryption: "tls"
  auth:
    username: "{{ smtp_username }}"
    password: "{{ smtp_password }}"
```

#### Domain Configuration
```yaml
domains:
  primary_domain: "example.com"
  dns:
    provider: "cloudflare"
    ttl: 3600
  ssl:
    provider: "letsencrypt"
    certificates:
      - domain: "example.com"
        key_type: "rsa"
```

#### SSO Configuration
```yaml
sso:
  provider:
    type: "okta"
    name: "Corporate SSO"
  application:
    client_id: "{{ client_id }}"
    client_secret: "{{ client_secret }}"
    redirect_uri: "https://app.example.com/callback"
```

### 2. Validation System

#### Schema Validation
- JSON Schema based validation
- Type checking
- Required field validation
- Pattern matching
- Enumeration validation

#### Error Handling
- Structured error output
- Error aggregation
- Clear error messages
- Context-aware validation

#### Visualization
- Progress indicators
- Color-coded output
- Summary reporting
- JSON report generation

## Configuration Guidelines

### 1. Template Usage

1. Copy the appropriate template:
   ```bash
   cp configs/templates/network.yaml.template configs/network.yaml
   ```

2. Fill in the template values:
   ```yaml
   network:
     cidr_block: "10.0.0.0/16"
     # ... add your values
   ```

3. Validate the configuration:
   ```bash
   ./configs/validation/validate_config.py
   ```

### 2. Security Considerations

1. Secret Management
   - Use environment variables for secrets
   - Never commit secrets to version control
   - Use secret management systems when possible

2. Access Control
   - Restrict configuration access
   - Use version control
   - Implement change tracking

3. Validation Rules
   - Network security rules
   - SSL/TLS requirements
   - Authentication policies

### 3. Best Practices

1. Template Management
   - Keep templates updated
   - Document all variables
   - Include usage examples

2. Validation Process
   - Regular validation checks
   - Automated testing
   - Documentation updates

3. Change Management
   - Version control
   - Change documentation
   - Backup configurations

## Configuration Examples

### 1. Basic Network Setup
```yaml
network:
  cidr_block: "10.0.0.0/16"
  subnets:
    public:
      cidr: "10.0.1.0/24"
      availability_zone: "us-east-1a"
    private:
      cidr: "10.0.2.0/24"
      availability_zone: "us-east-1a"
  vlans:
    app:
      id: 100
      description: "Application Network"
      subnet: "10.0.10.0/24"
```

### 2. Email Configuration
```yaml
smtp:
  host: "smtp.gmail.com"
  port: 587
  encryption: "tls"
  auth:
    username: "{{ smtp_username }}"
    password: "{{ smtp_password }}"
  timeout: 30
  max_retries: 3

notifications:
  default_from: "noreply@example.com"
  alerts:
    enabled: true
    recipients:
      - "admin@example.com"
```

### 3. SSL Configuration
```yaml
ssl:
  provider: "letsencrypt"
  certificates:
    - domain: "example.com"
      sans:
        - "www.example.com"
      key_type: "rsa"
      key_size: 2048
  security:
    min_tls_version: "TLS1.2"
    hsts_enabled: true
    ocsp_stapling: true
```

## Troubleshooting

### 1. Common Issues

#### Schema Validation Errors
```bash
Error at network -> cidr_block: '192.168.1' does not match pattern
Solution: Ensure CIDR block is in correct format (e.g., '192.168.1.0/24')
```

#### Authentication Errors
```bash
Error at sso -> provider -> type: 'auth0' is not one of ['okta', 'azure_ad', 'google']
Solution: Use supported SSO provider from the enumerated list
```

### 2. Validation Process

1. Check syntax:
   ```bash
   yamllint configs/*.yaml
   ```

2. Validate against schema:
   ```bash
   ./configs/validation/validate_config.py
   ```

3. Test configuration:
   ```bash
   ./configs/validation/test_config.py
   ```

## References

- [Architecture Documentation](../architecture/index.md)
- [Security Guidelines](../security/index.md)
- [Infrastructure Setup](../infrastructure/index.md)
- [Installation Guide](../installation/index.md)
