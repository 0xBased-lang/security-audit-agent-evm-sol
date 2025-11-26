"""
Pytest configuration for security audit framework tests.

Configures:
- pytest-asyncio for async test support (optional)
- Custom markers (slow, benchmark)
- Common fixtures
"""

import pytest
import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Configure pytest-asyncio
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "benchmark: marks tests as benchmark tests"
    )
    config.addinivalue_line(
        "markers", "asyncio: marks tests as async tests"
    )


# Conditionally load pytest-asyncio if available
try:
    import pytest_asyncio
    pytest_plugins = ['pytest_asyncio']
except ImportError:
    # pytest-asyncio not installed - async tests will be skipped
    pass


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def examples_path(project_root):
    """Return the examples directory."""
    return project_root / "examples"


@pytest.fixture
def vulnerable_evm_path(examples_path):
    """Return the vulnerable EVM contracts path."""
    path = examples_path / "vulnerable-evm"
    if not path.exists():
        pytest.skip("Vulnerable EVM contracts not found")
    return path


@pytest.fixture
def audit_results_path(project_root, tmp_path):
    """Return a temporary audit results directory."""
    return tmp_path / "audit-results"
