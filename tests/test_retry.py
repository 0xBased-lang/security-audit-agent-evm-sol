"""
Test suite for retry logic with exponential backoff.

Tests:
1. Exponential backoff calculation
2. Retry decorator functionality
3. RetryContext context manager
4. retry_on_failure helper
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.utils.retry import (
    exponential_backoff,
    retry_with_backoff,
    RetryContext,
    retry_on_failure
)
from src.exceptions import NetworkError, ValidationError, RPCError


class TestExponentialBackoff:
    """Test exponential backoff calculation."""

    def test_base_delay(self):
        """Test base delay calculation."""
        delay = exponential_backoff(0, base_delay=1.0, jitter=False)
        assert delay == 1.0

    def test_exponential_growth(self):
        """Test exponential growth."""
        # Without jitter for predictable testing
        delays = [
            exponential_backoff(i, base_delay=1.0, max_delay=60.0, jitter=False)
            for i in range(5)
        ]

        # Should grow exponentially: 1, 2, 4, 8, 16
        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_max_delay_cap(self):
        """Test maximum delay cap."""
        delay = exponential_backoff(10, base_delay=1.0, max_delay=30.0, jitter=False)
        assert delay == 30.0

    def test_jitter_adds_randomness(self):
        """Test jitter adds randomness."""
        delays = [
            exponential_backoff(3, base_delay=1.0, max_delay=60.0, jitter=True)
            for _ in range(10)
        ]

        # With jitter, delays should vary
        assert len(set(delays)) > 1

        # But all should be in reasonable range (8 + 0 to 25% = 8-10)
        for delay in delays:
            assert 8.0 <= delay <= 10.0


class TestRetryDecorator:
    """Test retry_with_backoff decorator."""

    def test_success_on_first_try(self):
        """Test function succeeds immediately."""
        mock_func = Mock(return_value="success")

        @retry_with_backoff(max_retries=3)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_success_after_retries(self):
        """Test function succeeds after retries."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Temporary failure")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count == 3

    def test_max_retries_exceeded(self):
        """Test exception raised when max retries exceeded."""
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def test_func():
            raise NetworkError("Always fails")

        with pytest.raises(NetworkError):
            test_func()

    def test_non_retryable_exception(self):
        """Test non-retryable exception fails immediately."""
        mock_func = Mock(side_effect=ValidationError("Bad input"))

        @retry_with_backoff(
            max_retries=3,
            retryable_exceptions=(NetworkError,)
        )
        def test_func():
            return mock_func()

        with pytest.raises(ValidationError):
            test_func()

        # Should fail immediately, no retries
        assert mock_func.call_count == 1

    def test_retry_callback(self):
        """Test on_retry callback is called."""
        retry_calls = []

        def on_retry_callback(exception, attempt):
            retry_calls.append((exception, attempt))

        call_count = 0

        @retry_with_backoff(
            max_retries=3,
            base_delay=0.01,
            on_retry=on_retry_callback
        )
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError(f"Fail {call_count}")
            return "success"

        result = test_func()

        assert result == "success"
        assert len(retry_calls) == 2  # Called on first 2 failures
        assert retry_calls[0][1] == 1  # First retry attempt
        assert retry_calls[1][1] == 2  # Second retry attempt

    def test_exponential_backoff_timing(self):
        """Test retry delays follow exponential backoff."""
        call_times = []

        @retry_with_backoff(max_retries=3, base_delay=0.1, max_delay=1.0)
        def test_func():
            call_times.append(time.time())
            if len(call_times) < 4:
                raise NetworkError("Retry")
            return "success"

        result = test_func()

        assert result == "success"
        assert len(call_times) == 4

        # Check delays between calls
        delays = [call_times[i+1] - call_times[i] for i in range(3)]

        # Delays should increase (allowing for jitter variance)
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]


