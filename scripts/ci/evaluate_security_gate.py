#!/usr/bin/env python3
"""
Security Gate Evaluator

Week 5: Evaluates security findings against gate thresholds.
Determines if PR/deployment should be blocked.

Exit Codes:
- 0: Passed all gates
- 1: Failed one or more gates
- 2: Error during evaluation
"""

import sys
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class GateResult:
    """Result of gate evaluation"""
    passed: bool
    gate_name: str
    severity: str
    threshold: int
    actual: int
    message: str
    should_block_pr: bool
    should_block_deploy: bool
    notifications: List[str]


class SecurityGateEvaluator:
    """Evaluates security findings against configured gates"""

    def __init__(self, gate_config_path: Path):
        self.config = self._load_config(gate_config_path)
        self.results: List[GateResult] = []

    def _load_config(self, path: Path) -> Dict:
        """Load gate configuration"""
        with open(path) as f:
            return yaml.safe_load(f)

    def evaluate(self, security_report_path: Path) -> bool:
        """
        Evaluate security report against gates

        Returns:
            True if all gates passed, False otherwise
        """
        print("\n" + "="*70)
        print("🚦 SECURITY GATE EVALUATION")
        print("="*70)
        print(f"Config: {self.config.get('name', 'Unknown')}")
        print(f"Mode: {self.config['settings']['mode']}\n")

        # Load security report
        with open(security_report_path) as f:
            report = json.load(f)

        # Evaluate severity thresholds
        self._evaluate_severity_thresholds(report)

        # Evaluate vulnerability types
        self._evaluate_vulnerability_types(report)

        # Evaluate adversarial results (Week 4)
        if 'adversarial' in report:
            self._evaluate_adversarial_results(report['adversarial'])

        # Evaluate code quality
        if 'code_quality' in report:
            self._evaluate_code_quality(report['code_quality'])

        # Print results
        self._print_results()

        # Determine final status
        all_passed = all(r.passed for r in self.results)

        if all_passed:
            print("\n✅ ALL SECURITY GATES PASSED")
            return True
        else:
            print("\n❌ SECURITY GATE FAILED")

            # Check if should block
            should_block_pr = any(r.should_block_pr for r in self.results if not r.passed)
            should_block_deploy = any(r.should_block_deploy for r in self.results if not r.passed)

            if should_block_pr:
                print("   🚫 PR BLOCKED")
            if should_block_deploy:
                print("   🚫 DEPLOYMENT BLOCKED")

            return False

    def _evaluate_severity_thresholds(self, report: Dict):
        """Evaluate findings by severity"""
        severity_counts = report.get('summary', {}).get('by_severity', {})

        for severity in ['critical', 'high', 'medium', 'low']:
            config = self.config.get(severity, {})
            max_count = config.get('max_count', 999)
            actual = severity_counts.get(severity, 0)

            passed = actual <= max_count

            result = GateResult(
                passed=passed,
                gate_name=f"{severity.upper()} Severity",
                severity=severity,
                threshold=max_count,
                actual=actual,
                message=config.get('message', ''),
                should_block_pr=config.get('block_pr', False),
                should_block_deploy=config.get('block_deploy', False),
                notifications=config.get('notify', [])
            )

            self.results.append(result)

    def _evaluate_vulnerability_types(self, report: Dict):
        """Evaluate specific vulnerability types"""
        vuln_types_config = self.config.get('vulnerability_types', {})
        findings = report.get('findings', [])

        for vuln_type, config in vuln_types_config.items():
            categories = config.get('categories', [])
            max_count = config.get('max_count', 0)

            # Count findings matching categories
            matching = [
                f for f in findings
                if f.get('type', '').lower() in [c.lower() for c in categories]
            ]

            actual = len(matching)
            passed = actual <= max_count

            result = GateResult(
                passed=passed,
                gate_name=f"{vuln_type.replace('_', ' ').title()}",
                severity=config.get('severity', 'medium'),
                threshold=max_count,
                actual=actual,
                message=f"Found {actual} {vuln_type} vulnerabilities",
                should_block_pr=True if config['severity'] in ['critical', 'high'] else False,
                should_block_deploy=True,
                notifications=['github']
            )

            if not passed:
                self.results.append(result)

    def _evaluate_adversarial_results(self, adversarial: Dict):
        """Evaluate Week 4 adversarial testing results"""
        adv_config = self.config.get('adversarial', {})

        # Check successful attacks
        successful_attacks = adversarial.get('successful_attacks', [])
        max_attacks = adv_config.get('successful_attacks', {}).get('max_count', 0)
        min_profit = adv_config.get('successful_attacks', {}).get('min_profit_usd', 100)

        # Filter by profit threshold
        profitable_attacks = [
            a for a in successful_attacks
            if a.get('net_profit_usd', 0) > min_profit
        ]

        passed = len(profitable_attacks) <= max_attacks

        result = GateResult(
            passed=passed,
            gate_name="Successful Attacks",
            severity="critical",
            threshold=max_attacks,
            actual=len(profitable_attacks),
            message=f"Adversarial tests: {len(profitable_attacks)} successful attacks",
            should_block_pr=True,
            should_block_deploy=True,
            notifications=['slack', 'github']
        )

        self.results.append(result)

        # Check invariant violations
        violations = adversarial.get('invariant_violations', [])
        critical_violations = [v for v in violations if v.get('severity') == 'critical']
        high_violations = [v for v in violations if v.get('severity') == 'high']

        inv_config = adv_config.get('invariant_violations', {})
        max_critical = inv_config.get('critical_max', 0)
        max_high = inv_config.get('high_max', 1)

        passed_critical = len(critical_violations) <= max_critical
        passed_high = len(high_violations) <= max_high

        if not passed_critical or not passed_high:
            result = GateResult(
                passed=False,
                gate_name="Protocol Invariants",
                severity="critical" if not passed_critical else "high",
                threshold=max_critical if not passed_critical else max_high,
                actual=len(critical_violations) if not passed_critical else len(high_violations),
                message=f"Invariant violations: {len(critical_violations)} critical, {len(high_violations)} high",
                should_block_pr=True,
                should_block_deploy=True,
                notifications=['slack', 'github']
            )

            self.results.append(result)

    def _evaluate_code_quality(self, quality: Dict):
        """Evaluate code quality metrics"""
        quality_config = self.config.get('code_quality', {})

        # Test coverage
        coverage_config = quality_config.get('test_coverage', {})
        min_line_coverage = coverage_config.get('min_line_coverage', 80)
        min_branch_coverage = coverage_config.get('min_branch_coverage', 70)

        actual_line = quality.get('line_coverage', 0)
        actual_branch = quality.get('branch_coverage', 0)

        if actual_line < min_line_coverage:
            result = GateResult(
                passed=False,
                gate_name="Test Coverage (Line)",
                severity="medium",
                threshold=min_line_coverage,
                actual=actual_line,
                message=f"Line coverage {actual_line}% < {min_line_coverage}%",
                should_block_pr=coverage_config.get('block_pr', True),
                should_block_deploy=False,
                notifications=['github']
            )

            self.results.append(result)

    def _print_results(self):
        """Print evaluation results"""
        print("\n📊 Gate Evaluation Results:\n")

        # Group by status
        failed = [r for r in self.results if not r.passed]
        passed = [r for r in self.results if r.passed]

        if failed:
            print("❌ FAILED GATES:")
            for result in failed:
                emoji = {
                    'critical': '🚨',
                    'high': '⚠️',
                    'medium': '⚡',
                    'low': 'ℹ️'
                }.get(result.severity, '❓')

                print(f"\n  {emoji} {result.gate_name}")
                print(f"     Threshold: {result.threshold}")
                print(f"     Actual: {result.actual}")
                print(f"     Message: {result.message}")

                if result.should_block_pr:
                    print(f"     🚫 BLOCKS PR")
                if result.should_block_deploy:
                    print(f"     🚫 BLOCKS DEPLOYMENT")

        if passed:
            print(f"\n✅ PASSED GATES ({len(passed)}):")
            for result in passed:
                print(f"   • {result.gate_name}: {result.actual}/{result.threshold}")

        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Evaluate security gate')
    parser.add_argument('--report', required=True, help='Security report JSON file')
    parser.add_argument('--config', default='.github/security-gate.yml', help='Gate config file')

    args = parser.parse_args()

    report_path = Path(args.report)
    config_path = Path(args.config)

    if not report_path.exists():
        print(f"❌ Error: Report not found: {report_path}")
        sys.exit(2)

    if not config_path.exists():
        print(f"❌ Error: Config not found: {config_path}")
        sys.exit(2)

    evaluator = SecurityGateEvaluator(config_path)
    passed = evaluator.evaluate(report_path)

    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
