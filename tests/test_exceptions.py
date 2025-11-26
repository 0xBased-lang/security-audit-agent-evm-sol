"""
Test suite for custom exception hierarchy.

Tests:
1. Exception creation and attributes
2. Error severity classification
3. Retryable exception detection
4. Context preservation
"""

import pytest
from src.exceptions import *


class TestBaseException:
    """Test SecurityAuditException base class."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = SecurityAuditException("Test error")
        assert str(exc) == "[MEDIUM] Test error"
        assert exc.severity == ErrorSeverity.MEDIUM
        assert exc.retryable is False

    def test_exception_with_severity(self):
        """Test exception with custom severity."""
        exc = SecurityAuditException(
            "Critical error",
            severity=ErrorSeverity.CRITICAL
        )
        assert exc.severity == ErrorSeverity.CRITICAL
        assert "[CRITICAL]" in str(exc)

    def test_exception_with_context(self):
        """Test exception with context."""
        exc = SecurityAuditException(
            "Error with context",
            context={'file': 'test.sol', 'line': 42}
        )
        exc_str = str(exc)
        assert "file=test.sol" in exc_str
        assert "line=42" in exc_str

    def test_retryable_exception(self):
        """Test retryable exception."""
        exc = SecurityAuditException(
            "Retry this",
            retryable=True
        )
        assert exc.retryable is True
        assert "[RETRYABLE]" in str(exc)


class TestConfigurationErrors:
    """Test configuration-related exceptions."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        exc = ConfigurationError(
            "Invalid config",
            config_key='api_timeout'
        )
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.retryable is False
        assert "config_key=api_timeout" in str(exc)

    def test_api_key_error(self):
        """Test APIKeyError."""
        exc = APIKeyError(
            "API key missing",
            api_name='Anthropic'
        )
        assert exc.severity == ErrorSeverity.HIGH
        assert "api=Anthropic" in str(exc)
        assert "config_key=api_key" in str(exc)


class TestNetworkErrors:
    """Test network-related exceptions."""

    def test_network_error_retryable(self):
        """Test NetworkError is retryable by default."""
        exc = NetworkError("Connection failed")
        assert exc.retryable is True
        assert exc.severity == ErrorSeverity.MEDIUM

    def test_rpc_error(self):
        """Test RPCError with RPC details."""
        exc = RPCError(
            "RPC call failed",
            rpc_url="https://mainnet.infura.io",
            chain_id=1
        )
        assert exc.retryable is True
        assert "rpc_url=" in str(exc)
        assert "chain_id=1" in str(exc)

    def test_tenderly_error(self):
        """Test TenderlyError."""
        exc = TenderlyError(
            "API rate limit",
            api_endpoint='/api/v1/simulate',
            status_code=429
        )
        assert exc.retryable is True
        assert "endpoint=/api/v1/simulate" in str(exc)
        assert "status_code=429" in str(exc)

    def test_timeout_error(self):
        """Test TimeoutError."""
        exc = TimeoutError(
            "Request timed out",
            timeout_seconds=30.0
        )
        assert exc.retryable is True
        assert "timeout=30.0" in str(exc)


class TestValidationErrors:
    """Test validation-related exceptions."""

    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError(
            "Invalid input",
            field='username',
            value='bad@user'
        )
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.retryable is False
        assert "field=username" in str(exc)
        assert "value_type=str" in str(exc)

    def test_path_traversal_error(self):
        """Test PathTraversalError."""
        exc = PathTraversalError(
            "Path traversal detected",
            path='../../etc/passwd'
        )
        assert exc.severity == ErrorSeverity.CRITICAL
        assert exc.retryable is False
        assert "path=" in str(exc)

    def test_command_injection_error(self):
        """Test CommandInjectionError."""
        exc = CommandInjectionError(
            "Command injection detected",
            command='rm -rf / && echo hacked'
        )
        assert exc.severity == ErrorSeverity.CRITICAL
        assert exc.retryable is False
        assert "command_length=" in str(exc)


class TestContractErrors:
    """Test smart contract related exceptions."""

    def test_contract_error(self):
        """Test ContractError."""
        exc = ContractError("Contract error")
        assert exc.severity == ErrorSeverity.HIGH

    def test_compilation_error(self):
        """Test CompilationError."""
        exc = CompilationError(
            "Compilation failed",
            contract_path='contracts/Token.sol',
            compiler_output='Error: Undeclared identifier'
        )
        assert exc.retryable is False
        assert "contract=contracts/Token.sol" in str(exc)
        assert "compiler_error=" in str(exc)

    def test_simulation_error(self):
        """Test SimulationError."""
        exc = SimulationError(
            "Simulation reverted",
            tx_hash='0xabc123',
            revert_reason='insufficient balance'
        )
        assert exc.retryable is False
        assert "tx_hash=0xabc123" in str(exc)
        assert "revert=insufficient balance" in str(exc)

    def test_invariant_violation(self):
        """Test InvariantViolation."""
        exc = InvariantViolation(
            "Invariant violated",
            invariant_name='total_supply_equals_balances',
            expected=1000,
            actual=999
        )
        assert exc.severity == ErrorSeverity.CRITICAL
        assert exc.retryable is False
        assert "invariant=total_supply_equals_balances" in str(exc)
        assert "expected=1000" in str(exc)
        assert "actual=999" in str(exc)


