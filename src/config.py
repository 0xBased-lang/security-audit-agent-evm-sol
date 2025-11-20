"""
Configuration management for the unified security framework
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class AuditConfig:
    """
    Configuration for security audits

    Modes:
    - quick: Traditional tools only (2-5 min)
    - standard: Traditional + basic adversarial (30-60 min)
    - deep: Full 10-layer AASS (2-4 hours)
    """

    # Audit mode
    mode: str = "standard"  # "quick", "standard", "deep"

    # Traditional audit settings
    traditional_enabled: bool = True
    traditional_tools: Optional[List[str]] = None  # None = all available
    traditional_timeout: int = 600  # seconds

    # Adversarial testing settings
    adversarial_enabled: bool = True
    adversarial_iterations: int = 1000
    adversarial_strategies: Optional[List[str]] = None  # None = all
    adversarial_timeout: int = 3600

    # Chain configuration
    chain: str = "ethereum"
    fork_block: Optional[int] = None
    simulation_adapter: Optional[str] = None  # None = auto-select

    # AI analysis settings
    ai_enabled: bool = True
    ai_model: str = "claude-sonnet-4"
    ai_max_tokens: int = 4096

    # Performance settings
    parallel_execution: bool = True
    max_workers: int = 4

    # Output settings
    output_dir: str = "./audit-results"
    output_formats: List[str] = field(default_factory=lambda: ["json", "markdown", "html"])
    verbose: bool = False

    # Resource limits
    max_memory_mb: int = 8192
    max_execution_time: int = 14400  # 4 hours

    # API keys (loaded from environment)
    anthropic_api_key: Optional[str] = field(default=None)
    tenderly_api_key: Optional[str] = field(default=None)

    def __post_init__(self):
        """Load API keys from environment"""
        if self.anthropic_api_key is None:
            self.anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')

        if self.tenderly_api_key is None:
            self.tenderly_api_key = os.environ.get('TENDERLY_API_KEY')

        # Adjust settings based on mode
        if self.mode == "quick":
            self.adversarial_enabled = False
            self.adversarial_iterations = 0
        elif self.mode == "standard":
            self.adversarial_iterations = 1000
        elif self.mode == "deep":
            self.adversarial_iterations = 10000

        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_mode(cls, mode: str) -> 'AuditConfig':
        """
        Create config for specific audit mode

        Args:
            mode: "quick", "standard", or "deep"

        Returns:
            Configured AuditConfig instance
        """
        return cls(mode=mode)

    @classmethod
    def quick(cls) -> 'AuditConfig':
        """Quick audit configuration (2-5 min)"""
        return cls(mode="quick")

    @classmethod
    def standard(cls) -> 'AuditConfig':
        """Standard audit configuration (30-60 min)"""
        return cls(mode="standard")

    @classmethod
    def deep(cls) -> 'AuditConfig':
        """Deep audit configuration (2-4 hours)"""
        return cls(mode="deep")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'mode': self.mode,
            'traditional_enabled': self.traditional_enabled,
            'traditional_tools': self.traditional_tools,
            'adversarial_enabled': self.adversarial_enabled,
            'adversarial_iterations': self.adversarial_iterations,
            'chain': self.chain,
            'fork_block': self.fork_block,
            'ai_enabled': self.ai_enabled,
            'output_dir': self.output_dir,
            'output_formats': self.output_formats,
        }

    def validate(self) -> bool:
        """
        Validate configuration

        Returns:
            True if config is valid

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate mode
        valid_modes = ['quick', 'standard', 'deep']
        if self.mode not in valid_modes:
            raise ValueError(
                f"Invalid mode '{self.mode}'. "
                f"Must be one of: {', '.join(valid_modes)}"
            )

        # Validate iterations
        if self.adversarial_iterations < 0:
            raise ValueError("adversarial_iterations must be >= 0")

        # Validate output formats
        valid_formats = ['json', 'markdown', 'html']
        for fmt in self.output_formats:
            if fmt not in valid_formats:
                raise ValueError(
                    f"Invalid output format '{fmt}'. "
                    f"Must be one of: {', '.join(valid_formats)}"
                )

        # Warn if AI enabled but no API key
        if self.ai_enabled and not self.anthropic_api_key:
            import logging
            logging.warning(
                "AI analysis enabled but ANTHROPIC_API_KEY not set. "
                "AI synthesis will be skipped."
            )

        return True


# Default configurations
DEFAULT_CONFIG = AuditConfig()
QUICK_CONFIG = AuditConfig.quick()
STANDARD_CONFIG = AuditConfig.standard()
DEEP_CONFIG = AuditConfig.deep()
