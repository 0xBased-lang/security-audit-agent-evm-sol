"""
Test suite for secret management security.

Tests:
1. SecretStr properly masks secrets
2. Log filtering works
3. API key validation
4. Config integration
"""

import pytest
import os
import logging
from io import StringIO

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.security.secrets import (
    SecretManager,
    APIKeySecret,
    AnthropicAPIKey,
    TenderlyAPIKey,
    LogFilter,
    setup_secret_logging,
    SecretValidationError,
)
from pydantic import SecretStr


class TestAPIKeySecret:
    """Test basic API key secret functionality."""

    def test_secret_is_masked_in_repr(self):
        """Test that secrets are masked in string representation."""
        secret = APIKeySecret(value="my-secret-api-key-123")

        # Should not expose secret in repr
        repr_str = repr(secret)
        assert "my-secret-api-key-123" not in repr_str
        assert "APIKeySecret" in repr_str

    def test_secret_masking(self):
        """Test different masking options."""
        secret = APIKeySecret(value="sk-1234567890abcdef")

        # Prefix only
        masked = secret.get_masked(show_prefix=True, show_suffix=False)
        assert masked == "sk-1..."
        assert "1234567890abcdef" not in masked

        # Suffix only
        masked = secret.get_masked(show_prefix=False, show_suffix=True)
        assert masked == "...cdef"
        assert "sk-1234567890ab" not in masked

        # Both
        masked = secret.get_masked(show_prefix=True, show_suffix=True)
        assert masked == "sk-1...cdef"

        # Neither
        masked = secret.get_masked(show_prefix=False, show_suffix=False)
        assert masked == "***"

    def test_get_secret_value(self):
        """Test that secret value can be retrieved when needed."""
        secret_value = "my-secret-123"
        secret = APIKeySecret(value=secret_value)

        # Can get actual value
        assert secret.value.get_secret_value() == secret_value

    def test_empty_secret_rejected(self):
        """Test that empty secrets are rejected."""
        with pytest.raises(ValueError):
            APIKeySecret(value="")

    def test_secret_format_validation(self):
        """Test pattern-based format validation."""
        secret = APIKeySecret(value="sk-test-123")

        # Valid pattern
        assert secret.validate_format(r'^sk-.*') is True

        # Invalid pattern
        with pytest.raises(SecretValidationError):
            secret.validate_format(r'^api-.*')


class TestAnthropicAPIKey:
    """Test Anthropic-specific API key validation."""

    def test_valid_anthropic_key(self):
        """Test that valid Anthropic keys are accepted."""
        valid_key = "sk-ant-" + "x" * 40
        key = AnthropicAPIKey(value=valid_key)
        assert key.value.get_secret_value() == valid_key

    def test_invalid_prefix_rejected(self):
        """Test that keys without sk-ant- prefix are rejected."""
        with pytest.raises(SecretValidationError):
            AnthropicAPIKey(value="sk-wrong-prefix" + "x" * 40)

    def test_too_short_rejected(self):
        """Test that short keys are rejected."""
        with pytest.raises(SecretValidationError):
            AnthropicAPIKey(value="sk-ant-tooshort")


class TestTenderlyAPIKey:
    """Test Tenderly-specific API key validation."""

    def test_valid_tenderly_key(self):
        """Test that valid Tenderly keys are accepted."""
        valid_key = "a" * 32
        key = TenderlyAPIKey(value=valid_key)
        assert key.value.get_secret_value() == valid_key

    def test_too_short_rejected(self):
        """Test that short keys are rejected."""
        with pytest.raises(SecretValidationError):
            TenderlyAPIKey(value="tooshort")

    def test_invalid_characters_rejected(self):
        """Test that keys with invalid characters are rejected."""
        with pytest.raises(SecretValidationError):
            TenderlyAPIKey(value="a" * 32 + "!@#$%")


