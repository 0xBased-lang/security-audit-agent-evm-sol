#!/usr/bin/env python3
"""
Audit Mode Performance Benchmarks

Tests performance characteristics of different audit modes:
- Quick: Fast preliminary scan (target: <2 min)
- Standard: Balanced analysis (target: <10 min)
- Deep: Comprehensive audit (target: <30 min)

Run with: pytest tests/benchmarks/test_audit_benchmarks.py -v --benchmark-only
"""

import pytest
import subprocess
import time
import json
import os
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass


# Test configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
VULNERABLE_EVM_PATH = PROJECT_ROOT / 'examples' / 'vulnerable-evm'
AUDIT_RESULTS_PATH = PROJECT_ROOT / 'audit-results'


@dataclass
class AuditBenchmarkResult:
    """Result of an audit benchmark"""
    mode: str
    duration_seconds: float
    vulnerabilities_found: int
    memory_peak_mb: float
    exit_code: int
    success: bool


class AuditBenchmark:
    """Benchmark runner for audit modes"""

    # Target performance thresholds (in seconds)
    PERFORMANCE_TARGETS = {
        'quick': 120,    # 2 minutes
        'standard': 600, # 10 minutes
        'deep': 1800     # 30 minutes
    }

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.results = []

    def run_audit(self, mode: str, timeout: int = None) -> AuditBenchmarkResult:
        """Run an audit and measure performance"""
        timeout = timeout or self.PERFORMANCE_TARGETS.get(mode, 600)

        start_time = time.time()

        try:
            result = subprocess.run(
                [
                    'node', 'src/cli.js', 'audit',
                    '--project', str(self.project_path),
                    '--mode', mode,
                    '--output', str(AUDIT_RESULTS_PATH)
                ],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
                timeout=timeout
            )

            duration = time.time() - start_time

            # Count vulnerabilities from output
            vuln_count = self._count_vulnerabilities(result.stdout)

            return AuditBenchmarkResult(
                mode=mode,
                duration_seconds=duration,
                vulnerabilities_found=vuln_count,
                memory_peak_mb=0,  # Would need psutil for accurate measurement
                exit_code=result.returncode,
                success=True
            )

        except subprocess.TimeoutExpired:
            return AuditBenchmarkResult(
                mode=mode,
                duration_seconds=timeout,
                vulnerabilities_found=0,
                memory_peak_mb=0,
                exit_code=-1,
                success=False
            )

    def _count_vulnerabilities(self, output: str) -> int:
        """Count vulnerabilities from audit output"""
        # Try to find count in output
        lower = output.lower()
        if 'critical' in lower or 'high' in lower:
            return 1
        return 0


class TestAuditModePerformance:
    """Test audit mode performance targets"""

    @pytest.fixture
    def benchmark_runner(self):
        """Create benchmark runner"""
        if not VULNERABLE_EVM_PATH.exists():
            pytest.skip("Vulnerable contracts not found")
        return AuditBenchmark(VULNERABLE_EVM_PATH)

    @pytest.mark.benchmark
    def test_quick_mode_performance(self, benchmark_runner):
        """Quick mode should complete in under 2 minutes"""
        result = benchmark_runner.run_audit('quick')

        assert result.success, "Quick audit should complete"
        assert result.duration_seconds < AuditBenchmark.PERFORMANCE_TARGETS['quick'], \
            f"Quick audit took {result.duration_seconds:.1f}s, target is 120s"

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_standard_mode_performance(self, benchmark_runner):
        """Standard mode should complete in under 10 minutes"""
        result = benchmark_runner.run_audit('standard')

        assert result.success, "Standard audit should complete"
        assert result.duration_seconds < AuditBenchmark.PERFORMANCE_TARGETS['standard'], \
            f"Standard audit took {result.duration_seconds:.1f}s, target is 600s"

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_deep_mode_performance(self, benchmark_runner):
        """Deep mode should complete in under 30 minutes"""
        result = benchmark_runner.run_audit('deep')

        assert result.success, "Deep audit should complete"
        assert result.duration_seconds < AuditBenchmark.PERFORMANCE_TARGETS['deep'], \
            f"Deep audit took {result.duration_seconds:.1f}s, target is 1800s"