class TestToolErrors:
    """Test external tool integration errors."""

    def test_tool_error(self):
        """Test ToolError."""
        exc = ToolError("Tool failed", tool_name='slither')
        assert exc.retryable is True
        assert "tool=slither" in str(exc)

    def test_slither_error(self):
        """Test SlitherError."""
        exc = SlitherError("Analysis failed")
        assert "tool=slither" in str(exc)

    def test_mythril_error(self):
        """Test MythrilError."""
        exc = MythrilError("Analysis timeout")
        assert "tool=mythril" in str(exc)

    def test_echidna_error(self):
        """Test EchidnaError."""
        exc = EchidnaError("Fuzzing failed")
        assert "tool=echidna" in str(exc)


class TestAIErrors:
    """Test AI/LLM related errors."""

    def test_ai_error(self):
        """Test AIError."""
        exc = AIError("LLM request failed")
        assert exc.retryable is True
        assert exc.severity == ErrorSeverity.MEDIUM

    def test_llm_rate_limit(self):
        """Test LLMRateLimitError."""
        exc = LLMRateLimitError(
            "Rate limit hit",
            retry_after=60
        )
        assert exc.retryable is True
        assert exc.severity == ErrorSeverity.LOW
        assert "retry_after_seconds=60" in str(exc)

    def test_llm_token_limit(self):
        """Test LLMTokenLimitError."""
        exc = LLMTokenLimitError(
            "Token limit exceeded",
            token_count=150000,
            max_tokens=100000
        )
        assert exc.retryable is False
        assert "token_count=150000" in str(exc)
        assert "max_tokens=100000" in str(exc)


class TestResourceErrors:
    """Test resource-related errors."""

    def test_file_not_found(self):
        """Test FileNotFoundError."""
        exc = FileNotFoundError(
            "File missing",
            file_path='/path/to/missing.sol'
        )
        assert exc.retryable is False
        assert "path=/path/to/missing.sol" in str(exc)

    def test_permission_error(self):
        """Test PermissionError."""
        exc = PermissionError(
            "Access denied",
            resource='/secure/file.txt',
            required_permission='read'
        )
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.retryable is False
        assert "resource=/secure/file.txt" in str(exc)
        assert "required=read" in str(exc)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_is_retryable_custom_exception(self):
        """Test is_retryable with custom exception."""
        retryable_exc = NetworkError("Network down")
        non_retryable_exc = ValidationError("Bad input")

        assert is_retryable(retryable_exc) is True
        assert is_retryable(non_retryable_exc) is False

    def test_is_retryable_builtin_exception(self):
        """Test is_retryable with built-in exceptions."""
        connection_error = ConnectionError("Connection lost")
        value_error = ValueError("Invalid value")

        assert is_retryable(connection_error) is True
        assert is_retryable(value_error) is False

    def test_get_severity_custom_exception(self):
        """Test get_severity with custom exception."""
        critical_exc = PathTraversalError("Attack detected")
        medium_exc = NetworkError("Connection failed")

        assert get_severity(critical_exc) == ErrorSeverity.CRITICAL
        assert get_severity(medium_exc) == ErrorSeverity.MEDIUM

    def test_get_severity_builtin_exception(self):
        """Test get_severity with built-in exception."""
        value_error = ValueError("Invalid")
        assert get_severity(value_error) == ErrorSeverity.MEDIUM


class TestErrorHierarchy:
    """Test exception hierarchy relationships."""

    def test_inheritance_chain(self):
        """Test exception inheritance."""
        # All custom exceptions inherit from SecurityAuditException
        assert issubclass(ConfigurationError, SecurityAuditException)
        assert issubclass(APIKeyError, ConfigurationError)
        assert issubclass(NetworkError, SecurityAuditException)
        assert issubclass(RPCError, NetworkError)

    def test_multiple_inheritance_levels(self):
        """Test multi-level inheritance."""
        exc = APIKeyError("Missing key", api_name='test')

        # Should have all attributes from parent classes
        assert hasattr(exc, 'severity')
        assert hasattr(exc, 'retryable')
        assert hasattr(exc, 'context')
        assert hasattr(exc, 'message')

    def test_catching_base_exception(self):
        """Test catching exceptions by base class."""
        exceptions = [
            RPCError("RPC failed"),
            TenderlyError("Tenderly failed"),
            TimeoutError("Timeout")
        ]

        # All should be catchable as NetworkError
        for exc in exceptions:
            assert isinstance(exc, NetworkError)
            assert isinstance(exc, SecurityAuditException)
