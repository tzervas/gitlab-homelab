#!/usr/bin/env python3

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import jsonschema
import yaml

from validation_result import ConfigType, ValidationResult, ValidationStatus


class ConfigSchemaValidator:
    """Validator for configuration schemas.
    
    This class wraps jsonschema's Draft7Validator to provide a more domain-specific
    interface for validating configuration files against their schemas.
    """
    
    def __init__(self, schema_definition: Dict) -> None:
        """Initialize the validator with a schema definition.
        
        Args:
            schema_definition: The JSON schema definition to validate against
        
        Raises:
            jsonschema.exceptions.SchemaError: If the schema is invalid
        """
        self.validator = jsonschema.Draft7Validator(schema_definition)
    
    def validate(self, config: Dict) -> List[jsonschema.exceptions.ValidationError]:
        """Validate a configuration against the schema.
        
        Args:
            config: The configuration dictionary to validate
            
        Returns:
            List of validation errors sorted by their path in the document
        """
        return sorted(self.validator.iter_errors(config), key=lambda e: e.path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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
    except FileNotFoundError:
        logging.error(f"Schema file not found: {schema_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format in schema file {schema_path}: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error loading schema from {schema_path}: {e}")
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
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Invalid YAML format in configuration file {config_path}: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error loading configuration from {config_path}: {e}")
        sys.exit(1)

def validate_config(config: Dict, schema: Dict, config_type: str, config_path: str) -> ValidationResult:
    """Validate a configuration against its schema.
    
    Args:
        config: Configuration dictionary to validate
        schema: JSON schema to validate against
        config_type: Type of configuration being validated
        config_path: Path to the configuration file
        
    Returns:
        ValidationResult object containing validation status and messages
    """
    result = ValidationResult(
        config_type=ConfigType(config_type),
        config_path=config_path
    )
    
    try:
        schema_definition = schema['definitions'][config_type]
        validator = ConfigSchemaValidator(schema_definition)
        errors = validator.validate(config)
    
    for error in errors:
        path = ' -> '.join(str(p) for p in error.path)
        message = f"Error at {path}: {error.message}"
        result.add_error(message)
    
    if not errors:
        result.mark_as_valid()
    
    return result

def check_security_requirements(config: Dict, result: ValidationResult) -> None:
    """Check security-specific requirements for configurations.
    
    Args:
        config: Configuration dictionary to check
        result: ValidationResult object to add warnings to
    """
    config_type = result.config_type.value
    
    if config_type == 'network':
        # Check for open CIDR blocks
        if any('0.0.0.0/0' in str(v) for v in config.values()):
            result.add_security_warning("Found overly permissive CIDR block (0.0.0.0/0)")
            
    elif config_type == 'email':
        # Check for secure SMTP settings
        smtp = config.get('smtp', {})
        if smtp.get('encryption') == 'none':
            result.add_security_warning("SMTP is configured without encryption")
            
    elif config_type == 'domains':
        # Check SSL/TLS settings
        ssl = config.get('ssl', {})
        if not ssl.get('hsts_enabled'):
            result.add_security_warning("HSTS is not enabled")
        if not ssl.get('ocsp_stapling'):
            result.add_security_warning("OCSP stapling is not enabled")
            
    elif config_type == 'sso':
        # Check SSO security settings
        auth = config.get('authentication', {})
        if not auth.get('mfa', {}).get('enabled'):
            result.add_security_warning("MFA is not enabled for SSO")
        session = auth.get('session', {})
        if session.get('lifetime', 0) > 86400:  # 24 hours
            result.add_security_warning("Session lifetime exceeds 24 hours")

def generate_summary(validation_results: List[ValidationResult]) -> None:
    """Generate a structured summary of validation results.
    
    Aggregates validation results to show:
    - Total configurations checked
    - Count of invalid configurations
    - Errors grouped by configuration type
    - Security warnings summary
    
    Args:
        validation_results: List of ValidationResult objects to summarize
    """
    total_configs = len(validation_results)
    invalid_configs = sum(1 for r in validation_results if not r.is_valid())
    
    # Group errors by config type
    errors_by_type = {}
    total_warnings = 0
    
    for result in validation_results:
        config_type = result.config_type.value
        if result.errors:
            errors_by_type[config_type] = result.errors
        total_warnings += len(result.security_warnings)
    
    # Log summary using structured format
    logging.info("\nValidation Summary Report")
    logging.info("=======================")
    logging.info(f"Total Configurations Checked: {total_configs}")
    logging.info(f"Invalid Configurations: {invalid_configs}")
    logging.info(f"Total Security Warnings: {total_warnings}\n")
    
    if errors_by_type:
        logging.info("Errors by Configuration Type:")
        logging.info("----------------------------")
        for config_type, errors in errors_by_type.items():
            logging.info(f"\n{config_type.upper()} Errors:")
            for error in errors:
                logging.info(f"  - {error}")
    
    if total_warnings > 0:
        logging.info("\nSecurity Warnings Summary:")
        logging.info("------------------------")
        for result in validation_results:
            if result.security_warnings:
                logging.info(f"\n{result.config_type.value.upper()}:")
                for warning in result.security_warnings:
                    logging.info(f"  - {warning}")


def main():
    """Main validation function."""
    # Set up paths
    config_dir = Path(__file__).parent.parent
    schema_path = config_dir / 'validation' / 'schema' / 'config.schema.json'
    
    # Load schema
    schema = load_schema(str(schema_path))
    
    # Configuration types to validate
    config_types = ['network', 'email', 'domains', 'sso']

    # Initialize results collection
    validation_results: List[ValidationResult] = []

    # Process each config type
    for config_type in config_types:
        logging.info(f"Validating {config_type} configuration...")

        config_path = config_dir / 'templates' / f'{config_type}.yaml.template'
        if not config_path.exists():
            logging.warning(f"Configuration file not found: {config_path}")
            continue
            
        # Load and validate configuration
        config = load_yaml_config(str(config_path))
        result = validate_config(config, schema, config_type, str(config_path))
        validation_results.append(result)
        
        # Check security requirements
        check_security_requirements(config, result)
        
        # Log validation results
        if not result.is_valid():
            logging.error("Validation errors found:")
            for error in result.errors:
                logging.error(f"  {error}")
        else:
            logging.info("Configuration validation successful")
            
        if result.security_warnings:
            logging.warning("Security issues detected:")
            for warning in result.security_warnings:
                logging.warning(f"  {warning}")
    
    # Generate detailed validation summary before exit
    generate_summary(validation_results)

    # Exit the program
    sys.exit(0 if all(result.is_valid() for result in validation_results) else 1)

if __name__ == '__main__':
    main()