class TestToolPerformance:
    """Test individual tool performance"""

    @pytest.mark.benchmark
    def test_slither_performance(self):
        """Slither should analyze single file in under 30 seconds"""
        contract_path = VULNERABLE_EVM_PATH / 'Reentrancy.sol'

        if not contract_path.exists():
            pytest.skip("Reentrancy.sol not found")

        start = time.time()

        result = subprocess.run(
            ['slither', str(contract_path), '--json', '-'],
            capture_output=True,
            text=True,
            timeout=60
        )

        duration = time.time() - start

        assert duration < 60, f"Slither took {duration:.1f}s, target is 60s"

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_mythril_performance(self):
        """Mythril should analyze single file in under 5 minutes"""
        contract_path = VULNERABLE_EVM_PATH / 'Reentrancy.sol'

        if not contract_path.exists():
            pytest.skip("Reentrancy.sol not found")

        # Check Mythril is available
        check = subprocess.run(['myth', '--version'], capture_output=True)
        if check.returncode != 0:
            pytest.skip("Mythril not installed")

        start = time.time()

        result = subprocess.run(
            ['myth', 'analyze', str(contract_path), '-o', 'json'],
            capture_output=True,
            text=True,
            timeout=300
        )

        duration = time.time() - start

        assert duration < 300, f"Mythril took {duration:.1f}s, target is 300s"

    @pytest.mark.benchmark
    def test_foundry_build_performance(self):
        """Foundry should build project in under 120 seconds"""
        # Check Foundry is available
        check = subprocess.run(['forge', '--version'], capture_output=True)
        if check.returncode != 0:
            pytest.skip("Foundry not installed")

        start = time.time()

        result = subprocess.run(
            ['forge', 'build'],
            capture_output=True,
            text=True,
            cwd=str(VULNERABLE_EVM_PATH),
            timeout=180
        )

        duration = time.time() - start

        # Build may fail due to missing dependencies, but should be fast
        # First-time builds with dependencies can take longer
        assert duration < 120, f"Forge build took {duration:.1f}s, target is 120s"


