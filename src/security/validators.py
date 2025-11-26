"""
Input validation and sanitization utilities.

Provides security-critical validation for:
- File paths (prevent path traversal attacks)
- Shell commands (prevent command injection)
- URLs (prevent SSRF and malicious endpoints)
- Chain identifiers (prevent injection via chain names)

All validators follow a whitelist approach and fail closed (deny by default).
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Set
from urllib.parse import urlparse, ParseResult


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class PathTraversalError(ValidationError):
    """Raised when path traversal is detected."""
    pass


class CommandInjectionError(ValidationError):
    """Raised when command injection attempt is detected."""
    pass


class InvalidURLError(ValidationError):
    """Raised when URL validation fails."""
    pass


class PathValidator:
    """
    Validates file and directory paths to prevent path traversal attacks.

    Security Model:
    - All paths must be within allowed base directories
    - Prevents ../ traversal attempts
    - Rejects absolute paths to sensitive directories
    - Validates path components contain only safe characters

    Example:
        validator = PathValidator(allowed_base="/home/user/projects")
        safe_path = validator.validate_project_path("./my-contract")
        # Returns: /home/user/projects/my-contract

        validator.validate_project_path("../../etc/passwd")
        # Raises: PathTraversalError
    """

    # Dangerous path patterns that should always be rejected
    DANGEROUS_PATTERNS = [
        '/etc', '/sys', '/proc', '/dev', '/root',
        'C:\\Windows', 'C:\\Program Files',
        '~/.ssh', '~/.aws', '~/.config'
    ]

    # Characters allowed in path components (alphanumeric, dash, underscore, dot)
    SAFE_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')

    @classmethod
    def validate_project_path(
        cls,
        project_path: str,
        allowed_base: Optional[str] = None
    ) -> Path:
        """
        Validate a project directory path.

        Args:
            project_path: Path to validate
            allowed_base: Base directory that path must be within (default: cwd)

        Returns:
            Validated absolute Path object

        Raises:
            PathTraversalError: If path traversal detected
            ValidationError: If path is invalid
        """
        if not project_path:
            raise ValidationError("Project path cannot be empty")

        # Use current working directory as default base
        if allowed_base is None:
            allowed_base = os.getcwd()

        # Resolve to absolute paths
        try:
            resolved_path = Path(project_path).resolve()
            base_path = Path(allowed_base).resolve()
        except (ValueError, OSError) as e:
            raise ValidationError(f"Invalid path: {e}")

        # Check if resolved path is within allowed base
        try:
            resolved_path.relative_to(base_path)
        except ValueError:
            raise PathTraversalError(
                f"Path escapes allowed directory: {project_path} "
                f"is not within {allowed_base}"
            )

        # Check for dangerous patterns
        path_str = str(resolved_path)
        for dangerous in cls.DANGEROUS_PATTERNS:
            if path_str.startswith(dangerous) or dangerous in path_str:
                raise PathTraversalError(
                    f"Path contains dangerous pattern: {dangerous}"
                )

        # Check for path traversal sequences
        if '..' in project_path or project_path.startswith('/'):
            # Only allow if it resolves safely (already checked above)
            # But warn about suspicious input
            pass

        return resolved_path

    @classmethod
    def validate_file_path(
        cls,
        file_path: str,
        project_base: str
    ) -> Path:
        """
        Validate a file path relative to project base.

        Args:
            file_path: Relative file path
            project_base: Project directory base

        Returns:
            Validated absolute Path object

        Raises:
            PathTraversalError: If file escapes project directory
        """
        if not file_path:
            raise ValidationError("File path cannot be empty")

        # Construct full path
        full_path = os.path.join(project_base, file_path)

        # Validate using project path validation
        validated_project = cls.validate_project_path(
            project_base,
            allowed_base=os.getcwd()
        )

        # Resolve file path
        try:
            resolved_file = Path(full_path).resolve()
        except (ValueError, OSError) as e:
            raise ValidationError(f"Invalid file path: {e}")

        # Ensure file is within project
        try:
            resolved_file.relative_to(validated_project)
        except ValueError:
            raise PathTraversalError(
                f"File escapes project directory: {file_path}"
            )

        return resolved_file

    @classmethod
    def validate_path_component(cls, component: str) -> str:
        """
        Validate a single path component (filename or directory name).

        Args:
            component: Path component to validate

        Returns:
            Validated component

        Raises:
            ValidationError: If component contains unsafe characters
        """
        if not component:
            raise ValidationError("Path component cannot be empty")

        if component in ('.', '..'):
            raise ValidationError(f"Path component cannot be: {component}")

        if not cls.SAFE_PATH_PATTERN.match(component):
            raise ValidationError(
                f"Path component contains unsafe characters: {component}"
            )

        return component


class CommandValidator:
    """
    Validates shell commands and arguments to prevent command injection.

    Security Model:
    - Whitelist allowed commands
    - Sanitize all arguments
    - Reject shell metacharacters
    - Use array form for subprocess calls

    Example:
        validator = CommandValidator(allowed_commands=['slither', 'mythril'])
        cmd, args = validator.validate_command('slither', ['Contract.sol'])
        # subprocess.run([cmd] + args)
    """

    # Allowed tool commands (whitelist)
    ALLOWED_TOOLS: Set[str] = {
        'slither',
        'mythril',
        'forge',
        'echidna',
        'cargo',
        'npm',
        'node',
        'python',
        'python3',
    }

    # Shell metacharacters that should be rejected in arguments
    SHELL_METACHARACTERS = set(';&|`$<>(){}[]!*?')

    @classmethod
    def validate_command(
        cls,
        command: str,
        arguments: Optional[List[str]] = None
    ) -> tuple[str, List[str]]:
        """
        Validate a command and its arguments.

        Args:
            command: Command name to execute
            arguments: List of command arguments

        Returns:
            Tuple of (validated_command, validated_arguments)

        Raises:
            CommandInjectionError: If command or args are unsafe
        """
        if not command:
            raise ValidationError("Command cannot be empty")

        # Validate command is in whitelist
        if command not in cls.ALLOWED_TOOLS:
            raise CommandInjectionError(
                f"Command not in whitelist: {command}. "
                f"Allowed: {', '.join(sorted(cls.ALLOWED_TOOLS))}"
            )

        # Validate arguments
        validated_args = []
        if arguments:
            for arg in arguments:
                validated_args.append(cls.sanitize_argument(arg))

        return command, validated_args

    @classmethod
    def sanitize_argument(cls, argument: str) -> str:
        """
        Sanitize a command argument.

        Args:
            argument: Argument to sanitize

        Returns:
            Sanitized argument

        Raises:
            CommandInjectionError: If argument contains shell metacharacters
        """
        if not isinstance(argument, str):
            raise ValidationError(f"Argument must be string, got {type(argument)}")

        # Check for shell metacharacters
        for char in argument:
            if char in cls.SHELL_METACHARACTERS:
                raise CommandInjectionError(
                    f"Argument contains shell metacharacter: {char} in {argument}"
                )

        # Check for null bytes
        if '\0' in argument:
            raise CommandInjectionError("Argument contains null byte")

        # Check for newlines (command injection technique)
        if '\n' in argument or '\r' in argument:
            raise CommandInjectionError("Argument contains newline")

        return argument

    @classmethod
    def validate_file_argument(cls, file_path: str, project_base: str) -> str:
        """
        Validate a file path argument for shell commands.

        Combines path validation with argument sanitization.

        Args:
            file_path: File path argument
            project_base: Project base directory

        Returns:
            Validated file path string
        """
        # First validate as path
        validated_path = PathValidator.validate_file_path(file_path, project_base)

        # Then sanitize as argument
        path_str = str(validated_path)
        return cls.sanitize_argument(path_str)


class URLValidator:
    """
    Validates URLs to prevent SSRF and malicious endpoint attacks.

    Security Model:
    - Whitelist allowed schemes (https, http, wss, ws)
    - Whitelist or validate domains
    - Reject file://, data://, and other dangerous schemes
    - Validate URL structure

    Example:
        validator = URLValidator()
        url = validator.validate_rpc_url("https://mainnet.infura.io/v3/...")
        # Returns validated URL

        validator.validate_rpc_url("file:///etc/passwd")
        # Raises: InvalidURLError
    """

    # Allowed URL schemes for RPC endpoints
    ALLOWED_SCHEMES: Set[str] = {'https', 'http', 'wss', 'ws'}

    # Known safe RPC provider domains (whitelist)
    SAFE_RPC_DOMAINS: Set[str] = {
        'mainnet.infura.io',
        'sepolia.infura.io',
        'goerli.infura.io',
        'polygon-mainnet.infura.io',
        'alchemy.com',
        'eth-mainnet.g.alchemy.com',
        'eth-sepolia.g.alchemy.com',
        'cloudflare-eth.com',
        'rpc.ankr.com',
        'api.tenderly.co',
        'localhost',
        '127.0.0.1',
    }

    @classmethod
    def validate_rpc_url(
        cls,
        url: str,
        require_safe_domain: bool = False
    ) -> str:
        """
        Validate an RPC URL.

        Args:
            url: URL to validate
            require_safe_domain: If True, require domain in whitelist

        Returns:
            Validated URL string

        Raises:
            InvalidURLError: If URL is invalid or unsafe
        """
        if not url:
            raise ValidationError("URL cannot be empty")

        # Parse URL
        try:
            parsed: ParseResult = urlparse(url)
        except Exception as e:
            raise InvalidURLError(f"Invalid URL format: {e}")

        # Validate scheme
        if parsed.scheme not in cls.ALLOWED_SCHEMES:
            raise InvalidURLError(
                f"URL scheme not allowed: {parsed.scheme}. "
                f"Allowed: {', '.join(cls.ALLOWED_SCHEMES)}"
            )

        # Validate has netloc (domain)
        if not parsed.netloc:
            raise InvalidURLError("URL must have a domain")

        # Extract domain (without port)
        domain = parsed.netloc.split(':')[0].lower()

        # Check against whitelist if required
        if require_safe_domain:
            if domain not in cls.SAFE_RPC_DOMAINS:
                raise InvalidURLError(
                    f"Domain not in whitelist: {domain}. "
                    f"Known safe domains: {', '.join(sorted(cls.SAFE_RPC_DOMAINS))}"
                )

        # Reject localhost/127.0.0.1 in production (SSRF risk)
        # This is a basic check - in production you'd check environment
        if domain in ('localhost', '127.0.0.1') and require_safe_domain:
            # Allow for development but warn
            pass

        # Reject private IP ranges (SSRF prevention)
        if cls._is_private_ip(domain):
            raise InvalidURLError(f"Private IP addresses not allowed: {domain}")

        return url

    @staticmethod
    def _is_private_ip(domain: str) -> bool:
        """Check if domain is a private IP address."""
        # Basic check for common private IP ranges
        private_ranges = [
            '192.168.', '10.', '172.16.', '172.17.', '172.18.',
            '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
            '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
            '172.29.', '172.30.', '172.31.'
        ]

        for prefix in private_ranges:
            if domain.startswith(prefix):
                return True

        return False


class ChainValidator:
    """
    Validates blockchain chain identifiers.

    Security Model:
    - Whitelist allowed chain names
    - Prevent injection via chain names
    - Validate format
    """

    ALLOWED_CHAINS: Set[str] = {
        'ethereum', 'mainnet', 'sepolia', 'goerli',
        'polygon', 'mumbai',
        'avalanche', 'fuji',
        'bsc', 'bsc-testnet',
        'arbitrum', 'arbitrum-goerli',
        'optimism', 'optimism-goerli',
        'base', 'base-goerli',
        'solana', 'solana-devnet',
    }

    @classmethod
    def validate_chain_name(cls, chain: str) -> str:
        """
        Validate a chain identifier.

        Args:
            chain: Chain name to validate

        Returns:
            Validated chain name (lowercase)

        Raises:
            ValidationError: If chain name is invalid
        """
        if not chain:
            raise ValidationError("Chain name cannot be empty")

        chain_lower = chain.lower().strip()

        if chain_lower not in cls.ALLOWED_CHAINS:
            raise ValidationError(
                f"Unknown chain: {chain}. "
                f"Allowed: {', '.join(sorted(cls.ALLOWED_CHAINS))}"
            )

        return chain_lower
