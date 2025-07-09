from enum import Enum
from typing import List


class ConfigType(Enum):
    """Enumeration of supported configuration types."""
    NETWORK = "network"
    EMAIL = "email" 
    DOMAINS = "domains"
    SSO = "sso"


class ValidationStatus(Enum):
    """Enumeration of possible validation statuses."""
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"


class ValidationResult:
    """Tracks the validation outcomes for configuration validation.
    
    Attributes:
        config_type: The type of configuration being validated
        status: Current validation status
        errors: List of validation error messages
        security_warnings: List of security-related warnings
        config_path: Path to the configuration being validated
    """

    def __init__(
        self,
        config_type: ConfigType,
        config_path: str,
        status: ValidationStatus = ValidationStatus.PENDING,
        errors: List[str] | None = None,
        security_warnings: List[str] | None = None
    ) -> None:
        """Initialize a new ValidationResult instance.
        
        Args:
            config_type: Type of configuration being validated
            config_path: Path to the configuration being validated
            status: Current validation status (defaults to PENDING)
            errors: List of validation error messages (defaults to empty list)
            security_warnings: List of security warnings (defaults to empty list)
        """
        self.config_type = config_type
        self.status = status
        self.errors = errors or []
        self.security_warnings = security_warnings or []
        self.config_path = config_path

    def add_error(self, error: str) -> None:
        """Add a validation error message.
        
        Args:
            error: The error message to add
        """
        self.errors.append(error)
        self.status = ValidationStatus.INVALID

    def add_security_warning(self, warning: str) -> None:
        """Add a security warning message.
        
        Args:
            warning: The security warning message to add
        """
        self.security_warnings.append(warning)

    def is_valid(self) -> bool:
        """Check if the validation status is valid.
        
        Returns:
            bool: True if status is VALID, False otherwise
        """
        return self.status == ValidationStatus.VALID

    def mark_as_valid(self) -> None:
        """Mark the validation status as valid."""
        self.status = ValidationStatus.VALID

    def __str__(self) -> str:
        """Return a string representation of the validation result.
        
        Returns:
            str: A formatted string showing validation details
        """
        return (
            f"ValidationResult(type={self.config_type.value}, "
            f"status={self.status.value}, "
            f"errors={len(self.errors)}, "
            f"warnings={len(self.security_warnings)}, "
            f"path='{self.config_path}')"
        )
