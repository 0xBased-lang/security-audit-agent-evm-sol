"""
Secret Management Module

Provides secure handling of sensitive information:
- API keys masking in logs
- Environment variable validation
- Secret format validation
- Secure secret storage using Pydantic SecretStr

Security Model:
- Secrets are never logged or printed
- Validation at initialization
- Clear error messages without exposing secrets
- Type-safe secret handling
"""

import os
import re
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, SecretStr, field_validator


class SecretValidationError(Exception):
    """Raised when secret validation fails."""
    pass


class APIKeySecret(BaseModel):
    """
    Secure API key storage using Pydantic SecretStr.

    Features:
    - Automatic masking in logs and repr
    - Validation of API key format
    - Prevents accidental exposure

    Example:
        key = APIKeySecret(value="sk-1234567890abcdef")
        print(key)  # APIKeySecret(value='**********')
        print(key.value.get_secret_value())  # sk-1234567890abcdef
    """

    value: SecretStr
    name: str = Field(default="API_KEY")

    @field_validator('value')
    @classmethod
    def validate_not_empty(cls, v: SecretStr) -> SecretStr:
        """Validate secret is not empty."""
        if not v.get_secret_value():
            raise ValueError("API key cannot be empty")
        return v

    def get_masked(self, show_prefix: bool = True, show_suffix: bool = False) -> str:
        """
        Get masked version of secret for logging.

        Args:
            show_prefix: Show first 4 characters
            show_suffix: Show last 4 characters

        Returns:
            Masked secret string
        """
        secret = self.value.get_secret_value()
        if len(secret) < 8:
            return "***"

        if show_prefix and show_suffix:
            return f"{secret[:4]}...{secret[-4:]}"
        elif show_prefix:
            return f"{secret[:4]}..."
        elif show_suffix:
            return f"...{secret[-4:]}"
        else:
            return "***"

    def validate_format(self, pattern: Optional[str] = None) -> bool:
        """
        Validate secret matches expected format.

        Args:
            pattern: Regex pattern to match (None skips validation)

        Returns:
            True if valid

        Raises:
            SecretValidationError: If validation fails
        """
        if not pattern:
            return True

        secret = self.value.get_secret_value()
        if not re.match(pattern, secret):
            raise SecretValidationError(
                f"{self.name} does not match expected format"
            )
        return True


class AnthropicAPIKey(APIKeySecret):
    """Anthropic API key with format validation."""

    name: str = Field(default="ANTHROPIC_API_KEY")

    @field_validator('value')
    @classmethod
    def validate_anthropic_format(cls, v: SecretStr) -> SecretStr:
        """Validate Anthropic API key format."""
        secret = v.get_secret_value()

        # Anthropic keys typically start with 'sk-ant-'
        if not secret.startswith('sk-ant-'):
            raise SecretValidationError(
                "Anthropic API key should start with 'sk-ant-'"
            )

        # Should be at least 40 characters
        if len(secret) < 40:
            raise SecretValidationError(
                "Anthropic API key too short"
            )

        return v


class TenderlyAPIKey(APIKeySecret):
    """Tenderly API key with format validation."""

    name: str = Field(default="TENDERLY_API_KEY")

    @field_validator('value')
    @classmethod
    def validate_tenderly_format(cls, v: SecretStr) -> SecretStr:
        """Validate Tenderly API key format."""
        secret = v.get_secret_value()

        # Tenderly keys are typically 32+ alphanumeric characters
        if len(secret) < 32:
            raise SecretValidationError(
                "Tenderly API key too short"
            )

        if not re.match(r'^[a-zA-Z0-9_-]+$', secret):
            raise SecretValidationError(
                "Tenderly API key contains invalid characters"
            )

        return v


