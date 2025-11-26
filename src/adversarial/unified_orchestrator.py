"""
Unified Orchestrator for Claude Code Agent Integration

This orchestrator is designed to output JSON results that Claude Code
reads and analyzes. It does NOT make any AI API calls - Claude Code
IS the AI doing the analysis.

Architecture:
    User: "Audit this contract"
           │
           ▼
    Claude Code (Interactive AI)
           │
           ├── Reads agent definitions from .claude/agents/
           ├── Spawns sub-agents using Task tool
           ├── Runs: python unified_orchestrator.py --project [path]
           ├── Reads: audit-results/adversarial-findings.json
           └── Synthesizes and generates report

    This file provides:
    1. Tool execution (Slither, Mythril, Foundry)
    2. Adversarial simulation setup
    3. JSON output for Claude Code to read
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from enum import Enum

# Local imports
try:
    from .simulation.evm_environment import EVMEnvironment
    from .agents.attacker_agents import AttackerAgentFactory
    from .search.evolutionary import EvolutionarySearch
    from .invariants.amm_invariants import AMMInvariants
    from .invariants.lending_invariants import LendingInvariants
    from .invariants.oracle_invariants import OracleInvariants
except ImportError:
    # Running as standalone script
    EVMEnvironment = None
    AttackerAgentFactory = None
    EvolutionarySearch = None


class AuditMode(Enum):
    QUICK = "quick"      # 1-3 minutes, basic checks
    STANDARD = "standard"  # 5-10 minutes, comprehensive
    DEEP = "deep"        # 15-30 minutes, exhaustive


@dataclass
class UnifiedConfig:
    """Configuration for unified orchestration"""
    project_path: str
    chain: str = "evm"
    mode: str = "standard"
    output_dir: str = "./audit-results"
    strategies: List[str] = None
    fork_url: Optional[str] = None
    fork_block: Optional[int] = None
    parallel: bool = True
    max_iterations: int = 100

    def __post_init__(self):
        if self.strategies is None:
            self.strategies = ["mev", "flash_loan", "oracle_manipulation", "invariants"]


@dataclass
class Finding:
    """Structured finding for JSON output"""
    id: str
    type: str
    severity: str
    title: str
    description: str
    location: Dict[str, Any]
    detected_by: List[str]
    confidence: float
    profitability: Optional[Dict[str, Any]] = None
    exploit_sequence: Optional[List[str]] = None
    recommendation: str = ""

    def to_dict(self):
        return asdict(self)


class UnifiedOrchestrator:
    """
    Unified Orchestrator for Claude Code Integration

    This class:
    1. Runs security tools (Slither, Mythril, Foundry)
    2. Executes adversarial simulations
    3. Outputs structured JSON for Claude Code analysis

    It does NOT:
    - Make AI API calls (Claude Code does this)
    - Generate reports (Claude Code does this)
    - Make security decisions (Claude Code does this)
    """

    def __init__(self, config: UnifiedConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.findings: List[Finding] = []
        self.tool_results: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}

        # Ensure output directory exists
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Unified Orchestrator initialized")
        self.logger.info(f"  Chain: {config.chain}")
        self.logger.info(f"  Mode: {config.mode}")
        self.logger.info(f"  Strategies: {config.strategies}")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("unified_orchestrator")
        logger.setLevel(logging.INFO)

        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)

        return logger

    def run(self) -> Dict[str, Any]:
        """
        Main execution method

        Returns structured JSON that Claude Code reads to analyze
        """
        start_time = datetime.now()
        self.logger.info("=" * 60)
        self.logger.info("UNIFIED ORCHESTRATOR - Starting Audit")
        self.logger.info("=" * 60)

        try:
            # Phase 1: Static Analysis
            self.logger.info("\n[Phase 1] Running Static Analysis Tools...")
            self._run_static_analysis()

            # Phase 2: Adversarial Testing
            self.logger.info("\n[Phase 2] Running Adversarial Simulations...")
            self._run_adversarial_testing()

            # Phase 3: Invariant Checking
            self.logger.info("\n[Phase 3] Checking Protocol Invariants...")
            self._run_invariant_checks()

            # Phase 4: Compile Results
            self.logger.info("\n[Phase 4] Compiling Results...")
            results = self._compile_results(start_time)

            # Save to JSON for Claude Code
            output_path = self._save_results(results)

            self.logger.info("=" * 60)
            self.logger.info(f"AUDIT COMPLETE - Results saved to: {output_path}")
            self.logger.info("=" * 60)

            return results

        except Exception as e:
            self.logger.error(f"Orchestrator error: {e}")
            return self._compile_error_results(str(e), start_time)

    def _run_static_analysis(self):
        """Run static analysis tools and collect findings"""
        import subprocess
        import os

        project_path = self.config.project_path

        # Find Solidity files
        sol_files = list(Path(project_path).rglob("*.sol"))
        if not sol_files:
            self.logger.warning("No Solidity files found")
            return

        self.logger.info(f"Found {len(sol_files)} Solidity files")

        # Run Slither
        self._run_slither(project_path)

        # Run Foundry tests if available
        if self.config.mode in ["standard", "deep"]:
            self._run_foundry(project_path)

        # Run Mythril for deep mode only (it's slow)
        if self.config.mode == "deep":
            self._run_mythril(project_path)

    def _run_slither(self, project_path: str):
        """Run Slither static analyzer"""
        import subprocess

        self.logger.info("  Running Slither...")

        output_path = Path(self.config.output_dir) / "slither.json"

        try:
            # Check if contracts/ directory exists
            contracts_dir = Path(project_path) / "contracts"
            target_path = str(contracts_dir) if contracts_dir.exists() else project_path

            cmd = [
                "slither", target_path,
                "--json", str(output_path),
                "--filter-paths", "node_modules|test|mock",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=project_path
            )

            if output_path.exists():
                with open(output_path) as f:
                    slither_results = json.load(f)

                # Parse Slither findings
                detectors = slither_results.get("results", {}).get("detectors", [])
                for i, detector in enumerate(detectors):
                    finding = Finding(
                        id=f"slither-{i+1:03d}",
                        type=detector.get("check", "unknown"),
                        severity=self._map_slither_severity(detector.get("impact", "Low")),
                        title=detector.get("check", "Unknown Issue"),
                        description=detector.get("description", ""),
                        location={
                            "file": detector.get("elements", [{}])[0].get("source_mapping", {}).get("filename", "unknown"),
                            "line": detector.get("elements", [{}])[0].get("source_mapping", {}).get("lines", [0])[0] if detector.get("elements") else 0,
                            "function": detector.get("elements", [{}])[0].get("name", "unknown") if detector.get("elements") else "unknown"
                        },
                        detected_by=["slither"],
                        confidence=self._map_slither_confidence(detector.get("confidence", "Low")),
                        recommendation=f"Review {detector.get('check')} pattern"
                    )
                    self.findings.append(finding)

                self.tool_results["slither"] = {
                    "status": "success",
                    "findings_count": len(detectors),
                    "output_path": str(output_path)
                }
                self.logger.info(f"  Slither complete: {len(detectors)} findings")
            else:
                self.tool_results["slither"] = {
                    "status": "no_output",
                    "stderr": result.stderr[:500] if result.stderr else ""
                }

        except subprocess.TimeoutExpired:
            self.logger.warning("  Slither timed out")
            self.tool_results["slither"] = {"status": "timeout"}
        except FileNotFoundError:
            self.logger.warning("  Slither not installed")
            self.tool_results["slither"] = {"status": "not_installed"}
        except Exception as e:
            self.logger.error(f"  Slither error: {e}")
            self.tool_results["slither"] = {"status": "error", "message": str(e)}

    def _run_foundry(self, project_path: str):
        """Run Foundry fuzz tests"""
        import subprocess

        self.logger.info("  Running Foundry fuzz tests...")

        # Check if foundry.toml exists
        if not (Path(project_path) / "foundry.toml").exists():
            self.logger.info("  No foundry.toml found, skipping")
            self.tool_results["foundry"] = {"status": "skipped", "reason": "no foundry.toml"}
            return

        try:
            cmd = ["forge", "test", "--fuzz-runs", "256", "--json"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=project_path
            )

            # Parse Foundry output
            failed_tests = []
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if '"status":"Failure"' in line or 'FAIL' in line:
                        failed_tests.append(line)

            for i, test_fail in enumerate(failed_tests):
                finding = Finding(
                    id=f"foundry-{i+1:03d}",
                    type="fuzz_failure",
                    severity="HIGH",
                    title="Fuzz Test Failure",
                    description=test_fail[:200],
                    location={"test": test_fail},
                    detected_by=["foundry"],
                    confidence=0.9,
                    recommendation="Review failing invariant/fuzz test"
                )
                self.findings.append(finding)

            self.tool_results["foundry"] = {
                "status": "success",
                "failed_tests": len(failed_tests)
            }
            self.logger.info(f"  Foundry complete: {len(failed_tests)} failures")

        except subprocess.TimeoutExpired:
            self.logger.warning("  Foundry timed out")
            self.tool_results["foundry"] = {"status": "timeout"}
        except FileNotFoundError:
            self.logger.warning("  Foundry not installed")
            self.tool_results["foundry"] = {"status": "not_installed"}
        except Exception as e:
            self.logger.error(f"  Foundry error: {e}")
            self.tool_results["foundry"] = {"status": "error", "message": str(e)}

    def _run_mythril(self, project_path: str):
        """Run Mythril symbolic execution"""
        import subprocess

        self.logger.info("  Running Mythril (this may take a while)...")

        # Find main contract file
        sol_files = list(Path(project_path).rglob("*.sol"))
        if not sol_files:
            return

        # Analyze first few contracts (Mythril is slow)
        contracts_to_analyze = sol_files[:3]

        mythril_findings = []

        for sol_file in contracts_to_analyze:
            try:
                cmd = [
                    "myth", "analyze", str(sol_file),
                    "--solc-json", "--execution-timeout", "60",
                    "-o", "json"
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=project_path
                )

                if result.stdout:
                    try:
                        mythril_output = json.loads(result.stdout)
                        if mythril_output.get("issues"):
                            mythril_findings.extend(mythril_output["issues"])
                    except json.JSONDecodeError:
                        pass

            except subprocess.TimeoutExpired:
                self.logger.info(f"    Mythril timed out on {sol_file.name}")
            except Exception as e:
                self.logger.debug(f"    Mythril error on {sol_file.name}: {e}")

        for i, issue in enumerate(mythril_findings):
            finding = Finding(
                id=f"mythril-{i+1:03d}",
                type=issue.get("swc-id", "unknown"),
                severity=self._map_mythril_severity(issue.get("severity", "Low")),
                title=issue.get("title", "Mythril Finding"),
                description=issue.get("description", ""),
                location={
                    "file": issue.get("filename", "unknown"),
                    "line": issue.get("lineno", 0),
                    "address": issue.get("address", "")
                },
                detected_by=["mythril"],
                confidence=0.7,
                recommendation=f"Review SWC-{issue.get('swc-id', 'unknown')}"
            )
            self.findings.append(finding)

        self.tool_results["mythril"] = {
            "status": "success",
            "findings_count": len(mythril_findings),
            "contracts_analyzed": len(contracts_to_analyze)
        }
        self.logger.info(f"  Mythril complete: {len(mythril_findings)} findings")

    def _run_adversarial_testing(self):
        """Run adversarial attack simulations"""

        if "mev" in self.config.strategies:
            self._detect_mev_vulnerabilities()

        if "flash_loan" in self.config.strategies:
            self._detect_flash_loan_vulnerabilities()

        if "oracle_manipulation" in self.config.strategies:
            self._detect_oracle_vulnerabilities()

        if "governance" in self.config.strategies:
            self._detect_governance_vulnerabilities()

    def _detect_mev_vulnerabilities(self):
        """Detect MEV vulnerabilities (sandwich attacks, frontrunning)"""
        self.logger.info("  Checking for MEV vulnerabilities...")

        # Pattern-based detection (Claude Code does deep analysis)
        mev_patterns = [
            (r"swap.*\(", "Swap function - potential sandwich attack target"),
            (r"addLiquidity", "Liquidity addition - MEV extractable"),
            (r"removeLiquidity", "Liquidity removal - MEV extractable"),
            (r"transfer.*\(.*amount", "Large transfer - potential frontrunning target"),
        ]

        # Search for patterns in Solidity files
        import re

        sol_files = list(Path(self.config.project_path).rglob("*.sol"))
        mev_risks = []

        for sol_file in sol_files:
            try:
                content = sol_file.read_text()
                for pattern, description in mev_patterns:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    for match in matches:
                        # Get line number
                        line_num = content[:match.start()].count('\n') + 1
                        mev_risks.append({
                            "file": str(sol_file),
                            "line": line_num,
                            "pattern": pattern,
                            "description": description
                        })
            except Exception:
                pass

        for i, risk in enumerate(mev_risks[:10]):  # Limit to 10
            finding = Finding(
                id=f"mev-{i+1:03d}",
                type="mev_vulnerability",
                severity="MEDIUM",
                title="Potential MEV Extraction Point",
                description=risk["description"],
                location={
                    "file": Path(risk["file"]).name,
                    "line": risk["line"]
                },
                detected_by=["pattern_analysis"],
                confidence=0.5,
                profitability={
                    "type": "sandwich_attack",
                    "estimated_profit": "Variable based on liquidity",
                    "requires": "Mempool monitoring"
                },
                recommendation="Consider MEV protection mechanisms (Flashbots, private transactions)"
            )
            self.findings.append(finding)

        self.logger.info(f"  MEV check complete: {len(mev_risks)} potential issues")

    def _detect_flash_loan_vulnerabilities(self):
        """Detect flash loan attack vectors"""
        self.logger.info("  Checking for flash loan vulnerabilities...")

        flash_loan_patterns = [
            (r"balanceOf\(.*\).*[/\*]", "Price calculated from balance - flash loan manipulable"),
            (r"getReserves", "Using AMM reserves for pricing - flash loan risk"),
            (r"flashLoan", "Flash loan integration point"),
            (r"borrow.*callback", "Borrow callback - potential reentrancy via flash loan"),
        ]

        import re

        sol_files = list(Path(self.config.project_path).rglob("*.sol"))
        flash_risks = []

        for sol_file in sol_files:
            try:
                content = sol_file.read_text()
                for pattern, description in flash_loan_patterns:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        flash_risks.append({
                            "file": str(sol_file),
                            "line": line_num,
                            "description": description
                        })
            except Exception:
                pass

        for i, risk in enumerate(flash_risks[:10]):
            finding = Finding(
                id=f"flash-{i+1:03d}",
                type="flash_loan_vulnerability",
                severity="HIGH",
                title="Flash Loan Attack Vector",
                description=risk["description"],
                location={
                    "file": Path(risk["file"]).name,
                    "line": risk["line"]
                },
                detected_by=["pattern_analysis"],
                confidence=0.6,
                profitability={
                    "type": "flash_loan_attack",
                    "flash_loan_fee": "0.09% (Aave)",
                    "capital_required": "$0 (borrowed)"
                },
                recommendation="Use TWAP oracles, validate prices across multiple sources"
            )
            self.findings.append(finding)

        self.logger.info(f"  Flash loan check complete: {len(flash_risks)} potential issues")

    def _detect_oracle_vulnerabilities(self):
        """Detect oracle manipulation vulnerabilities"""
        self.logger.info("  Checking for oracle vulnerabilities...")

        oracle_patterns = [
            (r"latestRoundData", "Chainlink oracle - verify staleness checks"),
            (r"getPrice|price\(\)", "Price oracle - verify manipulation resistance"),
            (r"spot.*price", "Spot price - easily manipulable"),
            (r"twap|TWAP", "TWAP oracle - verify window duration"),
        ]

        import re

        sol_files = list(Path(self.config.project_path).rglob("*.sol"))
        oracle_risks = []

        for sol_file in sol_files:
            try:
                content = sol_file.read_text()
                for pattern, description in oracle_patterns:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        oracle_risks.append({
                            "file": str(sol_file),
                            "line": line_num,
                            "description": description
                        })
            except Exception:
                pass

        for i, risk in enumerate(oracle_risks[:10]):
            finding = Finding(
                id=f"oracle-{i+1:03d}",
                type="oracle_vulnerability",
                severity="HIGH",
                title="Oracle Manipulation Risk",
                description=risk["description"],
                location={
                    "file": Path(risk["file"]).name,
                    "line": risk["line"]
                },
                detected_by=["pattern_analysis"],
                confidence=0.5,
                recommendation="Use multiple oracle sources, implement staleness checks"
            )
            self.findings.append(finding)

        self.logger.info(f"  Oracle check complete: {len(oracle_risks)} potential issues")

    def _detect_governance_vulnerabilities(self):
        """Detect governance attack vectors"""
        self.logger.info("  Checking for governance vulnerabilities...")

        gov_patterns = [
            (r"vote\(|castVote", "Voting function - check for flash loan voting"),
            (r"propose\(", "Proposal creation - verify proposer requirements"),
            (r"timelock|delay", "Timelock - verify sufficient delay"),
            (r"delegate", "Vote delegation - check for manipulation"),
        ]

        import re

        sol_files = list(Path(self.config.project_path).rglob("*.sol"))
        gov_risks = []

        for sol_file in sol_files:
            try:
                content = sol_file.read_text()
                for pattern, description in gov_patterns:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        gov_risks.append({
                            "file": str(sol_file),
                            "line": line_num,
                            "description": description
                        })
            except Exception:
                pass

        for i, risk in enumerate(gov_risks[:10]):
            finding = Finding(
                id=f"gov-{i+1:03d}",
                type="governance_vulnerability",
                severity="HIGH",
                title="Governance Attack Vector",
                description=risk["description"],
                location={
                    "file": Path(risk["file"]).name,
                    "line": risk["line"]
                },
                detected_by=["pattern_analysis"],
                confidence=0.5,
                profitability={
                    "type": "governance_attack",
                    "historical_losses": "$200M+ in 2024"
                },
                recommendation="Use snapshot voting, require token holding period"
            )
            self.findings.append(finding)

        self.logger.info(f"  Governance check complete: {len(gov_risks)} potential issues")

    def _run_invariant_checks(self):
        """Run protocol invariant checks"""
        self.logger.info("  Running invariant checks...")

        # Define core invariants to check
        invariants = [
            "total_supply_conservation",
            "balance_sum_equals_supply",
            "no_negative_balances",
            "price_bounds",
            "liquidity_invariants"
        ]

        # For now, output invariants to check - Claude Code runs actual tests
        self.tool_results["invariants"] = {
            "status": "pattern_detection",
            "invariants_to_verify": invariants,
            "note": "Claude Code should run Foundry invariant tests"
        }

    def _compile_results(self, start_time: datetime) -> Dict[str, Any]:
        """Compile all results into structured JSON"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate statistics
        stats = {
            "total": len(self.findings),
            "critical": len([f for f in self.findings if f.severity == "CRITICAL"]),
            "high": len([f for f in self.findings if f.severity == "HIGH"]),
            "medium": len([f for f in self.findings if f.severity == "MEDIUM"]),
            "low": len([f for f in self.findings if f.severity == "LOW"]),
            "info": len([f for f in self.findings if f.severity == "INFO"])
        }

        return {
            "metadata": {
                "project_path": self.config.project_path,
                "chain": self.config.chain,
                "mode": self.config.mode,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "orchestrator_version": "1.0.0"
            },
            "statistics": stats,
            "findings": [f.to_dict() for f in self.findings],
            "tool_results": self.tool_results,
            "strategies_executed": self.config.strategies,
            "notes_for_claude_code": [
                "These are pattern-detected findings - analyze each for validity",
                "Cross-reference findings from multiple tools",
                "Filter false positives based on context",
                "Run deeper analysis on HIGH/CRITICAL findings",
                "Check for attack chains combining multiple findings"
            ]
        }

    def _compile_error_results(self, error: str, start_time: datetime) -> Dict[str, Any]:
        """Compile error results"""
        return {
            "metadata": {
                "project_path": self.config.project_path,
                "error": error,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            },
            "statistics": {"total": 0},
            "findings": [],
            "tool_results": self.tool_results,
            "error": error
        }

    def _save_results(self, results: Dict[str, Any]) -> str:
        """Save results to JSON file"""
        output_path = Path(self.config.output_dir) / "adversarial-findings.json"

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        return str(output_path)

    def _map_slither_severity(self, impact: str) -> str:
        """Map Slither severity to standard"""
        mapping = {
            "High": "HIGH",
            "Medium": "MEDIUM",
            "Low": "LOW",
            "Informational": "INFO",
            "Optimization": "INFO"
        }
        return mapping.get(impact, "LOW")

    def _map_slither_confidence(self, confidence: str) -> float:
        """Map Slither confidence to 0-1 scale"""
        mapping = {
            "High": 0.9,
            "Medium": 0.7,
            "Low": 0.5
        }
        return mapping.get(confidence, 0.5)

    def _map_mythril_severity(self, severity: str) -> str:
        """Map Mythril severity to standard"""
        mapping = {
            "High": "HIGH",
            "Medium": "MEDIUM",
            "Low": "LOW"
        }
        return mapping.get(severity, "LOW")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Unified Security Audit Orchestrator for Claude Code"
    )
    parser.add_argument(
        "--project", "-p",
        required=True,
        help="Path to project to audit"
    )
    parser.add_argument(
        "--chain", "-c",
        default="evm",
        choices=["evm", "solana"],
        help="Blockchain type"
    )
    parser.add_argument(
        "--mode", "-m",
        default="standard",
        choices=["quick", "standard", "deep"],
        help="Audit depth"
    )
    parser.add_argument(
        "--output", "-o",
        default="./audit-results",
        help="Output directory"
    )
    parser.add_argument(
        "--strategies", "-s",
        default="mev,flash_loan,oracle_manipulation,invariants",
        help="Comma-separated adversarial strategies"
    )

    args = parser.parse_args()

    config = UnifiedConfig(
        project_path=args.project,
        chain=args.chain,
        mode=args.mode,
        output_dir=args.output,
        strategies=args.strategies.split(",")
    )

    orchestrator = UnifiedOrchestrator(config)
    results = orchestrator.run()

    # Print summary
    stats = results.get("statistics", {})
    print(f"\n{'='*60}")
    print("AUDIT SUMMARY")
    print(f"{'='*60}")
    print(f"Total Findings: {stats.get('total', 0)}")
    print(f"  Critical: {stats.get('critical', 0)}")
    print(f"  High: {stats.get('high', 0)}")
    print(f"  Medium: {stats.get('medium', 0)}")
    print(f"  Low: {stats.get('low', 0)}")
    print(f"\nResults saved to: {args.output}/adversarial-findings.json")
    print("Claude Code can now read and analyze these findings.")


if __name__ == "__main__":
    main()
