"""
Custom exception hierarchy for Security Audit Framework.

Provides structured error handling with:
- Specific exception types for different error categories
- Error context preservation
- Retry-ability hints
- Severity levels
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorSeverity(Enum):
    """Error severity levels for classification and handling."""

    LOW = "low"              # Minor issues, non-blocking
    MEDIUM = "medium"        # Important but recoverable
    HIGH = "high"            # Significant impact, requires attention
    CRITICAL = "critical"    # System integrity at risk, immediate action required


class SecurityAuditException(Exception):
    """
    Base exception for all security audit framework errors.

    Attributes:
        message: Human-readable error description
        severity: ErrorSeverity level
        retryable: Whether operation can be retried
        context: Additional error context (file, line, operation, etc.)
    """

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        retryable: bool = False,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.retryable = retryable
        self.context = context or {}

    def __str__(self) -> str:
        """Format exception with context for logging."""
        base = f"[{self.severity.value.upper()}] {self.message}"

        if self.context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base += f" (Context: {ctx_str})"

        if self.retryable:
            base += " [RETRYABLE]"

        return base


# ============================================================================
# Configuration & Initialization Errors
# ============================================================================

class ConfigurationError(SecurityAuditException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        context = {}
        if config_key:
            context['config_key'] = config_key

        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            retryable=False,
            context=context
        )


class APIKeyError(ConfigurationError):
    """Raised when API key is missing, invalid, or unauthorized."""

    def __init__(self, message: str, api_name: Optional[str] = None):
        # Call ConfigurationError first to get base context
        super().__init__(message, config_key='api_key')

        # Add API name to context
        if api_name:
            self.context['api'] = api_name


# ============================================================================
# Network & External Service Errors
# ============================================================================

class NetworkError(SecurityAuditException):
    """Base class for network-related errors."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            context=context
        )


class RPCError(NetworkError):
    """Raised when RPC connection or request fails."""

    def __init__(
        self,
        message: str,
        rpc_url: Optional[str] = None,
        chain_id: Optional[int] = None
    ):
        context = {}
        if rpc_url:
            context['rpc_url'] = rpc_url
        if chain_id:
            context['chain_id'] = chain_id

        super().__init__(message, context=context)


class TenderlyError(NetworkError):
    """Raised when Tenderly API interaction fails."""

    def __init__(
        self,
        message: str,
        api_endpoint: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        context = {}
        if api_endpoint:
            context['endpoint'] = api_endpoint
        if status_code:
            context['status_code'] = status_code

        super().__init__(message, context=context)


class TimeoutError(NetworkError):
    """Raised when operation times out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None
    ):
        context = {}
        if timeout_seconds:
            context['timeout'] = timeout_seconds

        # Override parent to set different severity
        SecurityAuditException.__init__(
            self,
            message,
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            context=context
        )


# ============================================================================
# Validation & Input Errors
# ============================================================================

class ValidationError(SecurityAuditException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        context = {}
        if field:
            context['field'] = field
        if value is not None:
            # Don't include full value if it's sensitive/large
            context['value_type'] = type(value).__name__

        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            retryable=False,
            context=context
        )


class PathTraversalError(ValidationError):
    """Raised when path traversal attempt is detected."""

    def __init__(self, message: str, path: Optional[str] = None):
        # Call ValidationError first
        super().__init__(message, field='path')

        # Override severity to CRITICAL
        self.severity = ErrorSeverity.CRITICAL

        # Add path to context
        if path:
            self.context['path'] = path


class CommandInjectionError(ValidationError):
    """Raised when command injection attempt is detected."""

    def __init__(self, message: str, command: Optional[str] = None):
        # Call ValidationError first
        super().__init__(message, field='command')

        # Override severity to CRITICAL
        self.severity = ErrorSeverity.CRITICAL

        # Add command length to context (not full command for security)
        if command:
            self.context['command_length'] = len(command)


# ============================================================================
# Smart Contract & Blockchain Errors
# ============================================================================

class ContractError(SecurityAuditException):
    """Base class for smart contract related errors."""

    def __init__(self, message: str, retryable: bool = False, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            retryable=retryable,
            context=context
        )


class CompilationError(ContractError):
    """Raised when smart contract compilation fails."""

    def __init__(
        self,
        message: str,
        contract_path: Optional[str] = None,
        compiler_output: Optional[str] = None
    ):
        context = {}
        if contract_path:
            context['contract'] = contract_path
        if compiler_output:
            # Store only first 200 chars to avoid log spam
            context['compiler_error'] = compiler_output[:200]

        super().__init__(message, retryable=False, context=context)


class SimulationError(ContractError):
    """Raised when transaction simulation fails."""

    def __init__(
        self,
        message: str,
        tx_hash: Optional[str] = None,
        revert_reason: Optional[str] = None
    ):
        context = {}
        if tx_hash:
            context['tx_hash'] = tx_hash
        if revert_reason:
            context['revert'] = revert_reason

        super().__init__(message, retryable=False, context=context)


class InvariantViolation(ContractError):
    """Raised when protocol invariant is violated."""

    def __init__(
        self,
        message: str,
        invariant_name: Optional[str] = None,
        expected: Optional[Any] = None,
        actual: Optional[Any] = None
    ):
        context = {}
        if invariant_name:
            context['invariant'] = invariant_name
        if expected is not None:
            context['expected'] = str(expected)
        if actual is not None:
            context['actual'] = str(actual)

        # Call ContractError first
        super().__init__(message, retryable=False, context=context)

        # Override severity to CRITICAL
        self.severity = ErrorSeverity.CRITICAL


# ============================================================================
# Tool & External Integration Errors
# ============================================================================

class ToolError(SecurityAuditException):
    """Base class for external tool integration errors."""

    def __init__(self, message: str, tool_name: Optional[str] = None):
        context = {}
        if tool_name:
            context['tool'] = tool_name

        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            context=context
        )


class SlitherError(ToolError):
    """Raised when Slither analysis fails."""

    def __init__(self, message: str):
        super().__init__(message, tool_name='slither')


class MythrilError(ToolError):
    """Raised when Mythril analysis fails."""

    def __init__(self, message: str):
        super().__init__(message, tool_name='mythril')


class EchidnaError(ToolError):
    """Raised when Echidna fuzzing fails."""

    def __init__(self, message: str):
        super().__init__(message, tool_name='echidna')


# ============================================================================
# AI & LLM Errors
# ============================================================================

class AIError(SecurityAuditException):
    """Base class for AI/LLM related errors."""

    def __init__(self, message: str, retryable: bool = True, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            retryable=retryable,
            context=context
        )


class LLMRateLimitError(AIError):
    """Raised when LLM API rate limit is hit."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None
    ):
        context = {}
        if retry_after:
            context['retry_after_seconds'] = retry_after

        # Call AIError first
        super().__init__(message, retryable=True, context=context)

        # Override severity to LOW
        self.severity = ErrorSeverity.LOW


