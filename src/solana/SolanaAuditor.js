/**
 * SolanaAuditor - Coordinates Solana/Rust security tools
 */

const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs').promises;
const path = require('path');
const Logger = require('../core/Logger');

const execAsync = promisify(exec);

class SolanaAuditor {
    constructor(config) {
        this.config = config;
        this.logger = new Logger(config.verbosity);
        this.tools = config.tools?.solana || ['cargo-audit', 'clippy'];
        this.findings = [];
    }

    /**
     * Run complete Solana audit
     */
    async audit() {
        this.logger.section('Solana Security Audit');

        const results = {
            findings: [],
            tools: {},
            metadata: {
                startTime: new Date(),
                chain: 'solana',
                tools: this.tools
            }
        };

        // Run each tool
        for (const tool of this.tools) {
            try {
                this.logger.info(`Running ${tool}...`);
                const toolResults = await this.runTool(tool);
                results.tools[tool] = toolResults;
                results.findings.push(...toolResults.findings);
                this.logger.success(`${tool} completed: ${toolResults.findings.length} findings`);
            } catch (error) {
                this.logger.error(`${tool} failed: ${error.message}`);
                results.tools[tool] = { error: error.message, findings: [] };
            }
        }

        results.metadata.endTime = new Date();
        return results;
    }

    /**
     * Run individual security tool
     */
    async runTool(tool) {
        switch (tool) {
            case 'cargo-audit':
                return await this.runCargoAudit();
            case 'clippy':
                return await this.runClippy();
            case 'anchor-test':
                return await this.runAnchorTests();
            default:
                throw new Error(`Unknown tool: ${tool}`);
        }
    }

    /**
     * Run cargo audit for dependency vulnerabilities
     */
    async runCargoAudit() {
        try {
            const command = 'cargo audit --json';
            const { stdout } = await execAsync(command, {
                cwd: this.config.projectPath
            });

            const auditOutput = JSON.parse(stdout);
            return {
                findings: this.parseCargoAuditFindings(auditOutput),
                raw: auditOutput
            };

        } catch (error) {
            // cargo audit returns non-zero when vulnerabilities found
            if (error.stdout) {
                try {
                    const auditOutput = JSON.parse(error.stdout);
                    return {
                        findings: this.parseCargoAuditFindings(auditOutput),
                        raw: auditOutput
                    };
                } catch (parseError) {
                    throw error;
                }
            }
            throw error;
        }
    }

    /**
     * Parse cargo audit findings
     */
    parseCargoAuditFindings(auditOutput) {
        const findings = [];

        if (!auditOutput.vulnerabilities || !auditOutput.vulnerabilities.list) {
            return findings;
        }

        for (const vuln of auditOutput.vulnerabilities.list) {
            findings.push({
                tool: 'cargo-audit',
                severity: this.mapRustSecSeverity(vuln.advisory.cvss),
                title: vuln.advisory.title,
                description: vuln.advisory.description,
                category: 'dependency-vulnerability',
                package: vuln.package.name,
                version: vuln.package.version,
                patchedVersions: vuln.advisory.patched_versions,
                rustsecId: vuln.advisory.id,
                references: [
                    vuln.advisory.url,
                    ...(vuln.advisory.references || [])
                ]
            });
        }

        return findings;
    }

    /**
     * Map RustSec severity (CVSS) to standard format
     */
    mapRustSecSeverity(cvss) {
        if (!cvss) return 'medium';

        if (cvss >= 9.0) return 'critical';
        if (cvss >= 7.0) return 'high';
        if (cvss >= 4.0) return 'medium';
        return 'low';
    }

    /**
     * Run Clippy linter
     */
    async runClippy() {
        try {
            const command = 'cargo clippy --message-format=json -- -D warnings -D clippy::integer_arithmetic -W clippy::unwrap_used';
            const { stdout } = await execAsync(command, {
                cwd: this.config.projectPath
            });

            const clippyLines = stdout.split('\n').filter(l => l.trim());
            const clippyMessages = clippyLines
                .map(line => {
                    try {
                        return JSON.parse(line);
                    } catch {
                        return null;
                    }
                })
                .filter(msg => msg && msg.message);

            return {
                findings: this.parseClippyFindings(clippyMessages),
                raw: clippyMessages
            };

        } catch (error) {
            if (error.stdout) {
                const clippyLines = error.stdout.split('\n').filter(l => l.trim());
                const clippyMessages = clippyLines
                    .map(line => {
                        try {
                            return JSON.parse(line);
                        } catch {
                            return null;
                        }
                    })
                    .filter(msg => msg && msg.message);

                return {
                    findings: this.parseClippyFindings(clippyMessages),
                    raw: clippyMessages
                };
            }
            throw error;
        }
    }