class SecretManager:
    """
    Centralized secret management.

    Features:
    - Load secrets from environment
    - Validate secret formats
    - Mask secrets in logs
    - Provide clear error messages

    Example:
        manager = SecretManager()
        manager.load_anthropic_key(required=True)
        manager.load_tenderly_key(required=False)

        # Get masked version for logging
        logger.info(f"Using API key: {manager.anthropic_key.get_masked()}")
    """

    def __init__(self):
        """Initialize secret manager."""
        self.anthropic_key: Optional[AnthropicAPIKey] = None
        self.tenderly_key: Optional[TenderlyAPIKey] = None
        self._secrets: Dict[str, APIKeySecret] = {}
        self.logger = logging.getLogger(__name__)

    def load_anthropic_key(self, required: bool = False) -> Optional[AnthropicAPIKey]:
        """
        Load Anthropic API key from environment.

        Args:
            required: If True, raise error if not found

        Returns:
            AnthropicAPIKey if found, None otherwise

        Raises:
            SecretValidationError: If required but not found or invalid
        """
        env_value = os.environ.get('ANTHROPIC_API_KEY')

        if not env_value:
            if required:
                raise SecretValidationError(
                    "ANTHROPIC_API_KEY not found in environment. "
                    "Set it with: export ANTHROPIC_API_KEY='sk-ant-...'"
                )
            return None

        try:
            self.anthropic_key = AnthropicAPIKey(value=env_value)
            self._secrets['anthropic'] = self.anthropic_key
            self.logger.info(
                f"Loaded Anthropic API key: {self.anthropic_key.get_masked()}"
            )
            return self.anthropic_key

        except Exception as e:
            if required:
                raise SecretValidationError(
                    f"Invalid ANTHROPIC_API_KEY: {e}"
                )
            self.logger.warning(f"Failed to load Anthropic API key: {e}")
            return None

    def load_tenderly_key(self, required: bool = False) -> Optional[TenderlyAPIKey]:
        """
        Load Tenderly API key from environment.

        Args:
            required: If True, raise error if not found

        Returns:
            TenderlyAPIKey if found, None otherwise

        Raises:
            SecretValidationError: If required but not found or invalid
        """
        # Try both TENDERLY_API_KEY and TENDERLY_ACCESS_KEY
        env_value = (
            os.environ.get('TENDERLY_API_KEY') or
            os.environ.get('TENDERLY_ACCESS_KEY')
        )

        if not env_value:
            if required:
                raise SecretValidationError(
                    "TENDERLY_API_KEY or TENDERLY_ACCESS_KEY not found in environment. "
                    "Set it with: export TENDERLY_API_KEY='your-key'"
                )
            return None

        try:
            self.tenderly_key = TenderlyAPIKey(value=env_value)
            self._secrets['tenderly'] = self.tenderly_key
            self.logger.info(
                f"Loaded Tenderly API key: {self.tenderly_key.get_masked()}"
            )
            return self.tenderly_key

        except Exception as e:
            if required:
                raise SecretValidationError(
                    f"Invalid TENDERLY_API_KEY: {e}"
                )
            self.logger.warning(f"Failed to load Tenderly API key: {e}")
            return None

    def load_custom_secret(
        self,
        env_var: str,
        name: str,
        required: bool = False,
        pattern: Optional[str] = None
    ) -> Optional[APIKeySecret]:
        """
        Load a custom secret from environment.

        Args:
            env_var: Environment variable name
            name: Friendly name for the secret
            required: If True, raise error if not found
            pattern: Optional regex pattern for validation

        Returns:
            APIKeySecret if found, None otherwise

        Raises:
            SecretValidationError: If required but not found or invalid
        """
        env_value = os.environ.get(env_var)

        if not env_value:
            if required:
                raise SecretValidationError(
                    f"{env_var} not found in environment"
                )
            return None

        try:
            secret = APIKeySecret(value=env_value, name=name)

            # Validate pattern if provided
            if pattern:
                secret.validate_format(pattern)

            self._secrets[name.lower()] = secret
            self.logger.info(f"Loaded {name}: {secret.get_masked()}")
            return secret

        except Exception as e:
            if required:
                raise SecretValidationError(
                    f"Invalid {env_var}: {e}"
                )
            self.logger.warning(f"Failed to load {name}: {e}")
            return None

    def get_secret(self, name: str) -> Optional[APIKeySecret]:
        """
        Get a loaded secret by name.

        Args:
            name: Secret name (lowercase)

        Returns:
            APIKeySecret if found, None otherwise
        """
        return self._secrets.get(name.lower())

    def to_dict(self, mask_secrets: bool = True) -> Dict[str, Any]:
        """
        Export secrets to dictionary.

        Args:
            mask_secrets: If True, mask secret values

        Returns:
            Dictionary of secrets
        """
        result = {}
        for name, secret in self._secrets.items():
            if mask_secrets:
                result[name] = secret.get_masked()
            else:
                result[name] = secret.value.get_secret_value()
        return result


class LogFilter(logging.Filter):
    """
    Logging filter to mask secrets in log messages.

    Automatically masks:
    - API keys (sk-*, api_key=...)
    - Tokens (token=...)
    - Passwords (password=...)
    - Bearer tokens (Bearer ...)

    Example:
        import logging

        logger = logging.getLogger()
        logger.addFilter(LogFilter())

        logger.info("API key: sk-ant-1234567890")
        # Logs: "API key: sk-ant-****"
    """

    # Patterns to mask
    PATTERNS = [
        # API keys starting with sk- (show first 7 chars only: "sk-ant-")
        (re.compile(r'sk-([a-zA-Z0-9-]{4,})'), lambda m: f"sk-{m.group(1)[:4]}***"),

        # Generic API key patterns (key=value)
        (re.compile(r'(api[_-]?key[=:]\s*)([^\s,;]+)', re.IGNORECASE), r'\1***'),

        # Token patterns
        (re.compile(r'(token[=:]\s*)([^\s,;]+)', re.IGNORECASE), r'\1***'),

        # Password patterns
        (re.compile(r'(password[=:]\s*)([^\s,;]+)', re.IGNORECASE), r'\1***'),

        # Bearer tokens
        (re.compile(r'(Bearer\s+)([^\s,;]+)', re.IGNORECASE), r'\1***'),

        # Generic secrets
        (re.compile(r'(secret[=:]\s*)([^\s,;]+)', re.IGNORECASE), r'\1***'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to mask secrets.

        Args:
            record: Log record to filter

        Returns:
            Always True (don't filter out the record)
        """
        # Mask secrets in message
        message = record.getMessage()
        for pattern, replacement in self.PATTERNS:
            message = pattern.sub(replacement, message)

        # Update the record
        record.msg = message
        record.args = ()

        return True


def setup_secret_logging():
    """
    Setup secret-safe logging for the entire application.

    Call this early in your application initialization:

    Example:
        from src.security.secrets import setup_secret_logging

        setup_secret_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting application...")
    """
    # Add filter to root logger
    root_logger = logging.getLogger()
    root_logger.addFilter(LogFilter())

    # Also add to any existing handlers
    for handler in root_logger.handlers:
        handler.addFilter(LogFilter())


# Export public API
__all__ = [
    'APIKeySecret',
    'AnthropicAPIKey',
    'TenderlyAPIKey',
    'SecretManager',
    'SecretValidationError',
    'LogFilter',
    'setup_secret_logging',
]
