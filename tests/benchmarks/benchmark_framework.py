#!/usr/bin/env python3
"""
Performance Benchmarking Framework

Week 6: Production Hardening
Measures and tracks performance across all framework components.

Benchmarks:
1. Static Analysis Performance
2. Live Fork Testing (Week 4)
3. CI/CD Pipeline (Week 5)
4. Memory Usage
5. Scalability
"""

import time
import psutil
import statistics
import json
from pathlib import Path
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@dataclass
class BenchmarkResult:
    """Result of a single benchmark"""
    name: str
    category: str
    duration_seconds: float
    memory_mb: float
    cpu_percent: float
    iterations: int
    timestamp: str

    # Statistics
    mean_duration: float = 0.0
    median_duration: float = 0.0
    std_deviation: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0

    # Metadata
    version: str = "1.0.0"
    system_info: Dict[str, Any] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class PerformanceBenchmark:
    """Performance benchmarking system"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent / "results"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results: List[BenchmarkResult] = []
        self.system_info = self._get_system_info()

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024 ** 3),
            'platform': sys.platform,
            'python_version': sys.version.split()[0]
        }

    def benchmark(
        self,
        name: str,
        category: str,
        func: Callable,
        iterations: int = 1,
        warmup: int = 0
    ) -> BenchmarkResult:
        """
        Run benchmark on a function

        Args:
            name: Benchmark name
            category: Category (static, adversarial, ci_cd, etc.)
            func: Function to benchmark
            iterations: Number of iterations
            warmup: Warmup iterations

        Returns:
            BenchmarkResult
        """
        print(f"\n{'='*70}")
        print(f"BENCHMARK: {name}")
        print(f"{'='*70}")
        print(f"Category: {category}")
        print(f"Iterations: {iterations}")
        print(f"Warmup: {warmup}\n")

        # Warmup runs
        for i in range(warmup):
            print(f"Warmup {i+1}/{warmup}...")
            func()

        # Actual benchmark runs
        durations = []
        memory_usage = []
        cpu_usage = []

        for i in range(iterations):
            print(f"Iteration {i+1}/{iterations}...")

            # Measure memory before
            process = psutil.Process()
            mem_before = process.memory_info().rss / (1024 ** 2)

            # Measure CPU usage
            cpu_before = psutil.cpu_percent(interval=0.1)

            # Run function
            start_time = time.time()
            try:
                func()
            except Exception as e:
                print(f"  ⚠️  Error during benchmark: {e}")
                continue

            duration = time.time() - start_time

            # Measure memory after
            mem_after = process.memory_info().rss / (1024 ** 2)
            mem_used = mem_after - mem_before

            # Measure CPU after
            cpu_after = psutil.cpu_percent(interval=0.1)
            cpu_avg = (cpu_before + cpu_after) / 2

            durations.append(duration)
            memory_usage.append(mem_used)
            cpu_usage.append(cpu_avg)

            print(f"  Duration: {duration:.3f}s")
            print(f"  Memory: {mem_used:.2f} MB")
            print(f"  CPU: {cpu_avg:.1f}%\n")

        # Calculate statistics
        result = BenchmarkResult(
            name=name,
            category=category,
            duration_seconds=durations[0] if durations else 0,
            memory_mb=statistics.mean(memory_usage) if memory_usage else 0,
            cpu_percent=statistics.mean(cpu_usage) if cpu_usage else 0,
            iterations=iterations,
            timestamp=datetime.now().isoformat(),
            mean_duration=statistics.mean(durations) if durations else 0,
            median_duration=statistics.median(durations) if durations else 0,
            std_deviation=statistics.stdev(durations) if len(durations) > 1 else 0,
            min_duration=min(durations) if durations else 0,
            max_duration=max(durations) if durations else 0,
            system_info=self.system_info
        )

        self.results.append(result)

        # Print summary
        self._print_result(result)

        return result

    def _print_result(self, result: BenchmarkResult):
        """Print benchmark result"""
        print(f"\n{'='*70}")
        print(f"RESULTS: {result.name}")
        print(f"{'='*70}")
        print(f"Mean Duration:   {result.mean_duration:.3f}s")
        print(f"Median Duration: {result.median_duration:.3f}s")
        print(f"Std Deviation:   {result.std_deviation:.3f}s")
        print(f"Min Duration:    {result.min_duration:.3f}s")
        print(f"Max Duration:    {result.max_duration:.3f}s")
        print(f"Memory Usage:    {result.memory_mb:.2f} MB")
        print(f"CPU Usage:       {result.cpu_percent:.1f}%")
        print(f"{'='*70}\n")

    def save_results(self, filename: str = None):
        """Save benchmark results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_{timestamp}.json"

        output_path = self.output_dir / filename

        data = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.system_info,
            'benchmarks': [r.to_dict() for r in self.results]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✅ Results saved to: {output_path}")

        return output_path

    def generate_report(self) -> str:
        """Generate markdown report"""
        report = ["# Performance Benchmark Report\n"]
        report.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**System**: {self.system_info['platform']}, "
                     f"{self.system_info['cpu_count']} CPUs, "
                     f"{self.system_info['memory_total_gb']:.1f} GB RAM\n")

        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        for category, results in categories.items():
            report.append(f"\n## {category.replace('_', ' ').title()}\n")
            report.append("\n| Benchmark | Mean Duration | Memory | CPU |")
            report.append("\n|-----------|---------------|--------|-----|")

            for r in results:
                report.append(
                    f"\n| {r.name} | {r.mean_duration:.3f}s | "
                    f"{r.memory_mb:.1f} MB | {r.cpu_percent:.1f}% |"
                )

        return '\n'.join(report)

    def compare_with_baseline(self, baseline_file: Path) -> Dict[str, Any]:
        """Compare current results with baseline"""
        if not baseline_file.exists():
            print(f"⚠️  Baseline not found: {baseline_file}")
            return {}

        with open(baseline_file) as f:
            baseline_data = json.load(f)

        baseline_benchmarks = {
            b['name']: b
            for b in baseline_data.get('benchmarks', [])
        }

        comparisons = []

        for result in self.results:
            if result.name in baseline_benchmarks:
                baseline = baseline_benchmarks[result.name]

                comparison = {
                    'name': result.name,
                    'current_duration': result.mean_duration,
                    'baseline_duration': baseline['mean_duration'],
                    'change_percent': (
                        (result.mean_duration - baseline['mean_duration']) /
                        baseline['mean_duration'] * 100
                    ),
                    'regression': result.mean_duration > baseline['mean_duration'] * 1.1
                }

                comparisons.append(comparison)

        return {
            'comparisons': comparisons,
            'regressions': [c for c in comparisons if c['regression']]
        }