class TestSecretManager:
    """Test SecretManager functionality."""

    def test_load_anthropic_key_success(self, monkeypatch):
        """Test loading Anthropic key from environment."""
        test_key = "sk-ant-" + "x" * 40
        monkeypatch.setenv("ANTHROPIC_API_KEY", test_key)

        manager = SecretManager()
        key = manager.load_anthropic_key(required=False)

        assert key is not None
        assert key.value.get_secret_value() == test_key

    def test_load_anthropic_key_missing_not_required(self, monkeypatch):
        """Test that missing non-required key returns None."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        manager = SecretManager()
        key = manager.load_anthropic_key(required=False)

        assert key is None

    def test_load_anthropic_key_missing_required(self, monkeypatch):
        """Test that missing required key raises error."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        manager = SecretManager()
        with pytest.raises(SecretValidationError):
            manager.load_anthropic_key(required=True)

    def test_load_tenderly_key_from_either_env(self, monkeypatch):
        """Test loading Tenderly key from either env variable."""
        test_key = "x" * 32

        # Test TENDERLY_API_KEY
        monkeypatch.setenv("TENDERLY_API_KEY", test_key)
        monkeypatch.delenv("TENDERLY_ACCESS_KEY", raising=False)

        manager = SecretManager()
        key = manager.load_tenderly_key()

        assert key is not None
        assert key.value.get_secret_value() == test_key

        # Test TENDERLY_ACCESS_KEY
        monkeypatch.delenv("TENDERLY_API_KEY", raising=False)
        monkeypatch.setenv("TENDERLY_ACCESS_KEY", test_key)

        manager2 = SecretManager()
        key2 = manager2.load_tenderly_key()

        assert key2 is not None
        assert key2.value.get_secret_value() == test_key

    def test_load_custom_secret(self, monkeypatch):
        """Test loading custom secrets."""
        test_key = "custom-secret-123"
        monkeypatch.setenv("MY_CUSTOM_KEY", test_key)

        manager = SecretManager()
        secret = manager.load_custom_secret(
            env_var="MY_CUSTOM_KEY",
            name="CustomKey",
            required=True
        )

        assert secret is not None
        assert secret.value.get_secret_value() == test_key
        assert secret.name == "CustomKey"

    def test_get_secret(self, monkeypatch):
        """Test retrieving loaded secrets."""
        test_key = "sk-ant-" + "x" * 40
        monkeypatch.setenv("ANTHROPIC_API_KEY", test_key)

        manager = SecretManager()
        manager.load_anthropic_key()

        # Should be able to retrieve
        secret = manager.get_secret("anthropic")
        assert secret is not None
        assert secret.value.get_secret_value() == test_key

    def test_to_dict_masked(self, monkeypatch):
        """Test exporting secrets with masking."""
        test_key = "sk-ant-" + "x" * 40
        monkeypatch.setenv("ANTHROPIC_API_KEY", test_key)

        manager = SecretManager()
        manager.load_anthropic_key()

        # Export with masking
        secrets_dict = manager.to_dict(mask_secrets=True)

        assert "anthropic" in secrets_dict
        assert test_key not in str(secrets_dict)
        assert "***" in secrets_dict["anthropic"] or "..." in secrets_dict["anthropic"]

    def test_to_dict_unmasked(self, monkeypatch):
        """Test exporting secrets without masking."""
        test_key = "sk-ant-" + "x" * 40
        monkeypatch.setenv("ANTHROPIC_API_KEY", test_key)

        manager = SecretManager()
        manager.load_anthropic_key()

        # Export without masking
        secrets_dict = manager.to_dict(mask_secrets=False)

        assert "anthropic" in secrets_dict
        assert secrets_dict["anthropic"] == test_key


class TestLogFilter:
    """Test log filtering for secrets."""

    def test_api_key_masking(self):
        """Test that API keys are masked in logs."""
        # Setup logger with filter
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.INFO)

        # Add filter
        log_filter = LogFilter()
        logger.addFilter(log_filter)

        # Capture log output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)

        # Log message with API key
        logger.info("Using API key: sk-ant-1234567890abcdef")

        # Check that key is masked
        log_output = stream.getvalue()
        assert "sk-ant-1234567890abcdef" not in log_output
        assert "sk-ant-" in log_output  # Prefix should remain

    def test_token_masking(self):
        """Test that tokens are masked."""
        logger = logging.getLogger("test_token_logger")
        logger.setLevel(logging.INFO)
        logger.addFilter(LogFilter())

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)

        logger.info("Authorization: token=secret123")

        log_output = stream.getvalue()
        assert "secret123" not in log_output
        assert "***" in log_output

    def test_password_masking(self):
        """Test that passwords are masked."""
        logger = logging.getLogger("test_password_logger")
        logger.setLevel(logging.INFO)
        logger.addFilter(LogFilter())

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)

        logger.info("Login with password: mypassword123")

        log_output = stream.getvalue()
        assert "mypassword123" not in log_output
        assert "***" in log_output

    def test_bearer_token_masking(self):
        """Test that Bearer tokens are masked."""
        logger = logging.getLogger("test_bearer_logger")
        logger.setLevel(logging.INFO)
        logger.addFilter(LogFilter())

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)

        logger.info("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")

        log_output = stream.getvalue()
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in log_output
        assert "Bearer" in log_output


class TestConfigIntegration:
    """Test integration with AuditConfig."""

    def test_config_loads_secrets_securely(self, monkeypatch):
        """Test that AuditConfig loads secrets using SecretManager."""
        from src.config import AuditConfig

        test_key = "sk-ant-" + "x" * 40
        monkeypatch.setenv("ANTHROPIC_API_KEY", test_key)

        config = AuditConfig()

        # Should have loaded key
        assert config.anthropic_api_key is not None

        # Should be masked in repr/str
        config_str = str(config)
        assert test_key not in config_str

    def test_config_to_dict_masks_secrets(self, monkeypatch):
        """Test that config.to_dict() masks secrets."""
        from src.config import AuditConfig

        test_key = "sk-ant-" + "x" * 40
        monkeypatch.setenv("ANTHROPIC_API_KEY", test_key)

        config = AuditConfig()
        config_dict = config.to_dict(mask_secrets=True)

        # Should be masked
        if "anthropic_api_key" in config_dict:
            assert test_key not in str(config_dict["anthropic_api_key"])

    def test_config_get_key_methods(self, monkeypatch):
        """Test helper methods to get actual key values."""
        from src.config import AuditConfig

        test_key = "sk-ant-" + "x" * 40
        monkeypatch.setenv("ANTHROPIC_API_KEY", test_key)

        config = AuditConfig()

        # Should be able to get actual value when needed
        actual_key = config.get_anthropic_key()
        assert actual_key == test_key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
