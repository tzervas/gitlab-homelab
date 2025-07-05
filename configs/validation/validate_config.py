#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import jsonschema
import yaml

def load_schema(schema_path: str) -> Dict:
    """Load and parse the JSON schema file.
    
    Args:
        schema_path: Path to the JSON schema file
        
    Returns:
        Dict containing the parsed schema
    """
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading schema from {schema_path}: {e}")
        sys.exit(1)

def load_yaml_config(config_path: str) -> Dict:
    """Load and parse a YAML configuration file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dict containing the parsed configuration
    """
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {e}")
        sys.exit(1)

def validate_config(config: Dict, schema: Dict, config_type: str) -> Tuple[bool, List[str]]:
    """Validate a configuration against its schema.
    
    Args:
        config: Configuration dictionary to validate
        schema: JSON schema to validate against
        config_type: Type of configuration being validated
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = jsonschema.Draft7Validator(schema['definitions'][config_type])
    errors = sorted(validator.iter_errors(config), key=lambda e: e.path)
    
    error_messages = []
    for error in errors:
        path = ' -> '.join(str(p) for p in error.path)
        message = f"Error at {path}: {error.message}"
        error_messages.append(message)
    
    return len(error_messages) == 0, error_messages

def check_security_requirements(config: Dict, config_type: str) -> List[str]:
    """Check security-specific requirements for configurations.
    
    Args:
        config: Configuration dictionary to check
        config_type: Type of configuration being checked
        
    Returns:
        List of security warnings
    """
    warnings = []
    
    if config_type == 'network':
        # Check for open CIDR blocks
        if any('0.0.0.0/0' in str(v) for v in config.values()):
            warnings.append("WARNING: Found overly permissive CIDR block (0.0.0.0/0)")
            
    elif config_type == 'email':
        # Check for secure SMTP settings
        smtp = config.get('smtp', {})
        if smtp.get('encryption') == 'none':
            warnings.append("WARNING: SMTP is configured without encryption")
            
    elif config_type == 'domains':
        # Check SSL/TLS settings
        ssl = config.get('ssl', {})
        if not ssl.get('hsts_enabled'):
            warnings.append("WARNING: HSTS is not enabled")
        if not ssl.get('ocsp_stapling'):
            warnings.append("WARNING: OCSP stapling is not enabled")
            
    elif config_type == 'sso':
        # Check SSO security settings
        auth = config.get('authentication', {})
        if not auth.get('mfa', {}).get('enabled'):
            warnings.append("WARNING: MFA is not enabled for SSO")
        session = auth.get('session', {})
        if session.get('lifetime', 0) > 86400:  # 24 hours
            warnings.append("WARNING: Session lifetime exceeds 24 hours")
            
    return warnings

def main():
    """Main validation function."""
    # Set up paths
    config_dir = Path(__file__).parent.parent
    schema_path = config_dir / 'validation' / 'schema' / 'config.schema.json'
    
    # Load schema
    schema = load_schema(str(schema_path))
    
    # Configuration types to validate
    config_types = ['network', 'email', 'domains', 'sso']
    
    # Track overall validation status
    all_valid = True
    
    for config_type in config_types:
        print(f"\nValidating {config_type} configuration...")
        
        config_path = config_dir / 'templates' / f'{config_type}.yaml.template'
        if not config_path.exists():
            print(f"WARNING: Configuration file not found: {config_path}")
            continue
            
        # Load and validate configuration
        config = load_yaml_config(str(config_path))
        is_valid, errors = validate_config(config, schema, config_type)
        
        if not is_valid:
            all_valid = False
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("Configuration is valid.")
            
        # Check security requirements
        security_warnings = check_security_requirements(config, config_type)
        if security_warnings:
            print("\nSecurity warnings:")
            for warning in security_warnings:
                print(f"  - {warning}")
    
    sys.exit(0 if all_valid else 1)

if __name__ == '__main__':
    main()