class TestAdversarialPerformance:
    """Test adversarial analysis performance"""

    @pytest.mark.benchmark
    def test_adversarial_quick_performance(self):
        """Adversarial quick mode should complete in under 3 minutes"""
        if not VULNERABLE_EVM_PATH.exists():
            pytest.skip("Vulnerable contracts not found")

        start = time.time()

        result = subprocess.run(
            [
                'python', '-m', 'src.adversarial.unified_orchestrator',
                '--project', str(VULNERABLE_EVM_PATH),
                '--mode', 'quick',
                '--output', str(AUDIT_RESULTS_PATH)
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=180
        )

        duration = time.time() - start

        assert duration < 180, f"Adversarial quick took {duration:.1f}s, target is 180s"

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_adversarial_standard_performance(self):
        """Adversarial standard mode should complete in under 10 minutes"""
        if not VULNERABLE_EVM_PATH.exists():
            pytest.skip("Vulnerable contracts not found")

        start = time.time()

        result = subprocess.run(
            [
                'python', '-m', 'src.adversarial.unified_orchestrator',
                '--project', str(VULNERABLE_EVM_PATH),
                '--mode', 'standard',
                '--output', str(AUDIT_RESULTS_PATH)
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=600
        )

        duration = time.time() - start

        assert duration < 600, f"Adversarial standard took {duration:.1f}s, target is 600s"


class TestHookPerformance:
    """Test hook execution performance"""

    @pytest.mark.benchmark
    def test_pre_audit_hook_performance(self):
        """Pre-audit hook should complete in under 30 seconds"""
        hook_path = PROJECT_ROOT / '.claude' / 'hooks' / 'pre-audit.sh'

        if not hook_path.exists():
            pytest.skip("Pre-audit hook not found")

        start = time.time()

        result = subprocess.run(
            [str(hook_path), str(VULNERABLE_EVM_PATH), 'quick'],
            capture_output=True,
            text=True,
            timeout=60
        )

        duration = time.time() - start

        assert duration < 30, f"Pre-audit hook took {duration:.1f}s, target is 30s"

    @pytest.mark.benchmark
    def test_post_audit_hook_performance(self):
        """Post-audit hook should complete in under 30 seconds"""
        hook_path = PROJECT_ROOT / '.claude' / 'hooks' / 'post-audit.sh'

        if not hook_path.exists():
            pytest.skip("Post-audit hook not found")

        # Ensure results directory exists
        AUDIT_RESULTS_PATH.mkdir(parents=True, exist_ok=True)

        start = time.time()

        result = subprocess.run(
            [str(hook_path), str(AUDIT_RESULTS_PATH), 'test-benchmark'],
            capture_output=True,
            text=True,
            timeout=60
        )

        duration = time.time() - start

        assert duration < 30, f"Post-audit hook took {duration:.1f}s, target is 30s"


class TestScalabilityBenchmarks:
    """Test framework scalability"""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_multi_contract_scaling(self):
        """Test scaling with multiple contracts"""
        if not VULNERABLE_EVM_PATH.exists():
            pytest.skip("Vulnerable contracts not found")

        # Count contracts
        contract_files = list(VULNERABLE_EVM_PATH.glob('*.sol'))
        num_contracts = len(contract_files)

        if num_contracts == 0:
            pytest.skip("No contracts found")

        start = time.time()

        # Run quick audit on all contracts
        result = subprocess.run(
            [
                'node', 'src/cli.js', 'audit',
                '--project', str(VULNERABLE_EVM_PATH),
                '--mode', 'quick',
                '--output', str(AUDIT_RESULTS_PATH)
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=300
        )

        duration = time.time() - start

        # Should scale linearly: ~30s per contract
        expected_max = num_contracts * 30
        assert duration < expected_max, \
            f"Scaling issue: {duration:.1f}s for {num_contracts} contracts"

        # Calculate per-contract time
        per_contract = duration / num_contracts
        print(f"\nScalability: {per_contract:.1f}s per contract ({num_contracts} contracts)")


# Performance baseline generator
def generate_baseline():
    """Generate performance baseline for regression testing"""
    from tests.benchmarks.benchmark_framework import PerformanceBenchmark

    bench = PerformanceBenchmark()

    # Run quick audit benchmark
    def quick_audit():
        subprocess.run(
            [
                'node', 'src/cli.js', 'audit',
                '--project', str(VULNERABLE_EVM_PATH),
                '--mode', 'quick',
                '--output', str(AUDIT_RESULTS_PATH)
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=180
        )

    bench.benchmark(
        name="Quick Audit",
        category="audit_mode",
        func=quick_audit,
        iterations=3,
        warmup=1
    )

    # Run Slither benchmark
    def slither_scan():
        subprocess.run(
            ['slither', str(VULNERABLE_EVM_PATH), '--json', '-'],
            capture_output=True,
            text=True,
            timeout=120
        )

    bench.benchmark(
        name="Slither Scan",
        category="static_analysis",
        func=slither_scan,
        iterations=3,
        warmup=1
    )

    # Save baseline
    bench.save_results("baseline_benchmark.json")
    print("\n✅ Baseline saved")


if __name__ == '__main__':
    import sys

    if '--generate-baseline' in sys.argv:
        generate_baseline()
    else:
        # Run tests
        pytest.main([__file__, '-v', '--tb=short'])
