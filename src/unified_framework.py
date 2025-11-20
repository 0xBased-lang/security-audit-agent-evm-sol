"""
Unified Security Framework

Single entry point integrating:
- Traditional static/dynamic analysis (Phase 1 - JavaScript)
- Adversarial agent testing (Phase 1 + 2 - Python)
- Multi-chain simulation (Phase 2)
- AI synthesis (Claude)
"""

import asyncio
import logging
import time
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

# Import schemas
from .schemas.vulnerability import (
    UnifiedVulnerability,
    VulnerabilityLocation,
    VulnerabilitySeverity,
    AuditReport,
)

# Import bridges
from .bridges.javascript_bridge import JavaScriptBridge, AuditError

# Import configuration
from .config import AuditConfig

# Import adversarial components (Phase 1)
from .adversarial.orchestrator import AdversarialOrchestrator


class UnifiedSecurityFramework:
    """
    Unified Security Framework

    Orchestrates all security testing components:
    1. Traditional audit tools (Slither, Mythril, etc.)
    2. Adversarial agent testing (economic exploits, MEV)
    3. AI-powered synthesis and analysis
    """

    def __init__(self, config: Optional[AuditConfig] = None):
        """
        Initialize unified framework

        Args:
            config: Audit configuration (uses default if None)
        """
        self.config = config or AuditConfig()
        self.config.validate()

        # Setup logging
        self.logger = self._setup_logging()

        # Initialize components
        self.js_bridge = JavaScriptBridge()
        self.adversarial_orchestrator = None  # Lazy initialization

        self.logger.info(
            f"Unified Security Framework initialized (mode={self.config.mode})"
        )

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('unified_framework')

        # Set level based on verbose flag
        level = logging.DEBUG if self.config.verbose else logging.INFO
        logger.setLevel(level)

        # Create console handler
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level)

            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)

            logger.addHandler(handler)

        return logger

    async def audit(
        self,
        project_path: str,
        mode: Optional[str] = None
    ) -> AuditReport:
        """
        Run complete security audit

        Args:
            project_path: Path to smart contract project
            mode: Audit mode override ("quick", "standard", "deep")

        Returns:
            Complete audit report

        Examples:
            # Quick audit (traditional tools only)
            framework = UnifiedSecurityFramework()
            report = await framework.audit('./my-project', mode='quick')

            # Standard audit (traditional + basic adversarial)
            report = await framework.audit('./my-project')

            # Deep audit (full 10-layer AASS)
            report = await framework.audit('./my-project', mode='deep')
        """
        # Override mode if specified
        if mode:
            self.config.mode = mode
            self.config.__post_init__()  # Reconfigure based on mode

        self.logger.info(f"Starting {self.config.mode} audit of {project_path}")
        start_time = time.time()

        # Validate project path
        if not os.path.exists(project_path):
            raise ValueError(f"Project path does not exist: {project_path}")

        # Detect chain type
        chain = self._detect_chain(project_path)
        self.logger.info(f"Detected chain: {chain}")

        # Initialize report
        report = AuditReport(
            project_name=Path(project_path).name,
            project_path=project_path,
            chain=chain,
            audit_mode=self.config.mode,
        )

        # Run audit phases
        try:
            # Phase 1: Traditional audit tools
            if self.config.traditional_enabled:
                traditional_results = await self._run_traditional_audit(
                    project_path, report
                )
                report.traditional_findings = traditional_results

            # Phase 2: Adversarial testing
            if self.config.adversarial_enabled:
                adversarial_results = await self._run_adversarial_testing(
                    project_path, report
                )
                report.adversarial_findings = adversarial_results

            # Phase 3: Integration & synthesis
            await self._synthesize_results(report)

            # Calculate final statistics
            report.calculate_statistics()

        except Exception as e:
            self.logger.error(f"Audit failed: {e}", exc_info=True)
            report.warning_messages['audit_error'] = str(e)

        # Record duration
        report.duration_seconds = time.time() - start_time
        self.logger.info(
            f"Audit completed in {report.duration_seconds:.1f}s "
            f"({report.total_vulnerabilities} vulnerabilities found)"
        )

        # Save reports
        await self._save_reports(report)

        return report

    async def _run_traditional_audit(
        self,
        project_path: str,
        report: AuditReport
    ) -> List[UnifiedVulnerability]:
        """
        Run Phase 1 traditional audit tools

        Args:
            project_path: Project path
            report: Report to update

        Returns:
            List of vulnerabilities from traditional tools
        """
        self.logger.info("Running traditional audit tools...")

        try:
            # Execute JavaScript audit tools
            results = self.js_bridge.run_traditional_audit(
                project_path=project_path,
                tools=self.config.traditional_tools,
                timeout=self.config.traditional_timeout
            )

            # Convert to unified vulnerabilities
            vulnerabilities = self._convert_traditional_results(results)

            # Update report
            report.tools_executed.extend(results.get('tools_executed', []))

            self.logger.info(
                f"Traditional audit found {len(vulnerabilities)} vulnerabilities"
            )

            return vulnerabilities

        except AuditError as e:
            self.logger.error(f"Traditional audit failed: {e}")
            report.warning_messages['traditional_audit'] = str(e)
            report.tools_failed.append('traditional_audit')
            return []

    async def _run_adversarial_testing(
        self,
        project_path: str,
        report: AuditReport
    ) -> List[UnifiedVulnerability]:
        """
        Run Phase 2 adversarial testing

        Args:
            project_path: Project path
            report: Report to update

        Returns:
            List of vulnerabilities from adversarial agents
        """
        self.logger.info("Running adversarial testing...")

        try:
            # Lazy initialization of adversarial orchestrator
            if self.adversarial_orchestrator is None:
                self.adversarial_orchestrator = AdversarialOrchestrator(
                    chain=self.config.chain,
                    strategies=self.config.adversarial_strategies,
                    iterations=self.config.adversarial_iterations,
                )

            # Run adversarial testing
            results = self.adversarial_orchestrator.run_adversarial_test()

            # Convert to unified vulnerabilities
            vulnerabilities = self._convert_adversarial_results(results)

            self.logger.info(
                f"Adversarial testing found {len(vulnerabilities)} vulnerabilities"
            )

            return vulnerabilities

        except Exception as e:
            self.logger.error(f"Adversarial testing failed: {e}", exc_info=True)
            report.warning_messages['adversarial_testing'] = str(e)
            report.tools_failed.append('adversarial_testing')
            return []

    async def _synthesize_results(self, report: AuditReport):
        """
        Synthesize all findings using Claude AI

        Args:
            report: Report to synthesize
        """
        self.logger.info("Synthesizing results with Claude AI...")

        # Combine all vulnerabilities
        all_vulnerabilities = []

        if report.traditional_findings:
            all_vulnerabilities.extend(report.traditional_findings)

        if report.adversarial_findings:
            all_vulnerabilities.extend(report.adversarial_findings)

        # Cross-reference findings (identify duplicates/related issues)
        all_vulnerabilities = self._cross_reference_findings(all_vulnerabilities)

        # Update report
        report.vulnerabilities = all_vulnerabilities

        # AI synthesis (if enabled and API key available)
        if self.config.ai_enabled and self.config.anthropic_api_key:
            try:
                synthesis = await self._run_ai_synthesis(report)
                report.synthesis = synthesis
            except Exception as e:
                self.logger.warning(f"AI synthesis failed: {e}")
                report.warning_messages['ai_synthesis'] = str(e)
        else:
            self.logger.info("AI synthesis disabled or no API key")

    def _cross_reference_findings(
        self,
        vulnerabilities: List[UnifiedVulnerability]
    ) -> List[UnifiedVulnerability]:
        """
        Cross-reference findings from different tools

        Identifies:
        - Duplicates (same vulnerability found by multiple tools)
        - Related vulnerabilities (compound risks)
        - False positives (theoretical issues not exploitable)

        Args:
            vulnerabilities: List of all vulnerabilities

        Returns:
            Deduplicated and cross-referenced vulnerabilities
        """
        self.logger.info(f"Cross-referencing {len(vulnerabilities)} findings...")

        # Group by type and location
        by_type_location: Dict[tuple, List[UnifiedVulnerability]] = {}

        for vuln in vulnerabilities:
            key = (
                vuln.type,
                vuln.location.file,
                vuln.location.line,
            )

            if key not in by_type_location:
                by_type_location[key] = []

            by_type_location[key].append(vuln)

        # Merge duplicates
        unique_vulnerabilities = []

        for key, dupes in by_type_location.items():
            if len(dupes) == 1:
                # Single finding
                unique_vulnerabilities.append(dupes[0])
            else:
                # Multiple tools found same issue - merge
                merged = self._merge_duplicate_vulnerabilities(dupes)
                unique_vulnerabilities.append(merged)

        self.logger.info(
            f"Cross-referencing complete: {len(unique_vulnerabilities)} unique findings"
        )

        return unique_vulnerabilities

    def _merge_duplicate_vulnerabilities(
        self,
        duplicates: List[UnifiedVulnerability]
    ) -> UnifiedVulnerability:
        """
        Merge duplicate vulnerabilities found by multiple tools

        Args:
            duplicates: List of duplicate vulnerabilities

        Returns:
            Single merged vulnerability
        """
        # Take the most severe assessment
        base = max(duplicates, key=lambda v: v.get_priority_score())

        # Record all detectors that found it
        base.confirmed_by = [v.detected_by for v in duplicates if v != base]

        # Increase confidence since multiple tools agree
        base.confidence = min(1.0, base.confidence * (1 + 0.1 * len(duplicates)))

        # Merge descriptions
        if len(duplicates) > 1:
            base.description += "\n\nConfirmed by: " + ", ".join(base.confirmed_by)

        return base

    async def _run_ai_synthesis(self, report: AuditReport) -> str:
        """
        Run Claude AI synthesis

        Args:
            report: Audit report

        Returns:
            Synthesis text
        """
        # TODO: Implement Claude API integration
        # For now, return placeholder
        self.logger.info("AI synthesis not yet implemented")
        return "AI synthesis pending implementation"

    def _convert_traditional_results(
        self,
        results: Dict[str, Any]
    ) -> List[UnifiedVulnerability]:
        """
        Convert traditional tool results to unified format

        Args:
            results: Results from JavaScript tools

        Returns:
            List of unified vulnerabilities
        """
        vulnerabilities = []

        for item in results.get('vulnerabilities', []):
            try:
                vuln = UnifiedVulnerability(
                    id=item.get('id', f"trad-{len(vulnerabilities)}"),
                    type=item.get('type', 'unknown'),
                    severity=VulnerabilitySeverity(item.get('severity', 'MEDIUM')),
                    title=item.get('title', 'Untitled'),
                    description=item.get('description', ''),
                    location=VulnerabilityLocation(
                        file=item.get('file', 'unknown'),
                        line=item.get('line'),
                        function=item.get('function'),
                        contract=item.get('contract'),
                    ),
                    detected_by=item.get('tool', 'unknown'),
                    confidence=item.get('confidence', 0.8),
                    recommendation=item.get('recommendation', ''),
                    references=item.get('references', []),
                )

                vulnerabilities.append(vuln)

            except Exception as e:
                self.logger.warning(f"Failed to parse vulnerability: {e}")
                continue

        return vulnerabilities

    def _convert_adversarial_results(
        self,
        results: Any
    ) -> List[UnifiedVulnerability]:
        """
        Convert adversarial testing results to unified format

        Args:
            results: Results from adversarial orchestrator (AdversarialTestResults)

        Returns:
            List of unified vulnerabilities
        """
        vulnerabilities = []

        if not results or not hasattr(results, 'vulnerabilities'):
            self.logger.warning("No adversarial results to convert")
            return []

        self.logger.info(f"Converting {len(results.vulnerabilities)} adversarial findings")

        for idx, adv_vuln in enumerate(results.vulnerabilities):
            try:
                # Extract core information
                vuln_type = adv_vuln.get('type', 'unknown_exploit')
                title = adv_vuln.get('title', f"Adversarial exploit {idx + 1}")
                description = adv_vuln.get('description', '')

                # Determine severity based on profit or impact
                profit = adv_vuln.get('profit_extracted', 0)
                severity = self._determine_adversarial_severity(profit, adv_vuln)

                # Extract location if available
                location_data = adv_vuln.get('location', {})
                location = VulnerabilityLocation(
                    file=location_data.get('file', 'unknown'),
                    line=location_data.get('line'),
                    function=location_data.get('function'),
                    contract=location_data.get('contract'),
                )

                # Create unified vulnerability
                vuln = UnifiedVulnerability(
                    id=f"adv-{idx + 1:03d}",
                    type=vuln_type,
                    severity=severity,
                    title=title,
                    description=description,
                    location=location,
                    detected_by='adversarial_agent',
                    confidence=adv_vuln.get('confidence', 0.85),

                    # Adversarial-specific fields
                    exploit_transaction_sequence=adv_vuln.get('attack_sequence', []),
                    profit_extracted=profit,
                    invariant_violated=adv_vuln.get('invariant_violated'),
                    feasibility_score=adv_vuln.get('feasibility_score', 75),

                    # Impact analysis
                    potential_loss_usd=profit if profit > 0 else adv_vuln.get('potential_loss', 0),
                    impact_description=adv_vuln.get('impact', ''),

                    # Remediation
                    recommendation=adv_vuln.get('recommendation', self._generate_adversarial_recommendation(vuln_type)),

                    # Metadata
                    tags=['adversarial', 'economic_exploit', vuln_type],
                    metadata={
                        'strategy': adv_vuln.get('strategy'),
                        'iterations': adv_vuln.get('iterations'),
                        'search_algorithm': adv_vuln.get('search_algorithm'),
                    }
                )

                vulnerabilities.append(vuln)

            except Exception as e:
                self.logger.error(f"Failed to convert adversarial vulnerability {idx}: {e}")
                continue

        self.logger.info(f"Successfully converted {len(vulnerabilities)} adversarial vulnerabilities")

        return vulnerabilities

    def _determine_adversarial_severity(
        self,
        profit: float,
        vuln_data: Dict[str, Any]
    ) -> VulnerabilitySeverity:
        """
        Determine severity based on exploit profitability and impact

        Args:
            profit: Profit extracted in ETH/SOL
            vuln_data: Vulnerability data

        Returns:
            Severity level
        """
        # Check if explicit severity provided
        if 'severity' in vuln_data:
            try:
                return VulnerabilitySeverity(vuln_data['severity'].upper())
            except (ValueError, AttributeError):
                pass

        # Determine from profit (assuming ETH/SOL at ~$2000-3000)
        if profit > 100:  # > $200k
            return VulnerabilitySeverity.CRITICAL
        elif profit > 10:  # > $20k
            return VulnerabilitySeverity.HIGH
        elif profit > 1:  # > $2k
            return VulnerabilitySeverity.MEDIUM
        elif profit > 0:
            return VulnerabilitySeverity.LOW
        else:
            # No profit extracted but invariant violated
            if vuln_data.get('invariant_violated'):
                return VulnerabilitySeverity.MEDIUM
            return VulnerabilitySeverity.LOW

    def _generate_adversarial_recommendation(self, vuln_type: str) -> str:
        """
        Generate recommendation based on vulnerability type

        Args:
            vuln_type: Type of vulnerability

        Returns:
            Remediation recommendation
        """
        recommendations = {
            'oracle_manipulation': 'Use TWAP oracle with minimum update interval. Implement circuit breakers for price deviations >5%.',
            'flash_loan': 'Add flash loan detection and protection. Use commit-reveal patterns for critical operations.',
            'sandwich_attack': 'Implement MEV protection: private transactions, time-weighted pricing, or MEV-resistant AMM design.',
            'liquidation_sniping': 'Add liquidation delays or Dutch auction mechanisms. Distribute MEV to protocol users.',
            'arbitrage_exploit': 'Review arbitrage opportunities. Consider if this is protocol design or exploit.',
            'reentrancy': 'Add reentrancy guards. Follow checks-effects-interactions pattern.',
            'frontrunning': 'Use commit-reveal, time-locks, or private transaction submission.',
        }

        return recommendations.get(
            vuln_type,
            'Review exploit mechanics and implement appropriate safeguards. Consider economic incentives.'
        )

    def _detect_chain(self, project_path: str) -> str:
        """
        Detect blockchain type from project structure

        Args:
            project_path: Project path

        Returns:
            Chain type ("ethereum", "solana", etc.)
        """
        project_path = Path(project_path)

        # Check for Solana indicators
        if (project_path / 'Cargo.toml').exists():
            return 'solana'

        # Check for Ethereum indicators
        if (project_path / 'hardhat.config.js').exists():
            return 'ethereum'

        if (project_path / 'foundry.toml').exists():
            return 'ethereum'

        if (project_path / 'package.json').exists():
            # Default to ethereum for JS projects
            return 'ethereum'

        # Default
        self.logger.warning(f"Could not detect chain type for {project_path}")
        return self.config.chain

    async def _save_reports(self, report: AuditReport):
        """
        Save audit reports in various formats

        Args:
            report: Report to save
        """
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON
        if 'json' in self.config.output_formats:
            json_path = output_dir / 'comprehensive-report.json'
            report.save(str(json_path))
            self.logger.info(f"Saved JSON report: {json_path}")

        # Save Markdown
        if 'markdown' in self.config.output_formats:
            from .reports.markdown_generator import MarkdownReportGenerator
            md_generator = MarkdownReportGenerator()
            md_path = output_dir / 'comprehensive-report.md'
            md_generator.save(report, str(md_path))
            self.logger.info(f"Saved Markdown report: {md_path}")

        # Save TOON (if enabled)
        if 'toon' in self.config.output_formats:
            from .utils.toon_encoder import TOONEncoder
            toon_encoder = TOONEncoder()
            toon_str = toon_encoder.encode_report(report.to_dict())
            toon_path = output_dir / 'comprehensive-report.toon'
            with open(toon_path, 'w') as f:
                f.write(toon_str)
            self.logger.info(f"Saved TOON report: {toon_path}")

            # Log token savings
            json_tokens = len(report.to_json()) // 4
            toon_tokens = len(toon_str) // 4
            savings = (1 - toon_tokens / json_tokens) * 100 if json_tokens > 0 else 0
            self.logger.info(
                f"TOON savings: {savings:.1f}% ({json_tokens} → {toon_tokens} tokens)"
            )

        # Save HTML
        if 'html' in self.config.output_formats:
            self.logger.info("HTML report generation not yet implemented (Phase 2+)")


# Convenience functions
async def quick_audit(project_path: str) -> AuditReport:
    """Run quick audit (traditional tools only, 2-5 min)"""
    framework = UnifiedSecurityFramework(config=AuditConfig.quick())
    return await framework.audit(project_path)


async def standard_audit(project_path: str) -> AuditReport:
    """Run standard audit (traditional + basic adversarial, 30-60 min)"""
    framework = UnifiedSecurityFramework(config=AuditConfig.standard())
    return await framework.audit(project_path)


async def deep_audit(project_path: str) -> AuditReport:
    """Run deep audit (full 10-layer AASS, 2-4 hours)"""
    framework = UnifiedSecurityFramework(config=AuditConfig.deep())
    return await framework.audit(project_path)
