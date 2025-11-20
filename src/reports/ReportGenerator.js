/**
 * ReportGenerator - Creates comprehensive audit reports in multiple formats
 */

const fs = require('fs').promises;
const path = require('path');
const Logger = require('../core/Logger');

class ReportGenerator {
    constructor(config) {
        this.config = {
            outputDir: config.outputDir || './audit-results',
            format: config.format || 'markdown',
            verbosity: config.verbosity || 'normal',
            ...config
        };
        this.logger = new Logger(this.config.verbosity);
    }

    /**
     * Generate audit report
     */
    async generate(results) {
        // Ensure output directory exists
        await fs.mkdir(this.config.outputDir, { recursive: true });

        const format = this.config.format;
        let reportPath;

        switch (format) {
            case 'markdown':
                reportPath = await this.generateMarkdown(results);
                break;
            case 'html':
                reportPath = await this.generateHTML(results);
                break;
            case 'json':
                reportPath = await this.generateJSON(results);
                break;
            default:
                reportPath = await this.generateMarkdown(results);
        }

        return {
            path: reportPath,
            format
        };
    }

    /**
     * Generate Markdown report
     */
    async generateMarkdown(results) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportPath = path.join(this.config.outputDir, `audit-report-${timestamp}.md`);

        const content = this.buildMarkdownReport(results);
        await fs.writeFile(reportPath, content, 'utf-8');

