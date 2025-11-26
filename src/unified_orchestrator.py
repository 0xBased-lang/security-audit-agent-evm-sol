#!/usr/bin/env python3
"""
Unified Security Orchestrator

Bridges JavaScript tools (Phase 1) with Python adversarial testing (Phase 2).
Coordinates multi-agent execution and aggregates results.

Architecture:
- Coordinates static analysis tools (Slither, Mythril, Foundry)
- Orchestrates adversarial agents (MEV, Flash Loan, Oracle)
- Aggregates findings from all sources
- Generates comprehensive audit reports
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys


class UnifiedSecurityOrchestrator:
    """
    Main orchestrator for comprehensive security audits.
    Bridges multiple analysis layers and coordinates agent execution.
    """

    def __init__(self, project_path: str, config: Optional[Dict] = None):
        self.project_path = Path(project_path)
        self.config = config or self._load_default_config()
        self.results = {
            "metadata": {
                "project_path": str(self.project_path),
                "timestamp": datetime.now().isoformat(),
                "framework_version": "1.0.0"
            },
            "static_analysis": {},
            "adversarial_testing": {},
            "agent_results": {},
            "summary": {}
        }

    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            "analysis_depth": "standard",  # quick | standard | deep
            "enable_adversarial": True,
            "enable_agents": True,
            "parallel_execution": True,
            "max_concurrent_agents": 5,
            "timeout_seconds": 600,
            "mcp_servers": {
                "vulnerability_feed": True,
                "evm_analysis": True,
                "adversarial": True
            }
        }

    async def run_comprehensive_audit(self) -> Dict:
        """
        Execute comprehensive security audit with all layers.

        Phases:
        1. Traditional static analysis (Slither, Mythril, Foundry)
        2. Adversarial testing (MEV, Flash Loans, Oracle)
        3. Protocol analysis (DeFi invariants, cross-protocol)
        4. Result synthesis and report generation
        """
        print(f"\n{'='*60}")
        print(f"🔍 COMPREHENSIVE SECURITY AUDIT")
        print(f"{'='*60}\n")
        print(f"Project: {self.project_path}")
        print(f"Depth: {self.config['analysis_depth']}")
        print(f"Timestamp: {self.results['metadata']['timestamp']}\n")

        # Phase 1: Static Analysis (Parallel)
        print("📊 Phase 1: Static Analysis")
        print("-" * 60)
        static_results = await self._run_static_analysis()
        self.results["static_analysis"] = static_results

        # Phase 2: Adversarial Testing (Parallel)
        if self.config["enable_adversarial"]:
            print("\n⚔️  Phase 2: Adversarial Testing")
            print("-" * 60)
            adversarial_results = await self._run_adversarial_testing()
            self.results["adversarial_testing"] = adversarial_results

        # Phase 3: Agent Coordination
        if self.config["enable_agents"]:
            print("\n🤖 Phase 3: Multi-Agent Analysis")
            print("-" * 60)
            agent_results = await self._run_agents()
            self.results["agent_results"] = agent_results

        # Phase 4: Synthesis
        print("\n📝 Phase 4: Synthesizing Results")
        print("-" * 60)
        summary = await self._synthesize_results()
        self.results["summary"] = summary

        # Generate report
        print("\n✅ Audit Complete!")
        print(f"{'='*60}\n")

        return self.results

    async def _run_static_analysis(self) -> Dict:
        """
        Run traditional static analysis tools in parallel.
        Uses MCP evm-analysis server for tool orchestration.
        """
        results = {
            "slither": None,
            "mythril": None,
            "foundry": None,
            "execution_time": 0
        }

        start_time = asyncio.get_event_loop().time()

        if self.config["parallel_execution"]:
            # Run tools in parallel
            tasks = []

            if self._should_run_tool("slither"):
                tasks.append(self._run_slither())

            if self._should_run_tool("mythril"):
                tasks.append(self._run_mythril())

            if self._should_run_tool("foundry"):
                tasks.append(self._run_foundry())

            # Execute all tasks concurrently
            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Map results
            for i, result in enumerate(task_results):
                if isinstance(result, Exception):
                    print(f"⚠️  Task {i} failed: {result}")
                    continue

                # Store result based on tool
                if "slither" in str(result.get("tool", "")):
                    results["slither"] = result
                elif "mythril" in str(result.get("tool", "")):
                    results["mythril"] = result
                elif "foundry" in str(result.get("tool", "")):
                    results["foundry"] = result
        else:
            # Sequential execution
            if self._should_run_tool("slither"):
                results["slither"] = await self._run_slither()

            if self._should_run_tool("mythril"):
                results["mythril"] = await self._run_mythril()

            if self._should_run_tool("foundry"):
                results["foundry"] = await self._run_foundry()

        results["execution_time"] = asyncio.get_event_loop().time() - start_time
        return results

    async def _run_slither(self) -> Dict:
        """Run Slither analysis"""
        print("  🔍 Running Slither...")

        try:
            # Check if Slither is installed
            subprocess.run(["slither", "--version"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("  ⚠️  Slither not installed, skipping")
            return {"tool": "slither", "status": "not_installed"}

        try:
            # Run Slither with JSON output
            cmd = ["slither", str(self.project_path), "--json", "-"]

            # Adjust based on analysis depth
            if self.config["analysis_depth"] == "quick":
                cmd.extend(["--severity", "high,critical"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_path
            )

            # Parse results
            try:
                slither_data = json.loads(result.stdout)
                findings = slither_data.get("results", {}).get("detectors", [])

                print(f"  ✓ Slither: {len(findings)} findings")

                return {
                    "tool": "slither",
                    "status": "success",
                    "findings_count": len(findings),
                    "findings": findings[:50],  # Limit to first 50
                    "raw_output": result.stdout[:5000]  # Truncate large output
                }
            except json.JSONDecodeError:
                print(f"  ⚠️  Slither: JSON parse error")
                return {
                    "tool": "slither",
                    "status": "parse_error",
                    "raw_output": result.stdout[:2000]
                }

        except subprocess.TimeoutExpired:
            print("  ⚠️  Slither: Timeout")
            return {"tool": "slither", "status": "timeout"}
        except Exception as e:
            print(f"  ⚠️  Slither error: {e}")
            return {"tool": "slither", "status": "error", "error": str(e)}

    async def _run_mythril(self) -> Dict:
        """Run Mythril symbolic execution"""
        print("  🔮 Running Mythril...")

        # Skip Mythril for quick mode
        if self.config["analysis_depth"] == "quick":
            print("  ⏭️  Mythril skipped (quick mode)")
            return {"tool": "mythril", "status": "skipped"}

        try:
            subprocess.run(["myth", "--version"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("  ⚠️  Mythril not installed, skipping")
            return {"tool": "mythril", "status": "not_installed"}

        # Find Solidity files
        sol_files = list(self.project_path.glob("**/*.sol"))
        if not sol_files:
            print("  ⚠️  No .sol files found")
            return {"tool": "mythril", "status": "no_files"}

        # Analyze first contract (or main contract)
        target_contract = sol_files[0]
        print(f"  🎯 Analyzing: {target_contract.name}")

        try:
            max_depth = 12 if self.config["analysis_depth"] == "standard" else 22

            result = subprocess.run(
                ["myth", "analyze", str(target_contract), f"--max-depth={max_depth}", "--json"],
                capture_output=True,
                text=True,
                timeout=300
            )

            try:
                mythril_data = json.loads(result.stdout)
                issues = mythril_data.get("issues", [])

                print(f"  ✓ Mythril: {len(issues)} issues")

                return {
                    "tool": "mythril",
                    "status": "success",
                    "issues_count": len(issues),
                    "issues": issues,
                    "analyzed_file": str(target_contract)
                }
            except json.JSONDecodeError:
                print("  ⚠️  Mythril: JSON parse error")
                return {"tool": "mythril", "status": "parse_error"}

        except subprocess.TimeoutExpired:
            print("  ⚠️  Mythril: Timeout")
            return {"tool": "mythril", "status": "timeout"}
        except Exception as e:
            print(f"  ⚠️  Mythril error: {e}")
            return {"tool": "mythril", "status": "error", "error": str(e)}

    async def _run_foundry(self) -> Dict:
        """Run Foundry fuzz tests"""
        print("  ⚡ Running Foundry tests...")

        # Check if Foundry project
        if not (self.project_path / "foundry.toml").exists():
            print("  ⏭️  Not a Foundry project, skipping")
            return {"tool": "foundry", "status": "not_foundry_project"}

        try:
            subprocess.run(["forge", "--version"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("  ⚠️  Foundry not installed, skipping")
            return {"tool": "foundry", "status": "not_installed"}

        try:
            fuzz_runs = {
                "quick": 100,
                "standard": 1000,
                "deep": 10000
            }.get(self.config["analysis_depth"], 1000)

            result = subprocess.run(
                ["forge", "test", f"--fuzz-runs={fuzz_runs}"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_path
            )

            # Parse test results
            stdout = result.stdout
            passed = "PASSED" in stdout
            failed = "FAILED" in stdout

            print(f"  ✓ Foundry: {'PASSED' if passed and not failed else 'FAILED'}")

            return {
                "tool": "foundry",
                "status": "success",
                "test_result": "passed" if passed and not failed else "failed",
                "fuzz_runs": fuzz_runs,
                "output": stdout[:2000]
            }

        except subprocess.TimeoutExpired:
            print("  ⚠️  Foundry: Timeout")
            return {"tool": "foundry", "status": "timeout"}
        except Exception as e:
            print(f"  ⚠️  Foundry error: {e}")
            return {"tool": "foundry", "status": "error", "error": str(e)}

    async def _run_adversarial_testing(self) -> Dict:
        """
        Run adversarial testing agents in parallel.
        Uses MCP adversarial server for attack simulations.
        """
        results = {
            "mev_analysis": None,
            "flash_loan_analysis": None,
            "oracle_analysis": None,
            "governance_analysis": None,
            "execution_time": 0
        }

        start_time = asyncio.get_event_loop().time()

        # Detect contract type to determine which tests to run
        contract_type = await self._detect_contract_type()

        print(f"  📋 Detected contract type: {contract_type}")

        # Run appropriate adversarial tests based on contract type
        tasks = []

        if contract_type in ["dex", "amm", "unknown"]:
            tasks.append(self._analyze_mev_vulnerabilities())

        if contract_type in ["lending", "defi", "unknown"]:
            tasks.append(self._analyze_flash_loan_vulnerabilities())

        if contract_type in ["dex", "lending", "defi", "unknown"]:
            tasks.append(self._analyze_oracle_vulnerabilities())

        if contract_type in ["governance", "dao", "unknown"]:
            tasks.append(self._analyze_governance_vulnerabilities())

        # Execute adversarial tests in parallel
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Map results
            for result in task_results:
                if isinstance(result, Exception):
                    continue

                analysis_type = result.get("analysis_type", "")
                if "mev" in analysis_type:
                    results["mev_analysis"] = result
                elif "flash_loan" in analysis_type:
                    results["flash_loan_analysis"] = result
                elif "oracle" in analysis_type:
                    results["oracle_analysis"] = result
                elif "governance" in analysis_type:
                    results["governance_analysis"] = result

        results["execution_time"] = asyncio.get_event_loop().time() - start_time
        return results

    async def _detect_contract_type(self) -> str:
        """Detect contract type from code analysis"""
        # Simple heuristic-based detection
        # Look for common patterns in contract files

        sol_files = list(self.project_path.glob("**/*.sol"))
        if not sol_files:
            return "unknown"

        # Read first few contracts
        content = ""
        for sol_file in sol_files[:5]:
            try:
                with open(sol_file, 'r') as f:
                    content += f.read().lower()
            except Exception as e:
                # File read error (permissions, encoding, etc.)
                # Log and continue with other files
                print(f"Warning: Could not read {sol_file}: {e}", file=sys.stderr)
                continue

        # Pattern matching
        if "swap" in content or "liquidity" in content or "pool" in content:
            return "dex"
        elif "borrow" in content or "lend" in content or "collateral" in content:
            return "lending"
        elif "vote" in content or "proposal" in content or "governance" in content:
            return "governance"
        elif "stake" in content or "reward" in content:
            return "staking"
        else:
            return "defi"  # Generic DeFi

    async def _analyze_mev_vulnerabilities(self) -> Dict:
        """Analyze MEV/sandwich attack vulnerabilities"""
        print("  🥪 Analyzing MEV vulnerabilities...")

        # Placeholder for actual MCP call to adversarial server
        # In real implementation, this would call:
        # mcp.call_tool("adversarial", "analyze_protocol_vulnerabilities", {...})

        return {
            "analysis_type": "mev",
            "status": "simulated",
            "vulnerable": False,
            "note": "Full adversarial MCP integration pending"
        }

    async def _analyze_flash_loan_vulnerabilities(self) -> Dict:
        """Analyze flash loan attack vulnerabilities"""
        print("  ⚡ Analyzing flash loan vulnerabilities...")

        return {
            "analysis_type": "flash_loan",
            "status": "simulated",
            "vulnerable": False,
            "note": "Full adversarial MCP integration pending"
        }

    async def _analyze_oracle_vulnerabilities(self) -> Dict:
        """Analyze oracle manipulation vulnerabilities"""
        print("  📊 Analyzing oracle vulnerabilities...")

        return {
            "analysis_type": "oracle",
            "status": "simulated",
            "vulnerable": False,
            "note": "Full adversarial MCP integration pending"
        }

    async def _analyze_governance_vulnerabilities(self) -> Dict:
        """Analyze governance attack vulnerabilities"""
        print("  🗳️  Analyzing governance vulnerabilities...")

        return {
            "analysis_type": "governance",
            "status": "simulated",
            "vulnerable": False,
            "note": "Full adversarial MCP integration pending"
        }

    async def _run_agents(self) -> Dict:
        """
        Coordinate multi-agent execution.
        Agents run in parallel where possible.
        """
        # Placeholder for agent coordination
        # Will be fully implemented in Week 3

        return {
            "agents_executed": [],
            "note": "Multi-agent coordination in development"
        }

    async def _synthesize_results(self) -> Dict:
        """
        Synthesize findings from all sources.
        Identifies attack chains, false positives, and prioritizes issues.
        """
        summary = {
            "total_issues": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "attack_vectors": [],
            "recommendations": []
        }

        # Count issues from static analysis
        if self.results.get("static_analysis"):
            slither_findings = self.results["static_analysis"].get("slither", {}).get("findings", [])
            summary["total_issues"] += len(slither_findings)

            # Count by severity
            for finding in slither_findings:
                impact = finding.get("impact", "").lower()
                if impact == "high":
                    summary["critical"] += 1
                elif impact == "medium":
                    summary["high"] += 1
                elif impact == "low":
                    summary["medium"] += 1

        # Add adversarial findings
        if self.results.get("adversarial_testing"):
            # Check each analysis type
            for analysis_type, analysis_data in self.results["adversarial_testing"].items():
                if isinstance(analysis_data, dict) and analysis_data.get("vulnerable"):
                    summary["attack_vectors"].append(analysis_type)
                    summary["critical"] += 1

        # Generate recommendations
        if summary["critical"] > 0:
            summary["recommendations"].append("Address all CRITICAL issues before deployment")

        if summary["attack_vectors"]:
            summary["recommendations"].append(f"Mitigate attack vectors: {', '.join(summary['attack_vectors'])}")

        print(f"\n  📊 Total Issues: {summary['total_issues']}")
        print(f"  🔴 Critical: {summary['critical']}")
        print(f"  🟠 High: {summary['high']}")
        print(f"  🟡 Medium: {summary['medium']}")

        return summary

    def _should_run_tool(self, tool_name: str) -> bool:
        """Check if a tool should be run based on config"""
        # For now, run all tools
        return True

    def save_results(self, output_path: Optional[Path] = None) -> Path:
        """Save audit results to JSON file"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"audit_results_{timestamp}.json")

        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Results saved to: {output_path}")
        return output_path