class LLMTokenLimitError(AIError):
    """Raised when LLM token limit is exceeded."""

    def __init__(
        self,
        message: str,
        token_count: Optional[int] = None,
        max_tokens: Optional[int] = None
    ):
        context = {}
        if token_count:
            context['token_count'] = token_count
        if max_tokens:
            context['max_tokens'] = max_tokens

        super().__init__(message, retryable=False, context=context)


# ============================================================================
# File & Resource Errors
# ============================================================================

class ResourceError(SecurityAuditException):
    """Base class for resource-related errors."""

    def __init__(self, message: str, retryable: bool = False, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            retryable=retryable,
            context=context
        )


class FileNotFoundError(ResourceError):
    """Raised when required file is not found."""

    def __init__(self, message: str, file_path: Optional[str] = None):
        context = {}
        if file_path:
            context['path'] = file_path

        super().__init__(message, retryable=False, context=context)


class PermissionError(ResourceError):
    """Raised when file/resource permissions are insufficient."""

    def __init__(
        self,
        message: str,
        resource: Optional[str] = None,
        required_permission: Optional[str] = None
    ):
        context = {}
        if resource:
            context['resource'] = resource
        if required_permission:
            context['required'] = required_permission

        # Call ResourceError first
        super().__init__(message, retryable=False, context=context)

        # Override severity to HIGH
        self.severity = ErrorSeverity.HIGH


# ============================================================================
# Utility Functions
# ============================================================================

def is_retryable(exception: Exception) -> bool:
    """
    Check if an exception is retryable.

    Args:
        exception: Exception to check

    Returns:
        True if exception can be retried
    """
    if isinstance(exception, SecurityAuditException):
        return exception.retryable

    # Network errors are generally retryable
    if isinstance(exception, (ConnectionError, OSError)):
        return True

    return False


def get_severity(exception: Exception) -> ErrorSeverity:
    """
    Get severity level of an exception.

    Args:
        exception: Exception to check

    Returns:
        ErrorSeverity level
    """
    if isinstance(exception, SecurityAuditException):
        return exception.severity

    # Default severity for unknown exceptions
    return ErrorSeverity.MEDIUM


__all__ = [
    # Enums
    'ErrorSeverity',

    # Base exceptions
    'SecurityAuditException',

    # Configuration
    'ConfigurationError',
    'APIKeyError',

    # Network
    'NetworkError',
    'RPCError',
    'TenderlyError',
    'TimeoutError',

    # Validation
    'ValidationError',
    'PathTraversalError',
    'CommandInjectionError',

    # Smart Contract
    'ContractError',
    'CompilationError',
    'SimulationError',
    'InvariantViolation',

    # Tools
    'ToolError',
    'SlitherError',
    'MythrilError',
    'EchidnaError',

    # AI/LLM
    'AIError',
    'LLMRateLimitError',
    'LLMTokenLimitError',

    # Resources
    'ResourceError',
    'FileNotFoundError',
    'PermissionError',

    # Utilities
    'is_retryable',
    'get_severity',
]