        return reportPath;
    }

    /**
     * Build Markdown report content
     */
    buildMarkdownReport(results) {
        const { aiAnalysis, metadata } = results;
        const allFindings = [
            ...(results.evm?.findings || []),
            ...(results.solana?.findings || [])
        ];

        const stats = this.getStatistics(allFindings);

        let md = `# Security Audit Report

**Generated**: ${new Date().toLocaleString()}
**Project Path**: ${metadata.projectPath}
**Chain**: ${metadata.chain.toUpperCase()}
**Duration**: ${this.formatDuration(metadata.duration)}

---

## Executive Summary

`;

        if (aiAnalysis) {
            md += `### Overall Risk Assessment

**Risk Level**: ${aiAnalysis.riskAssessment.level}
**Confidence**: ${aiAnalysis.riskAssessment.confidence}
**Deployment Recommendation**: ${aiAnalysis.riskAssessment.deploymentRecommendation}

${aiAnalysis.riskAssessment.justification}

`;
        }

        md += `### Findings Summary

- **Total Findings**: ${stats.total}
- **Critical**: ${stats.critical} 🔴
- **High**: ${stats.high} 🟠
- **Medium**: ${stats.medium} 🟡
- **Low**: ${stats.low} 🟢
- **Informational**: ${stats.informational} ℹ️

---

## Detailed Findings

`;

        // Group findings by severity
        const bySeverity = {
            critical: [],
            high: [],
            medium: [],
            low: [],
            informational: []
        };

        for (const finding of allFindings) {
            const severity = finding.severity || 'informational';
            if (bySeverity[severity]) {
                bySeverity[severity].push(finding);
            }
        }

        // Report each severity level
        for (const severity of ['critical', 'high', 'medium', 'low', 'informational']) {
            const findings = bySeverity[severity];
            if (findings.length === 0) continue;

            md += `### ${severity.toUpperCase()} Severity (${findings.length})\n\n`;

            for (let i = 0; i < findings.length; i++) {
                const finding = findings[i];
                md += this.formatFinding(finding, i + 1);
            }
        }

        // AI Analysis section
        if (aiAnalysis && aiAnalysis.analyses) {
            md += `\n---\n\n## AI-Powered Analysis\n\n`;

            for (const analysis of aiAnalysis.analyses) {
                md += `### ${analysis.category} (${analysis.findingsCount} findings)\n\n`;
                md += `${analysis.rawAnalysis}\n\n`;
            }
        }

        // Cross-reference
        if (aiAnalysis?.crossReference) {
            md += `\n---\n\n## Cross-Reference Analysis\n\n`;
            md += aiAnalysis.crossReference.analysis + '\n\n';
        }

        // Recommendations
        if (aiAnalysis?.recommendations) {
            md += `\n---\n\n## Recommendations\n\n`;
            md += aiAnalysis.recommendations.text + '\n\n';
        }

        // Tools used
        md += `\n---\n\n## Tools Used\n\n`;
        if (results.evm) {
            md += `### EVM Tools\n\n`;
            for (const [tool, data] of Object.entries(results.evm.tools || {})) {
                md += `- **${tool}**: ${data.findings?.length || 0} findings\n`;
            }
        }
        if (results.solana) {
            md += `\n### Solana Tools\n\n`;
            for (const [tool, data] of Object.entries(results.solana.tools || {})) {
                md += `- **${tool}**: ${data.findings?.length || 0} findings\n`;
            }
        }

        md += `\n---\n\n*Report generated by AI-Powered Blockchain Security Auditing Framework*\n`;

        return md;
    }

    /**
     * Format individual finding
     */
    formatFinding(finding, number) {
        let md = `#### ${number}. ${finding.title || 'Untitled Issue'}\n\n`;

        md += `**Tool**: ${finding.tool}\n`;
        md += `**Category**: ${finding.category || 'N/A'}\n`;

        if (finding.file) {
            md += `**Location**: \`${finding.file}\``;
            if (finding.line) md += `:${finding.line}`;
            md += '\n';
        }

        if (finding.confidence) {
            md += `**Confidence**: ${finding.confidence}\n`;
        }

        md += `\n**Description**:\n${finding.description}\n\n`;

        if (finding.codeSnippet) {
            md += `**Code Snippet**:\n\`\`\`solidity\n${finding.codeSnippet}\n\`\`\`\n\n`;
        }

        if (finding.remediation) {
            md += `**Remediation**: ${finding.remediation}\n\n`;
        }

        if (finding.references && finding.references.length > 0) {
            md += `**References**:\n`;
            for (const ref of finding.references) {
                md += `- ${ref}\n`;
            }
            md += '\n';
        }

        md += `---\n\n`;

        return md;
    }

    /**
     * Generate JSON report
     */
    async generateJSON(results) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportPath = path.join(this.config.outputDir, `audit-report-${timestamp}.json`);

        const jsonReport = {
            generatedAt: new Date().toISOString(),
            metadata: results.metadata,
            statistics: this.getStatistics([
                ...(results.evm?.findings || []),
                ...(results.solana?.findings || [])
            ]),
            findings: [
                ...(results.evm?.findings || []),
                ...(results.solana?.findings || [])
            ],
            aiAnalysis: results.aiAnalysis,
            toolResults: {
                evm: results.evm,
                solana: results.solana
            }
        };

        await fs.writeFile(reportPath, JSON.stringify(jsonReport, null, 2), 'utf-8');

        return reportPath;
    }

    /**
     * Generate HTML report
     */
    async generateHTML(results) {
        const mdReport = this.buildMarkdownReport(results);
        const marked = require('marked');
        const html = marked.parse(mdReport);

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportPath = path.join(this.config.outputDir, `audit-report-${timestamp}.html`);

        const fullHTML = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Security Audit Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }
        h3 { color: #7f8c8d; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
        pre { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .critical { color: #e74c3c; font-weight: bold; }
        .high { color: #e67e22; font-weight: bold; }
        .medium { color: #f39c12; font-weight: bold; }
        .low { color: #27ae60; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #3498db; color: white; }
    </style>
</head>
<body>
${html}
</body>
</html>`;

        await fs.writeFile(reportPath, fullHTML, 'utf-8');

        return reportPath;
    }

    /**
     * Calculate statistics
     */
    getStatistics(findings) {
        const stats = {
            total: findings.length,
            critical: 0,
            high: 0,
            medium: 0,
            low: 0,
            informational: 0
        };

        for (const finding of findings) {
            const severity = finding.severity || 'informational';
            stats[severity] = (stats[severity] || 0) + 1;
        }

        return stats;
    }

    /**
     * Format duration
     */
    formatDuration(ms) {
        if (!ms) return 'N/A';

        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);

        if (hours > 0) {
            return `${hours}h ${minutes % 60}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        } else {
            return `${seconds}s`;
        }
    }
}

module.exports = ReportGenerator;