    /**
     * Parse Clippy findings
     */
    parseClippyFindings(clippyMessages) {
        const findings = [];

        for (const msg of clippyMessages) {
            if (!msg.message || msg.message.level === 'help') continue;

            const spans = msg.message.spans || [];
            const primarySpan = spans.find(s => s.is_primary) || spans[0];

            findings.push({
                tool: 'clippy',
                severity: this.mapClippySeverity(msg.message.level, msg.message.code?.code),
                title: msg.message.message,
                description: this.formatClippyMessage(msg.message),
                category: this.categorizeClippyLint(msg.message.code?.code),
                file: primarySpan?.file_name,
                line: primarySpan?.line_start,
                column: primarySpan?.column_start,
                codeSnippet: primarySpan?.text?.[0]?.text,
                lintName: msg.message.code?.code,
                remediation: this.getClippyRemediation(msg.message.code?.code)
            });
        }

        return findings;
    }

    /**
     * Map Clippy severity
     */
    mapClippySeverity(level, lintCode) {
        // Specific security-critical lints
        const criticalLints = ['integer_arithmetic', 'unwrap_used', 'expect_used', 'panic'];
        if (lintCode && criticalLints.some(l => lintCode.includes(l))) {
            return 'high';
        }

        const mapping = {
            'error': 'high',
            'warning': 'medium',
            'note': 'low'
        };
        return mapping[level] || 'medium';
    }

    /**
     * Categorize Clippy lint
     */
    categorizeClippyLint(lintCode) {
        if (!lintCode) return 'code-quality';

        const categories = {
            'integer-safety': ['integer_arithmetic', 'integer_overflow', 'checked_conversions'],
            'memory-safety': ['unwrap_used', 'expect_used', 'panic', 'indexing_slicing'],
            'logic-errors': ['comparison', 'if_same_then_else'],
            'best-practices': ['needless', 'redundant', 'style']
        };

        for (const [category, lints] of Object.entries(categories)) {
            if (lints.some(l => lintCode.includes(l))) {
                return category;
            }
        }

        return 'code-quality';
    }

    /**
     * Format Clippy message
     */
    formatClippyMessage(message) {
        let text = message.message;

        if (message.children && message.children.length > 0) {
            const suggestions = message.children
                .filter(c => c.message)
                .map(c => c.message)
                .join('\n');

            if (suggestions) {
                text += '\n\nSuggestions:\n' + suggestions;
            }
        }

        return text;
    }

    /**
     * Get Clippy remediation advice
     */
    getClippyRemediation(lintCode) {
        const remediations = {
            'integer_arithmetic': 'Use checked arithmetic methods like checked_add(), checked_sub(), etc.',
            'unwrap_used': 'Handle Result/Option explicitly instead of using unwrap()',
            'expect_used': 'Handle errors properly instead of using expect()',
            'indexing_slicing': 'Use get() method with bounds checking instead of direct indexing'
        };

        if (!lintCode) return 'Follow Clippy suggestions';

        for (const [lint, remediation] of Object.entries(remediations)) {
            if (lintCode.includes(lint)) {
                return remediation;
            }
        }

        return 'Review Clippy documentation for this lint';
    }

    /**
     * Run Anchor tests
     */
    async runAnchorTests() {
        try {
            // Check if this is an Anchor project
            const anchorTomlPath = path.join(this.config.projectPath, 'Anchor.toml');
            await fs.access(anchorTomlPath);

            const command = 'anchor test --skip-local-validator';
            const { stdout, stderr } = await execAsync(command, {
                cwd: this.config.projectPath,
                timeout: 180000 // 3 minute timeout
            });

            return {
                findings: this.parseAnchorTestResults(stdout + stderr),
                raw: { stdout, stderr }
            };

        } catch (error) {
            if (error.code === 'ENOENT') {
                this.logger.info('Not an Anchor project, skipping Anchor tests');
                return { findings: [], raw: null };
            }

            // Parse test failures from error output
            if (error.stdout || error.stderr) {
                return {
                    findings: this.parseAnchorTestResults((error.stdout || '') + (error.stderr || '')),
                    raw: { stdout: error.stdout, stderr: error.stderr }
                };
            }

            throw error;
        }
    }

    /**
     * Parse Anchor test results
     */
    parseAnchorTestResults(output) {
        const findings = [];

        // Look for test failures
        const failurePattern = /FAILED.*test (\w+)/gi;
        const matches = output.matchAll(failurePattern);

        for (const match of matches) {
            findings.push({
                tool: 'anchor-test',
                severity: 'high',
                title: `Test failed: ${match[1]}`,
                description: 'Anchor test failure detected',
                category: 'test-failure',
                testName: match[1]
            });
        }

        // Look for panics/errors
        const errorPattern = /Error: (.+)/gi;
        const errors = output.matchAll(errorPattern);

        for (const error of errors) {
            findings.push({
                tool: 'anchor-test',
                severity: 'medium',
                title: 'Program error detected',
                description: error[1],
                category: 'runtime-error'
            });
        }

        return findings;
    }
}

module.exports = SolanaAuditor;
