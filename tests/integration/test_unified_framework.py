"""
Integration tests for unified security framework

Tests end-to-end workflow combining traditional and adversarial testing.
"""

import pytest
import asyncio
import os
from pathlib import Path

# Import framework
from src.unified_framework import (
    UnifiedSecurityFramework,
    quick_audit,
    standard_audit,
)
from src.config import AuditConfig
from src.schemas.vulnerability import VulnerabilitySeverity


@pytest.fixture
def test_project_path():
    """Path to test project (if available)"""
    # Try to find example project
    example_path = Path(__file__).parent.parent.parent / 'examples' / 'simple-vault'

    if example_path.exists():
        return str(example_path)

    # Skip if no test project available
    pytest.skip("No test project available")


@pytest.mark.asyncio
async def test_unified_framework_initialization():
    """Test framework can be initialized"""
    framework = UnifiedSecurityFramework()

    assert framework.config is not None
    assert framework.logger is not None
    assert framework.js_bridge is not None


@pytest.mark.asyncio
async def test_quick_audit_mode():
    """Test quick audit configuration"""
    config = AuditConfig.quick()

    assert config.mode == 'quick'
    assert config.traditional_enabled is True
    assert config.adversarial_enabled is False


@pytest.mark.asyncio
async def test_standard_audit_mode():
    """Test standard audit configuration"""
    config = AuditConfig.standard()

    assert config.mode == 'standard'
    assert config.traditional_enabled is True
    assert config.adversarial_enabled is True
    assert config.adversarial_iterations == 1000


@pytest.mark.asyncio
async def test_deep_audit_mode():
    """Test deep audit configuration"""
    config = AuditConfig.deep()

    assert config.mode == 'deep'
    assert config.traditional_enabled is True
    assert config.adversarial_enabled is True
    assert config.adversarial_iterations == 10000


@pytest.mark.asyncio
async def test_chain_detection():
    """Test chain type detection"""
    framework = UnifiedSecurityFramework()

    # Test Solana detection
    # (would need a test project with Cargo.toml)

    # Test Ethereum detection
    # (would need a test project with hardhat.config.js)

    # For now, just test default
    chain = framework._detect_chain('.')
    assert chain in ['ethereum', 'solana']


@pytest.mark.asyncio
async def test_vulnerability_schema():
    """Test vulnerability data structure"""
    from src.schemas.vulnerability import (
        UnifiedVulnerability,
        VulnerabilityLocation,
    )
    from datetime import datetime

    vuln = UnifiedVulnerability(
        id='test-001',
        type='reentrancy',
        severity=VulnerabilitySeverity.CRITICAL,
        title='Test Reentrancy',
        description='Test vulnerability',
        location=VulnerabilityLocation(
            file='test.sol',
            line=42,
        ),
        detected_by='test',
    )

    assert vuln.is_critical()
    assert vuln.get_priority_score() > 0

    # Test serialization
    vuln_dict = vuln.to_dict()
    assert vuln_dict['id'] == 'test-001'
    assert vuln_dict['severity'] == 'CRITICAL'

    # Test JSON
    json_str = vuln.to_json()
    assert 'test-001' in json_str


@pytest.mark.asyncio
async def test_cross_referencing():
    """Test vulnerability cross-referencing"""
    from src.schemas.vulnerability import (
        UnifiedVulnerability,
        VulnerabilityLocation,
    )

    framework = UnifiedSecurityFramework()

    # Create duplicate vulnerabilities
    vuln1 = UnifiedVulnerability(
        id='slither-001',
        type='reentrancy',
        severity=VulnerabilitySeverity.CRITICAL,
        title='Reentrancy in withdraw',
        description='Found by Slither',
        location=VulnerabilityLocation(file='Bank.sol', line=42),
        detected_by='slither',
        confidence=0.9,
    )

    vuln2 = UnifiedVulnerability(
        id='mythril-001',
        type='reentrancy',
        severity=VulnerabilitySeverity.HIGH,
        title='Reentrancy vulnerability',
        description='Found by Mythril',
        location=VulnerabilityLocation(file='Bank.sol', line=42),
        detected_by='mythril',
        confidence=0.85,
    )

    # Cross-reference
    merged = framework._cross_reference_findings([vuln1, vuln2])

    # Should merge duplicates
    assert len(merged) == 1

    # Should keep highest severity
    assert merged[0].severity == VulnerabilitySeverity.CRITICAL

    # Should record both detectors
    assert 'mythril' in merged[0].confirmed_by or merged[0].detected_by == 'slither'

    # Should increase confidence
    assert merged[0].confidence > 0.9


@pytest.mark.slow
@pytest.mark.asyncio
async def test_full_audit_workflow(test_project_path):
    """
    Test complete audit workflow

    This is a slow test that runs a real audit.
    Only runs if test project is available.
    """
    # Run quick audit (traditional only)
    report = await quick_audit(test_project_path)

    # Validate report
    assert report is not None
    assert report.project_path == test_project_path
    assert report.audit_mode == 'quick'
    assert report.duration_seconds > 0

    # Should have some results (even if no vulnerabilities)
    assert report.vulnerabilities is not None

    # Check statistics are calculated
    assert report.total_vulnerabilities >= 0


@pytest.mark.asyncio
async def test_javascript_bridge():
    """Test JavaScript bridge functionality"""
    from src.bridges.javascript_bridge import JavaScriptBridge

    bridge = JavaScriptBridge()

    # Should be able to check tools
    tools = bridge.check_tools_available()

    # Should return a dict
    assert isinstance(tools, dict)


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for invalid inputs"""
    framework = UnifiedSecurityFramework()

    # Test with non-existent path
    with pytest.raises(ValueError):
        await framework.audit('/non/existent/path')


def test_config_validation():
    """Test configuration validation"""
    config = AuditConfig()

    # Should validate successfully
    assert config.validate() is True

    # Test invalid mode
    config.mode = 'invalid'
    with pytest.raises(ValueError):
        config.validate()


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