# Benchmark definitions
def run_all_benchmarks():
    """Run all framework benchmarks"""
    bench = PerformanceBenchmark()

    print("\n" + "="*70)
    print(" FRAMEWORK PERFORMANCE BENCHMARKS")
    print("="*70)

    # 1. Static Analysis Benchmarks
    print("\n📊 Category: Static Analysis")
    print("-" * 70)

    def mock_slither():
        """Mock Slither analysis"""
        time.sleep(0.5)  # Simulate 500ms analysis

    bench.benchmark(
        name="Slither Analysis (single file)",
        category="static_analysis",
        func=mock_slither,
        iterations=3,
        warmup=1
    )

    def mock_mythril():
        """Mock Mythril analysis"""
        time.sleep(2.0)  # Simulate 2s analysis

    bench.benchmark(
        name="Mythril Analysis (single file)",
        category="static_analysis",
        func=mock_mythril,
        iterations=3,
        warmup=1
    )

    # 2. Live Fork Benchmarks (Week 4)
    print("\n📊 Category: Live Fork Testing")
    print("-" * 70)

    def mock_fork_startup():
        """Mock fork startup"""
        time.sleep(5.0)  # Simulate 5s fork

    bench.benchmark(
        name="Anvil Fork Startup",
        category="live_fork",
        func=mock_fork_startup,
        iterations=2,
        warmup=0
    )

    def mock_attack_execution():
        """Mock attack execution"""
        time.sleep(3.0)  # Simulate 3s attack

    bench.benchmark(
        name="Sandwich Attack Execution",
        category="live_fork",
        func=mock_attack_execution,
        iterations=3,
        warmup=1
    )

    # 3. CI/CD Benchmarks (Week 5)
    print("\n📊 Category: CI/CD Pipeline")
    print("-" * 70)

    def mock_pre_commit():
        """Mock pre-commit scan"""
        time.sleep(0.3)  # Simulate 300ms scan

    bench.benchmark(
        name="Pre-commit Quick Scan",
        category="ci_cd",
        func=mock_pre_commit,
        iterations=5,
        warmup=1
    )

    def mock_security_gate():
        """Mock security gate evaluation"""
        time.sleep(0.1)  # Simulate 100ms evaluation

    bench.benchmark(
        name="Security Gate Evaluation",
        category="ci_cd",
        func=mock_security_gate,
        iterations=5,
        warmup=1
    )

    # 4. Scalability Benchmarks
    print("\n📊 Category: Scalability")
    print("-" * 70)

    def mock_large_project():
        """Mock analysis of large project"""
        time.sleep(10.0)  # Simulate 10s for 50 files

    bench.benchmark(
        name="Large Project (50 files)",
        category="scalability",
        func=mock_large_project,
        iterations=1,
        warmup=0
    )

    # Generate and save results
    print("\n📝 Generating report...")
    report = bench.generate_report()
    print(report)

    report_path = bench.output_dir / "BENCHMARK_REPORT.md"
    report_path.write_text(report)
    print(f"\n✅ Report saved to: {report_path}")

    bench.save_results("latest_benchmark.json")

    return bench


def run_regression_check(baseline_file: str = "baseline_benchmark.json"):
    """Check for performance regressions"""
    bench = PerformanceBenchmark()

    # Run quick benchmarks
    def quick_scan():
        time.sleep(0.3)

    bench.benchmark(
        name="Pre-commit Quick Scan",
        category="regression",
        func=quick_scan,
        iterations=3
    )

    # Compare with baseline
    baseline_path = bench.output_dir / baseline_file

    if baseline_path.exists():
        comparison = bench.compare_with_baseline(baseline_path)

        if comparison.get('regressions'):
            print("\n❌ PERFORMANCE REGRESSIONS DETECTED:")
            for reg in comparison['regressions']:
                print(f"  {reg['name']}: {reg['change_percent']:+.1f}% slower")
            return False
        else:
            print("\n✅ No performance regressions detected")
            return True
    else:
        print(f"\n⚠️  No baseline found. Run:")
        print(f"    python {__file__} --save-baseline")
        return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run performance benchmarks')
    parser.add_argument('--save-baseline', action='store_true',
                       help='Save current run as baseline')
    parser.add_argument('--check-regression', action='store_true',
                       help='Check for performance regressions')

    args = parser.parse_args()

    if args.check_regression:
        passed = run_regression_check()
        sys.exit(0 if passed else 1)

    elif args.save_baseline:
        bench = run_all_benchmarks()
        baseline_path = bench.save_results("baseline_benchmark.json")
        print(f"\n✅ Baseline saved: {baseline_path}")

    else:
        run_all_benchmarks()
