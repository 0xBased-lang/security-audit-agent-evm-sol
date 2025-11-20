"""
Markdown Report Generator

Generates comprehensive, human-readable markdown reports for security audits.
"""

from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from ..schemas.vulnerability import (
    AuditReport,
    UnifiedVulnerability,
    VulnerabilitySeverity,
)


class MarkdownReportGenerator:
    """
    Generate professional markdown reports for security audits

    Output includes:
    - Executive summary
    - Statistics and risk assessment
    - Vulnerabilities grouped by severity
    - Detailed findings with remediation
    - Tool execution summary
    """

    def __init__(self):
        pass

    def generate(self, report: AuditReport) -> str:
        """
        Generate complete markdown report

        Args:
            report: Audit report to convert

        Returns:
            Markdown-formatted report string
        """
        sections = []

        # Header
        sections.append(self._generate_header(report))

        # Executive summary
        sections.append(self._generate_executive_summary(report))

        # Statistics
        sections.append(self._generate_statistics(report))

        # Critical findings (if any)
        if report.critical_count > 0:
            sections.append(self._generate_critical_findings(report))

        # Findings by severity
        sections.append(self._generate_findings_by_severity(report))

        # Synthesis (if available)
        if report.synthesis:
            sections.append(self._generate_synthesis(report))

        # Recommendations
        sections.append(self._generate_recommendations(report))

        # Tool summary
        sections.append(self._generate_tool_summary(report))

        # Footer
        sections.append(self._generate_footer(report))

        return '\n\n'.join(sections)

    def _generate_header(self, report: AuditReport) -> str:
        """Generate report header"""
        return f"""# Security Audit Report

**Project**: {report.project_name}
**Chain**: {report.chain.title()}
**Audit Date**: {report.audit_date.strftime('%Y-%m-%d %H:%M:%S')}
**Audit Mode**: {report.audit_mode.title()}
**Duration**: {report.duration_seconds:.1f}s

---"""

    def _generate_executive_summary(self, report: AuditReport) -> str:
        """Generate executive summary"""
        # Determine overall risk level
        if report.critical_count > 0:
            risk_level = "🔴 **CRITICAL**"
            risk_desc = "Critical vulnerabilities found. **DO NOT DEPLOY** until fixed."
        elif report.high_count > 5:
            risk_level = "🟠 **HIGH**"
            risk_desc = "Multiple high-severity vulnerabilities. Deployment not recommended."
        elif report.high_count > 0:
            risk_level = "🟡 **MEDIUM-HIGH**"
            risk_desc = "High-severity vulnerabilities found. Review and fix before deployment."
        elif report.medium_count > 10:
            risk_level = "🟡 **MEDIUM**"
            risk_desc = "Several medium-severity issues. Address before production deployment."
        else:
            risk_level = "🟢 **LOW**"
            risk_desc = "No critical or high-severity vulnerabilities found. Standard precautions apply."

        return f"""## Executive Summary

**Overall Risk**: {risk_level}

{risk_desc}

**Total Findings**: {report.total_vulnerabilities}
- Critical: {report.critical_count}
- High: {report.high_count}
- Medium: {report.medium_count}
- Low: {report.low_count}
- Informational: {report.info_count}"""

    def _generate_statistics(self, report: AuditReport) -> str:
        """Generate statistics table"""
        return f"""## Statistics

| Metric | Value |
|--------|-------|
| Total Vulnerabilities | {report.total_vulnerabilities} |
| Critical Severity | {report.critical_count} |
| High Severity | {report.high_count} |
| Medium Severity | {report.medium_count} |
| Low Severity | {report.low_count} |
| Informational | {report.info_count} |
| Tools Executed | {len(report.tools_executed)} |
| Traditional Findings | {len(report.traditional_findings) if report.traditional_findings else 0} |
| Adversarial Findings | {len(report.adversarial_findings) if report.adversarial_findings else 0} |"""

    def _generate_critical_findings(self, report: AuditReport) -> str:
        """Generate critical findings section"""
        critical_vulns = [v for v in report.vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL]

        if not critical_vulns:
            return ""

        lines = ["## 🔴 Critical Vulnerabilities", ""]
        lines.append("**IMMEDIATE ACTION REQUIRED**")
        lines.append("")

        for idx, vuln in enumerate(critical_vulns, 1):
            lines.append(f"### {idx}. {vuln.title}")
            lines.append("")
            lines.append(f"**ID**: `{vuln.id}`")
            lines.append(f"**Type**: {vuln.type}")
            lines.append(f"**Location**: `{vuln.location.file}:{vuln.location.line}`")
            if vuln.location.function:
                lines.append(f"**Function**: `{vuln.location.function}()`")
            lines.append(f"**Detected by**: {vuln.detected_by}")
            if vuln.confirmed_by:
                lines.append(f"**Confirmed by**: {', '.join(vuln.confirmed_by)}")
            lines.append("")

            lines.append("**Description**:")
            lines.append(vuln.description)
            lines.append("")

            if vuln.profit_extracted and vuln.profit_extracted > 0:
                lines.append(f"**Profit Extracted**: {vuln.profit_extracted:.2f} ETH/SOL")
                lines.append("")

            if vuln.feasibility_score:
                lines.append(f"**Exploitability**: {vuln.feasibility_score}/100")
                lines.append("")

            lines.append("**Recommendation**:")
            lines.append(vuln.recommendation)
            lines.append("")
            lines.append("---")
            lines.append("")

        return '\n'.join(lines)

    def _generate_findings_by_severity(self, report: AuditReport) -> str:
        """Generate all findings grouped by severity"""
        sections = ["## Detailed Findings", ""]

        # Group by severity
        by_severity = {
            VulnerabilitySeverity.HIGH: [],
            VulnerabilitySeverity.MEDIUM: [],
            VulnerabilitySeverity.LOW: [],
            VulnerabilitySeverity.INFO: [],
        }

        for vuln in report.vulnerabilities:
            if vuln.severity == VulnerabilitySeverity.CRITICAL:
                continue  # Already covered in critical section
            if vuln.severity in by_severity:
                by_severity[vuln.severity].append(vuln)

        # High severity
        if by_severity[VulnerabilitySeverity.HIGH]:
            sections.append("### 🟠 High Severity")
            sections.append("")
            for vuln in by_severity[VulnerabilitySeverity.HIGH]:
                sections.append(self._format_vulnerability(vuln))

        # Medium severity
        if by_severity[VulnerabilitySeverity.MEDIUM]:
            sections.append("### 🟡 Medium Severity")
            sections.append("")
            for vuln in by_severity[VulnerabilitySeverity.MEDIUM]:
                sections.append(self._format_vulnerability(vuln))

        # Low severity
        if by_severity[VulnerabilitySeverity.LOW]:
            sections.append("### 🔵 Low Severity")
            sections.append("")
            for vuln in by_severity[VulnerabilitySeverity.LOW]:
                sections.append(self._format_vulnerability(vuln))

        # Informational
        if by_severity[VulnerabilitySeverity.INFO]:
            sections.append("### ℹ️ Informational")
            sections.append("")
            for vuln in by_severity[VulnerabilitySeverity.INFO]:
                sections.append(self._format_vulnerability(vuln))

        return '\n'.join(sections)

    def _format_vulnerability(self, vuln: UnifiedVulnerability) -> str:
        """Format single vulnerability"""
        lines = [f"#### {vuln.title}", ""]
        lines.append(f"- **ID**: `{vuln.id}`")
        lines.append(f"- **Type**: {vuln.type}")
        lines.append(f"- **Location**: `{vuln.location.file}:{vuln.location.line}`")
        if vuln.location.function:
            lines.append(f"- **Function**: `{vuln.location.function}()`")
        lines.append(f"- **Detected by**: {vuln.detected_by}")
        if vuln.confirmed_by:
            lines.append(f"- **Confirmed by**: {', '.join(vuln.confirmed_by)}")
        lines.append("")

        lines.append(vuln.description)
        lines.append("")

        if vuln.recommendation:
            lines.append("**Recommendation**: " + vuln.recommendation)
            lines.append("")

        lines.append("---")
        lines.append("")

        return '\n'.join(lines)

    def _generate_synthesis(self, report: AuditReport) -> str:
        """Generate AI synthesis section"""
        return f"""## AI Analysis

{report.synthesis}"""

    def _generate_recommendations(self, report: AuditReport) -> str:
        """Generate recommendations section"""
        lines = ["## Recommendations", ""]

        if report.critical_count > 0:
            lines.append("### Immediate Actions")
            lines.append("")
            lines.append("1. **Do not deploy** to production until critical vulnerabilities are fixed")
            lines.append("2. Review and implement fixes for all critical findings")
            lines.append("3. Re-run security audit after fixes")
            lines.append("")

        if report.high_count > 0:
            lines.append("### High Priority")
            lines.append("")
            lines.append("1. Address all high-severity vulnerabilities before deployment")
            lines.append("2. Review economic attack vectors (flash loans, oracle manipulation)")
            lines.append("3. Implement additional testing for edge cases")
            lines.append("")

        if report.medium_count > 0:
            lines.append("### Medium Priority")
            lines.append("")
            lines.append("1. Review and fix medium-severity issues")
            lines.append("2. Add additional input validation and access controls")
            lines.append("3. Consider formal verification for critical functions")
            lines.append("")

        # Custom recommendations
        if report.recommended_actions:
            lines.append("### Additional Recommendations")
            lines.append("")
            for action in report.recommended_actions:
                lines.append(f"- {action}")
            lines.append("")

        return '\n'.join(lines)

    def _generate_tool_summary(self, report: AuditReport) -> str:
        """Generate tool execution summary"""
        lines = ["## Tool Summary", ""]

        if report.tools_executed:
            lines.append("### Tools Successfully Executed")
            lines.append("")
            for tool in report.tools_executed:
                lines.append(f"- ✅ {tool}")
            lines.append("")

        if report.tools_failed:
            lines.append("### Tools Failed")
            lines.append("")
            for tool in report.tools_failed:
                lines.append(f"- ❌ {tool}")
            lines.append("")

        if report.warning_messages:
            lines.append("### Warnings")
            lines.append("")
            for key, message in report.warning_messages.items():
                lines.append(f"- **{key}**: {message}")
            lines.append("")

        return '\n'.join(lines)

    def _generate_footer(self, report: AuditReport) -> str:
        """Generate report footer"""
        return f"""---

## Appendix

### Audit Configuration

- **Project Path**: `{report.project_path}`
- **Audit Mode**: {report.audit_mode}
- **Duration**: {report.duration_seconds:.1f} seconds

### Disclaimer

This automated security audit is provided as-is and should not be considered a substitute for professional security review. The absence of detected vulnerabilities does not guarantee the security of the smart contract. Always conduct thorough testing and consider professional audit services for high-value protocols.

### Report Generated

{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Unified Security Framework

---

*For questions or issues, refer to the documentation or submit an issue on GitHub.*"""

    def save(self, report: AuditReport, output_path: str):
        """
        Generate and save markdown report to file

        Args:
            report: Audit report
            output_path: Path to save markdown file
        """
        markdown_content = self.generate(report)

        # Create parent directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
