"""
Test suite for input validation security fixes.

Tests:
1. Path traversal protection
2. Command injection prevention
3. RPC URL validation
4. Chain name validation
"""

import pytest
import os
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.security.validators import (
    PathValidator,
    CommandValidator,
    URLValidator,
    ChainValidator,
    PathTraversalError,
    CommandInjectionError,
    InvalidURLError,
    ValidationError,
)


class TestPathValidator:
    """Test PathValidator security fixes."""

    def test_valid_project_path(self, tmp_path):
        """Test that valid paths are accepted."""
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()

        validated = PathValidator.validate_project_path(
            str(project_dir),
            allowed_base=str(tmp_path)
        )

        assert validated == project_dir

    def test_path_traversal_blocked(self, tmp_path):
        """Test that ../ traversal is blocked."""
        with pytest.raises(PathTraversalError):
            PathValidator.validate_project_path(
                "../../etc/passwd",
                allowed_base=str(tmp_path)
            )

    def test_dangerous_paths_blocked(self, tmp_path):
        """Test that dangerous system paths are blocked."""
        dangerous_paths = [
            "/etc/passwd",
            "/sys/kernel",
            "/proc/self",
            "C:\\Windows\\System32",
        ]

        for dangerous in dangerous_paths:
            with pytest.raises((PathTraversalError, ValidationError)):
                PathValidator.validate_project_path(dangerous, allowed_base=str(tmp_path))

    def test_path_escaping_project(self, tmp_path):
        """Test that paths escaping project directory are blocked."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Try to escape project directory
        with pytest.raises(PathTraversalError):
            PathValidator.validate_file_path(
                "../../../etc/passwd",
                str(project_dir)
            )

    def test_valid_file_path(self, tmp_path):
        """Test that valid file paths are accepted."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        file_path = "contracts/MyContract.sol"
        validated = PathValidator.validate_file_path(file_path, str(project_dir))

        expected = project_dir / file_path
        assert validated == expected

    def test_empty_path_rejected(self):
        """Test that empty paths are rejected."""
        with pytest.raises(ValidationError):
            PathValidator.validate_project_path("")

        with pytest.raises(ValidationError):
            PathValidator.validate_file_path("", "/some/base")

    def test_path_component_validation(self):
        """Test individual path component validation."""
        # Valid components
        assert PathValidator.validate_path_component("Contract.sol") == "Contract.sol"
        assert PathValidator.validate_path_component("my-contract") == "my-contract"
        assert PathValidator.validate_path_component("contract_v2") == "contract_v2"

        # Invalid components
        with pytest.raises(ValidationError):
            PathValidator.validate_path_component("..")

        with pytest.raises(ValidationError):
            PathValidator.validate_path_component(".")

        with pytest.raises(ValidationError):
            PathValidator.validate_path_component("contract;rm -rf /")


