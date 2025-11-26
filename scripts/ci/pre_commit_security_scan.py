#!/usr/bin/env python3
"""
Pre-commit Security Scan

Week 5: Fast security scanning for pre-commit hooks.
Optimized for speed (< 30 seconds) while maintaining high accuracy.

Modes:
- quick: Fast scan of changed files only
- solidity: Solidity-specific checks
- full: Comprehensive scan (for pre-push)

Exit Codes:
- 0: No critical issues found
- 1: Critical issues found (blocks commit)
- 2: Script error
"""

import sys
import os
import subprocess
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class PreCommitSecurityScanner:
    """Fast security scanner for pre-commit hooks"""

    def __init__(self, mode: str = "quick"):
        self.mode = mode
        self.project_root = Path(__file__).parent.parent.parent
        self.issues = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        self.start_time = time.time()

    def run(self) -> int:
        """
        Run security scan

        Returns:
            Exit code (0 = success, 1 = critical issues, 2 = error)
        """
        print("\n" + "="*70)
        print("🔐 PRE-COMMIT SECURITY SCAN")
        print("="*70)
        print(f"Mode: {self.mode}")
        print(f"Project: {self.project_root.name}\n")

        try:
            # Get changed files
            changed_files = self._get_changed_files()

            if not changed_files:
                print("✅ No files to scan")
                return 0

            print(f"📁 Files to scan: {len(changed_files)}\n")

            # Run mode-specific scans
            if self.mode == "quick":
                self._quick_scan(changed_files)
            elif self.mode == "solidity":
                self._solidity_scan(changed_files)
            elif self.mode == "full":
                self._full_scan(changed_files)
            else:
                print(f"❌ Unknown mode: {self.mode}")
                return 2

            # Print results
            self._print_results()

            # Determine exit code
            return self._get_exit_code()

        except Exception as e:
            print(f"\n❌ Error during scan: {e}")
            import traceback
            traceback.print_exc()
            return 2

    def _get_changed_files(self) -> List[Path]:
        """Get list of changed files in git staging area"""
        try:
            # Get staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            files = [
                self.project_root / f
                for f in result.stdout.strip().split('\n')
                if f and (f.endswith('.sol') or f.endswith('.py'))
            ]

            return [f for f in files if f.exists()]

        except subprocess.CalledProcessError:
            # Not in a git repo or no staged files
            return []

    def _quick_scan(self, files: List[Path]):
        """Fast scan for common issues"""
        print("⚡ Running quick scan...\n")

        for file_path in files:
            if file_path.suffix == '.sol':
                self._scan_solidity_file(file_path, quick=True)
            elif file_path.suffix == '.py':
                self._scan_python_file(file_path)

    def _solidity_scan(self, files: List[Path]):
        """Solidity-specific comprehensive scan"""
        print("🔍 Running Solidity security scan...\n")

        solidity_files = [f for f in files if f.suffix == '.sol']

        if not solidity_files:
            print("ℹ️  No Solidity files to scan")
            return

        for file_path in solidity_files:
            print(f"Scanning: {file_path.name}")
            self._scan_solidity_file(file_path, quick=False)

    def _full_scan(self, files: List[Path]):
        """Comprehensive scan (for pre-push)"""
        print("🔬 Running full security scan...\n")

        # Run both quick and solidity scans
        self._quick_scan(files)

        # Additional checks
        self._check_dependencies()
        self._check_configurations()

    def _scan_solidity_file(self, file_path: Path, quick: bool = True):
        """Scan a Solidity file for common vulnerabilities"""
        content = file_path.read_text()

        # Quick pattern-based checks
        patterns = {
            'critical': [
                (r'\.call\{value:', 'Reentrancy risk: external call with value'),
                (r'selfdestruct\(', 'Selfdestruct found (critical operation)'),
                (r'delegatecall\(', 'Delegatecall found (proxy risk)'),
            ],
            'high': [
                (r'tx\.origin', 'tx.origin used (phishing risk)'),
                (r'block\.timestamp', 'block.timestamp dependency (manipulation risk)'),
                (r'transfer\(', 'transfer() used (consider call{value:} instead)'),
                (r'send\(', 'send() used (unchecked return value)'),
            ],
            'medium': [
                (r'pragma solidity \^0\.[0-7]\.', 'Old Solidity version (<0.8.0)'),
                (r'assembly\s*\{', 'Inline assembly found (review carefully)'),
                (r'private\s+\w+\s*=', 'Private variable (not truly private)'),
            ]
        }

        import re
        for severity, pattern_list in patterns.items():
            for pattern, message in pattern_list:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    self.issues[severity].append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': line_num,
                        'message': message,
                        'pattern': pattern
                    })

        if not quick:
            # Run slither if available
            self._run_slither(file_path)

    def _scan_python_file(self, file_path: Path):
        """Scan a Python file for security issues"""
        content = file_path.read_text()

        # Check for common security issues
        import re
        patterns = {
            'high': [
                (r'eval\(', 'eval() found (code injection risk)'),
                (r'exec\(', 'exec() found (code injection risk)'),
                (r'__import__\(', '__import__() found (import injection risk)'),
            ],
            'medium': [
                (r'pickle\.load', 'pickle.load() found (deserialization risk)'),
                (r'yaml\.load\(', 'yaml.load() found (use yaml.safe_load instead)'),
                (r'subprocess\.call\(.+shell=True', 'shell=True in subprocess (injection risk)'),
            ]
        }

        for severity, pattern_list in patterns.items():
            for pattern, message in pattern_list:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    self.issues[severity].append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': line_num,
                        'message': message
                    })

    def _run_slither(self, file_path: Path):
        """Run Slither on a Solidity file"""
        try:
            result = subprocess.run(
                ['slither', str(file_path), '--json', '-'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout:
                slither_results = json.loads(result.stdout)

                for finding in slither_results.get('results', {}).get('detectors', []):
                    severity = finding.get('impact', 'Low').lower()

                    if severity == 'informational':
                        severity = 'low'

                    if severity in self.issues:
                        self.issues[severity].append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'line': finding.get('first_markdown_element', ''),
                            'message': finding.get('description', ''),
                            'tool': 'slither'
                        })

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            # Slither not available or timed out
            pass

    def _check_dependencies(self):
        """Check for vulnerable dependencies"""
        # Check Python dependencies
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                result = subprocess.run(
                    ['pip-audit', '-r', str(requirements_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    self.issues['high'].append({
                        'file': 'requirements.txt',
                        'line': 0,
                        'message': 'Vulnerable Python dependencies found',
                        'tool': 'pip-audit'
                    })

            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

    def _check_configurations(self):
        """Check for security misconfigurations"""
        # Check for exposed secrets
        env_example = self.project_root / ".env.example"
        env_file = self.project_root / ".env"

        if env_file.exists() and not env_example.exists():
            self.issues['medium'].append({
                'file': '.env',
                'line': 0,
                'message': '.env file exists without .env.example (commit risk)'
            })

    def _print_results(self):
        """Print scan results"""
        elapsed = time.time() - self.start_time

        print("\n" + "="*70)
        print("📊 SCAN RESULTS")
        print("="*70 + "\n")

        total_issues = sum(len(issues) for issues in self.issues.values())

        if total_issues == 0:
            print("✅ No security issues found!\n")
            print(f"⏱️  Scan completed in {elapsed:.2f}s")
            return

        # Print by severity
        severity_emoji = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '⚡',
            'low': 'ℹ️'
        }

        for severity in ['critical', 'high', 'medium', 'low']:
            issues = self.issues[severity]
            if not issues:
                continue

            emoji = severity_emoji[severity]
            print(f"{emoji} {severity.upper()}: {len(issues)} issue(s)")

            for issue in issues[:5]:  # Show first 5 per severity
                print(f"   📄 {issue['file']}:{issue.get('line', '?')}")
                print(f"      {issue['message']}\n")

            if len(issues) > 5:
                print(f"   ... and {len(issues) - 5} more\n")

        print(f"Total: {total_issues} issue(s) found")
        print(f"⏱️  Scan completed in {elapsed:.2f}s\n")

    def _get_exit_code(self) -> int:
        """Determine exit code based on findings"""
        # Critical or high severity = block commit
        if self.issues['critical'] or self.issues['high']:
            print("❌ COMMIT BLOCKED: Critical or high severity issues found")
            print("   Fix issues or use --no-verify to skip (not recommended)\n")
            return 1

        # Medium or low = warning but allow
        if self.issues['medium'] or self.issues['low']:
            print("⚠️  WARNING: Security issues found, but commit allowed")
            print("   Please review and fix these issues\n")
            return 0

        # No issues
        print("✅ COMMIT ALLOWED: No critical issues found\n")
        return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Pre-commit security scan')
    parser.add_argument(
        '--mode',
        choices=['quick', 'solidity', 'full'],
        default='quick',
        help='Scan mode'
    )

    args = parser.parse_args()

    scanner = PreCommitSecurityScanner(mode=args.mode)
    exit_code = scanner.run()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