class TestRetryContext:
    """Test RetryContext context manager."""

    def test_successful_operation(self):
        """Test context with successful operation."""
        call_count = 0

        with RetryContext(max_retries=3) as retry:
            for attempt in retry:
                call_count += 1
                result = "success"
                break

        assert result == "success"
        assert call_count == 1

    def test_retry_until_success(self):
        """Test retrying until operation succeeds."""
        call_count = 0

        with RetryContext(max_retries=5, base_delay=0.01) as retry:
            for attempt in retry:
                call_count += 1
                try:
                    if call_count < 3:
                        raise NetworkError("Temporary")
                    result = "success"
                    break
                except NetworkError as e:
                    if not retry.should_retry(e):
                        raise
                    retry.wait()

        assert result == "success"
        assert call_count == 3

    def test_max_retries_exhausted(self):
        """Test exception when retries exhausted."""
        with pytest.raises(NetworkError):
            with RetryContext(max_retries=2, base_delay=0.01) as retry:
                for attempt in retry:
                    try:
                        raise NetworkError("Always fails")
                    except NetworkError as e:
                        if not retry.should_retry(e):
                            raise
                        if attempt >= retry.max_retries:
                            raise
                        retry.wait()

    def test_non_retryable_exception(self):
        """Test non-retryable exception exits immediately."""
        call_count = 0

        with pytest.raises(ValidationError):
            with RetryContext(
                max_retries=3,
                retryable_exceptions=(NetworkError,)
            ) as retry:
                for attempt in retry:
                    call_count += 1
                    try:
                        raise ValidationError("Not retryable")
                    except ValidationError as e:
                        if not retry.should_retry(e):
                            raise
                        retry.wait()

        assert call_count == 1


class TestRetryOnFailure:
    """Test retry_on_failure helper function."""

    def test_successful_operation(self):
        """Test operation succeeds on first try."""
        operation = Mock(return_value="success")

        result = retry_on_failure(
            operation,
            max_retries=3,
            param1="value1"
        )

        assert result == "success"
        operation.assert_called_once_with(param1="value1")

    def test_retry_until_success(self):
        """Test retrying until success."""
        call_count = 0

        def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Temporary")
            return "success"

        result = retry_on_failure(
            operation,
            max_retries=5,
            base_delay=0.01
        )

        assert result == "success"
        assert call_count == 3

    def test_max_retries_exceeded(self):
        """Test exception when max retries exceeded."""
        operation = Mock(side_effect=NetworkError("Always fails"))

        with pytest.raises(NetworkError):
            retry_on_failure(
                operation,
                max_retries=2,
                base_delay=0.01
            )

        assert operation.call_count == 3  # Initial + 2 retries


class TestRetryWithRealExceptions:
    """Test retry logic with real framework exceptions."""

    def test_retry_rpc_error(self):
        """Test retrying RPC errors."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def fetch_from_rpc():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RPCError(
                    "Connection timeout",
                    rpc_url="https://mainnet.infura.io",
                    chain_id=1
                )
            return {"block": "0x123"}

        result = fetch_from_rpc()

        assert result == {"block": "0x123"}
        assert call_count == 2

    def test_no_retry_validation_error(self):
        """Test validation errors don't retry."""
        call_count = 0

        @retry_with_backoff(
            max_retries=3,
            retryable_exceptions=(NetworkError,)
        )
        def validate_input():
            nonlocal call_count
            call_count += 1
            raise ValidationError("Invalid address")

        with pytest.raises(ValidationError):
            validate_input()

        # Should fail immediately without retries
        assert call_count == 1


class TestRetryLogging:
    """Test retry mechanism logging."""

    @patch('src.utils.retry.logger')
    def test_retry_logs_attempts(self, mock_logger):
        """Test retry attempts are logged."""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Temporary")
            return "success"

        result = test_func()

        assert result == "success"

        # Should log 2 retry attempts
        assert mock_logger.log.call_count >= 2

    @patch('src.utils.retry.logger')
    def test_failure_logs_error(self, mock_logger):
        """Test final failure is logged."""
        @retry_with_backoff(max_retries=1, base_delay=0.01)
        def test_func():
            raise NetworkError("Always fails")

        with pytest.raises(NetworkError):
            test_func()

        # Should log error
        assert mock_logger.error.call_count >= 1
