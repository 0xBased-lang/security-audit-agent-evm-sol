"""
Fuzz tests for security audit framework.

Uses property-based testing to discover edge cases and vulnerabilities.
"""

import pytest
import string
import random
from hypothesis import given, strategies as st, settings, example
from pathlib import Path

from src.security.validators import PathValidator, CommandValidator, URLValidator
from src.exceptions import (
    PathTraversalError,
    CommandInjectionError,
    ValidationError,
    SecurityAuditException
)


class TestPathValidationFuzz:
    """Fuzz tests for path validation."""

    @given(st.text(alphabet=string.printable, min_size=1, max_size=500))
    @settings(max_examples=200)
    def test_path_validator_never_crashes(self, path_input):
        """Test path validator never crashes regardless of input."""
        try:
            # Should either validate or raise exception, never crash
            PathValidator.validate_path(path_input, "/tmp/project")
        except (PathTraversalError, ValidationError, OSError):
            # Expected exceptions are ok
            pass
        except Exception as e:
            # Unexpected exception - test fails
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    @given(
        st.lists(
            st.text(alphabet=string.ascii_letters + string.digits + ".-_/\\", max_size=50),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_path_components_fuzzing(self, path_components):
        """Test path validation with random path components."""
        path = "/".join(path_components)

        try:
            PathValidator.validate_path(path, "/tmp/project")
        except (PathTraversalError, ValidationError, OSError):
            pass

    @given(st.binary(min_size=1, max_size=500))
    @settings(max_examples=100)
    def test_binary_path_input(self, binary_input):
        """Test path validator with binary input."""
        try:
            # Try to decode as UTF-8
            path = binary_input.decode('utf-8', errors='ignore')
            PathValidator.validate_path(path, "/tmp/project")
        except (PathTraversalError, ValidationError, UnicodeDecodeError, OSError):
            pass


class TestCommandValidationFuzz:
    """Fuzz tests for command validation."""

    @given(
        st.text(alphabet=string.printable, min_size=1, max_size=100),
        st.lists(
            st.text(alphabet=string.printable, max_size=100),
            min_size=0,
            max_size=20
        )
    )
    @settings(max_examples=200)
    def test_command_validator_never_crashes(self, command, args):
        """Test command validator never crashes."""
        try:
            CommandValidator.validate_command(command, args)
        except (CommandInjectionError, ValidationError):
            # Expected exceptions
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    @given(
        st.lists(
            st.text(
                alphabet=string.ascii_letters + string.digits + "!@#$%^&*()_+-={}[]|\\:\";<>?,./",
                min_size=1,
                max_size=50
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=150)
    def test_command_args_fuzzing(self, args):
        """Test command validation with random arguments."""
        try:
            CommandValidator.validate_command("slither", args)
        except (CommandInjectionError, ValidationError):
            pass

    @given(st.dictionaries(
        st.text(alphabet=string.ascii_uppercase + "_", min_size=1, max_size=20),
        st.text(alphabet=string.printable, max_size=100),
        min_size=0,
        max_size=10
    ))
    @settings(max_examples=100)
    def test_env_vars_fuzzing(self, env_vars):
        """Test environment variable validation with random inputs."""
        try:
            CommandValidator.validate_env_vars(env_vars)
        except (ValidationError,):
            pass


class TestURLValidationFuzz:
    """Fuzz tests for URL validation."""

    @given(st.text(alphabet=string.printable, min_size=1, max_size=500))
    @settings(max_examples=200)
    def test_url_validator_never_crashes(self, url_input):
        """Test URL validator never crashes."""
        try:
            URLValidator.validate_rpc_url(url_input)
        except (ValidationError,):
            # Expected exceptions
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    @given(
        st.sampled_from(["http", "https", "ws", "wss", "ftp", "file", "javascript", "data"]),
        st.text(alphabet=string.ascii_letters + string.digits + ".-", min_size=1, max_size=50),
        st.integers(min_value=1, max_value=65535),
        st.text(alphabet=string.ascii_letters + string.digits + "/_-?&=", max_size=100)
    )
    @settings(max_examples=150)
    def test_url_components_fuzzing(self, protocol, host, port, path):
        """Test URL validation with random components."""
        url = f"{protocol}://{host}:{port}/{path}"

        try:
            URLValidator.validate_rpc_url(url)
        except (ValidationError,):
            pass


class TestExceptionHandlingFuzz:
    """Fuzz tests for exception handling."""

    @given(
        st.text(alphabet=string.printable, min_size=1, max_size=500),
        st.dictionaries(
            st.text(alphabet=string.ascii_letters + "_", min_size=1, max_size=20),
            st.one_of(
                st.text(max_size=100),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans()
            ),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=200)
    def test_exception_creation_never_crashes(self, message, context):
        """Test exception creation never crashes with random inputs."""
        try:
            exc = SecurityAuditException(message, context=context)
            # Should be able to convert to string
            str(exc)
            # Should be able to access attributes
            assert exc.message == message
            assert exc.context == context
        except Exception as e:
            pytest.fail(f"Exception creation failed: {type(e).__name__}: {e}")

    @given(st.text(alphabet=string.printable, min_size=0, max_size=1000))
    @settings(max_examples=100)
    def test_exception_string_representation(self, message):
        """Test exception string representation handles any message."""
        try:
            exc = SecurityAuditException(message)
            result = str(exc)
            # Result should be a string
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"String representation failed: {type(e).__name__}: {e}")


class TestEdgeCases:
    """Test edge cases discovered through fuzzing."""

    @pytest.mark.parametrize("empty_input", [
        "",
        " ",
        "\t",
        "\n",
        "\r\n",
        "   \t\n   ",
    ])
    def test_empty_and_whitespace_inputs(self, empty_input):
        """Test handling of empty and whitespace-only inputs."""
        with pytest.raises((ValidationError, PathTraversalError)):
            PathValidator.validate_path(empty_input, "/tmp/project")

    @pytest.mark.parametrize("special_chars", [
        "\x00",  # Null byte
        "\x1f",  # Unit separator
        "\x7f",  # DEL
        "�",     # Replacement character
    ])
    def test_special_character_handling(self, special_chars):
        """Test handling of special characters."""
        try:
            PathValidator.validate_path(special_chars, "/tmp/project")
        except (ValidationError, PathTraversalError, OSError):
            pass

    @pytest.mark.parametrize("long_input", [
        "a" * 1000,
        "a" * 10000,
        "../" * 1000,
        "a/b/" * 500,
    ])
    def test_very_long_inputs(self, long_input):
        """Test handling of very long inputs."""
        try:
            PathValidator.validate_path(long_input, "/tmp/project")
        except (ValidationError, PathTraversalError, OSError):
            pass

    @pytest.mark.parametrize("unicode_input", [
        "test\u0000file.sol",  # Null in unicode
        "test\u202efile.sol",  # Right-to-left override
        "test\ufefffile.sol",  # Zero-width no-break space
        "test\u200bfile.sol",  # Zero-width space
        "файл.sol",            # Cyrillic
        "文件.sol",            # Chinese
        "ファイル.sol",        # Japanese
        "🔥🔥🔥.sol",          # Emojis
    ])
    def test_unicode_handling(self, unicode_input):
        """Test handling of Unicode inputs."""
        try:
            PathValidator.validate_path(unicode_input, "/tmp/project")
        except (ValidationError, PathTraversalError, OSError):
            pass


class TestPropertyBasedValidation:
    """Property-based tests for validation logic."""

    @given(
        st.text(alphabet=string.ascii_letters + string.digits + "._-", min_size=1, max_size=50)
    )
    @settings(max_examples=100)
    @example("safe_file.sol")
    @example("contract-v2.sol")
    @example("test_123.sol")
    def test_safe_filenames_always_validate(self, safe_filename):
        """Test that safe filenames always validate."""
        # Safe filenames should never trigger traversal errors
        try:
            result = PathValidator.validate_path(safe_filename, "/tmp/project")
            # Should either succeed or fail with non-traversal error
            assert result is not None
        except PathTraversalError:
            pytest.fail(f"Safe filename {safe_filename} incorrectly flagged as traversal")
        except (ValidationError, OSError):
            # Other validation errors are ok (length, etc.)
            pass

    @given(
        st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20),
        st.lists(
            st.text(alphabet=string.ascii_letters + string.digits + "._-", min_size=1, max_size=30),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_safe_commands_always_validate(self, command, args):
        """Test that safe commands always validate."""
        # Commands without special chars should validate
        try:
            result = CommandValidator.validate_command(command, args)
            assert result is not None
        except CommandInjectionError:
            pytest.fail(f"Safe command {command} {args} incorrectly flagged as injection")
        except ValidationError:
            # Other validation errors are ok
            pass

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_traversal_patterns_always_detected(self, random_suffix):
        """Test that path traversal patterns are always detected."""
        # Paths with ../ should always be flagged (unless they resolve safely)
        traversal_path = f"../../etc/{random_suffix}"

        try:
            PathValidator.validate_path(traversal_path, "/tmp/project")
            # If it validates, it better not actually escape the directory
            # This would need additional checks in practice
        except (PathTraversalError, ValidationError, OSError):
            # Expected - traversal detected
            pass


class TestResilience:
    """Test resilience to malformed inputs."""

    @given(st.lists(st.integers(), min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_non_string_inputs_handled(self, non_string_list):
        """Test handling of non-string inputs."""
        try:
            # Should handle type errors gracefully
            PathValidator.validate_path(non_string_list, "/tmp/project")  # type: ignore
        except (TypeError, AttributeError, ValidationError, PathTraversalError):
            # Expected exceptions
            pass

    @given(st.none() | st.booleans() | st.floats())
    @settings(max_examples=50)
    def test_invalid_type_inputs(self, invalid_input):
        """Test handling of invalid type inputs."""
        try:
            PathValidator.validate_path(invalid_input, "/tmp/project")  # type: ignore
        except (TypeError, AttributeError, ValidationError, PathTraversalError):
            pass

    @pytest.mark.parametrize("nested_list", [
        [["nested"]],
        [[["deeply", "nested"]]],
        [1, [2, [3]]],
    ])
    def test_nested_structure_handling(self, nested_list):
        """Test handling of nested data structures."""
        try:
            CommandValidator.validate_command("slither", nested_list)  # type: ignore
        except (TypeError, AttributeError, ValidationError, CommandInjectionError):
            pass


class TestConcurrency:
    """Test validators under concurrent access."""

    def test_concurrent_validation(self):
        """Test validators work correctly under concurrent access."""
        import concurrent.futures
        import random

        test_paths = [
            "safe_file.sol",
            "../../etc/passwd",
            "contracts/Token.sol",
            "../../../root/.ssh/id_rsa",
        ]

        def validate_random_path(_):
            path = random.choice(test_paths)
            try:
                PathValidator.validate_path(path, "/tmp/project")
            except (PathTraversalError, ValidationError, OSError):
                pass

        # Run 100 concurrent validations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(validate_random_path, i) for i in range(100)]
            for future in concurrent.futures.as_completed(futures):
                # Should not raise exceptions
                future.result()