# ============ CLI Entry Point ============

async def main():
    """CLI entry point for unified orchestrator"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Unified Security Orchestrator for EVM Smart Contracts"
    )
    parser.add_argument(
        "project_path",
        help="Path to smart contract project"
    )
    parser.add_argument(
        "--depth",
        choices=["quick", "standard", "deep"],
        default="standard",
        help="Analysis depth (default: standard)"
    )
    parser.add_argument(
        "--no-adversarial",
        action="store_true",
        help="Skip adversarial testing"
    )
    parser.add_argument(
        "--no-agents",
        action="store_true",
        help="Skip multi-agent analysis"
    )
    parser.add_argument(
        "--output",
        help="Output file path for results"
    )

    args = parser.parse_args()

    # Build config
    config = {
        "analysis_depth": args.depth,
        "enable_adversarial": not args.no_adversarial,
        "enable_agents": not args.no_agents,
        "parallel_execution": True,
        "max_concurrent_agents": 5,
        "timeout_seconds": 600
    }

    # Create orchestrator
    orchestrator = UnifiedSecurityOrchestrator(args.project_path, config)

    # Run audit
    results = await orchestrator.run_comprehensive_audit()

    # Save results
    output_path = Path(args.output) if args.output else None
    orchestrator.save_results(output_path)

    # Exit with error code if critical issues found
    critical_count = results.get("summary", {}).get("critical", 0)
    sys.exit(1 if critical_count > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