class TestCommandValidator:
    """Test CommandValidator security fixes."""

    def test_allowed_commands(self):
        """Test that whitelisted commands are accepted."""
        allowed_tools = ['slither', 'mythril', 'forge', 'npm']

        for tool in allowed_tools:
            cmd, args = CommandValidator.validate_command(tool, [])
            assert cmd == tool

    def test_disallowed_commands_blocked(self):
        """Test that non-whitelisted commands are rejected."""
        dangerous_commands = ['rm', 'sudo', 'cat', 'ls', 'bash', 'sh']

        for cmd in dangerous_commands:
            with pytest.raises(CommandInjectionError):
                CommandValidator.validate_command(cmd, [])

    def test_shell_metacharacters_blocked(self):
        """Test that shell metacharacters in arguments are blocked."""
        metacharacters = ['&&', '||', ';', '|', '`', '$', '<', '>', '(', ')', '{', '}', '!']

        for char in metacharacters:
            with pytest.raises(CommandInjectionError):
                CommandValidator.sanitize_argument(f"arg{char}value")

    def test_valid_arguments(self):
        """Test that valid arguments are accepted."""
        valid_args = [
            'Contract.sol',
            '/home/user/project',
            '--format=json',
            'my-contract',
        ]

        for arg in valid_args:
            sanitized = CommandValidator.sanitize_argument(arg)
            assert sanitized == arg

    def test_null_byte_blocked(self):
        """Test that null bytes are blocked."""
        with pytest.raises(CommandInjectionError):
            CommandValidator.sanitize_argument("arg\x00value")

    def test_newline_blocked(self):
        """Test that newlines are blocked (command injection technique)."""
        with pytest.raises(CommandInjectionError):
            CommandValidator.sanitize_argument("arg\nrm -rf /")

        with pytest.raises(CommandInjectionError):
            CommandValidator.sanitize_argument("arg\r\nmalicious")

    def test_file_argument_validation(self, tmp_path):
        """Test combined file path and argument validation."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Valid file argument
        validated = CommandValidator.validate_file_argument(
            "contracts/MyContract.sol",
            str(project_dir)
        )
        assert "contracts" in validated and "MyContract.sol" in validated

        # Invalid (escapes project)
        with pytest.raises(PathTraversalError):
            CommandValidator.validate_file_argument(
                "../../etc/passwd",
                str(project_dir)
            )


class TestURLValidator:
    """Test URLValidator security fixes."""

    def test_valid_rpc_urls(self):
        """Test that valid RPC URLs are accepted."""
        valid_urls = [
            "https://mainnet.infura.io/v3/abc123",
            "https://eth-mainnet.g.alchemy.com/v2/xyz789",
            "wss://polygon-mainnet.infura.io/ws/v3/abc123",
            "http://localhost:8545",
        ]

        for url in valid_urls:
            validated = URLValidator.validate_rpc_url(url)
            assert validated == url

    def test_dangerous_schemes_blocked(self):
        """Test that dangerous URL schemes are blocked."""
        dangerous_urls = [
            "file:///etc/passwd",
            "data:text/html,<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "ftp://malicious.com/file",
        ]

        for url in dangerous_urls:
            with pytest.raises(InvalidURLError):
                URLValidator.validate_rpc_url(url)

    def test_missing_domain_blocked(self):
        """Test that URLs without domains are blocked."""
        with pytest.raises(InvalidURLError):
            URLValidator.validate_rpc_url("https://")

        with pytest.raises(InvalidURLError):
            URLValidator.validate_rpc_url("http://")

    def test_private_ip_blocked(self):
        """Test that private IP addresses are blocked (SSRF protection)."""
        private_ips = [
            "https://192.168.1.1",
            "https://10.0.0.1",
            "https://172.16.0.1",
        ]

        for url in private_ips:
            with pytest.raises(InvalidURLError):
                URLValidator.validate_rpc_url(url)

    def test_safe_domain_whitelist(self):
        """Test that safe domain requirement works."""
        # Should pass with safe domain
        URLValidator.validate_rpc_url(
            "https://mainnet.infura.io/v3/abc",
            require_safe_domain=True
        )

        # Should fail with unknown domain
        with pytest.raises(InvalidURLError):
            URLValidator.validate_rpc_url(
                "https://unknown-rpc-provider.com/rpc",
                require_safe_domain=True
            )

    def test_empty_url_rejected(self):
        """Test that empty URLs are rejected."""
        with pytest.raises(ValidationError):
            URLValidator.validate_rpc_url("")


class TestChainValidator:
    """Test ChainValidator security fixes."""

    def test_valid_chain_names(self):
        """Test that valid chain names are accepted."""
        valid_chains = [
            'ethereum', 'mainnet', 'sepolia', 'goerli',
            'polygon', 'mumbai', 'arbitrum', 'optimism',
            'solana', 'solana-devnet',
        ]

        for chain in valid_chains:
            validated = ChainValidator.validate_chain_name(chain)
            assert validated == chain.lower()

    def test_invalid_chain_names_blocked(self):
        """Test that invalid chain names are rejected."""
        invalid_chains = [
            'unknown-chain',
            'bitcoin',  # Not in whitelist
            'chain;rm -rf /',  # Injection attempt
            '../../../etc/passwd',  # Path traversal
        ]

        for chain in invalid_chains:
            with pytest.raises(ValidationError):
                ChainValidator.validate_chain_name(chain)

    def test_empty_chain_name_rejected(self):
        """Test that empty chain names are rejected."""
        with pytest.raises(ValidationError):
            ChainValidator.validate_chain_name("")

    def test_case_insensitive(self):
        """Test that chain validation is case-insensitive."""
        assert ChainValidator.validate_chain_name("ETHEREUM") == "ethereum"
        assert ChainValidator.validate_chain_name("Polygon") == "polygon"
        assert ChainValidator.validate_chain_name("SoLaNa") == "solana"


class TestIntegrationSecurity:
    """Integration tests for security fixes across modules."""

    def test_path_validation_in_bridge(self, tmp_path):
        """Test that JavaScriptBridge validates paths."""
        from src.bridges.javascript_bridge import JavaScriptBridge

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Valid path should work
        bridge = JavaScriptBridge(project_root=str(project_dir))
        assert Path(bridge.project_root) == project_dir

        # Path traversal should be blocked
        with pytest.raises(PathTraversalError):
            JavaScriptBridge(project_root="../../etc")

    def test_chain_validation_in_adapters(self):
        """Test that adapters validate chain names."""
        from src.adversarial.simulation.adapters.base import _has_rpc_endpoint, _has_hardhat_config

        # Valid chains should work
        result = _has_rpc_endpoint("ethereum")  # Will return False (no env var set)
        assert isinstance(result, bool)

        # Invalid chains should be rejected (return False, not raise)
        result = _has_rpc_endpoint("malicious;chain")
        assert result is False

    def test_url_validation_in_direct_rpc(self):
        """Test that DirectRPCAdapter validates URLs."""
        from src.adversarial.simulation.adapters.direct_rpc_adapter import DirectRPCAdapter

        # Test with invalid URL - should raise InvalidURLError
        with pytest.raises(InvalidURLError):
            DirectRPCAdapter(
                chain="ethereum",
                rpc_url="file:///etc/passwd"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
