/**
 * AuditOrchestrator - Main AI-powered audit orchestration engine
 * Coordinates all security tools and performs intelligent analysis
 */

const { EventEmitter } = require('events');
const path = require('path');
const fs = require('fs').promises;
const EVMAuditor = require('../evm/EVMAuditor');
const SolanaAuditor = require('../solana/SolanaAuditor');
const AIAnalyzer = require('./AIAnalyzer');
const ReportGenerator = require('../reports/ReportGenerator');
const Logger = require('./Logger');

class AuditOrchestrator extends EventEmitter {
    constructor(config = {}) {
        super();

        this.config = {
            chain: config.chain || 'auto', // 'evm', 'solana', or 'auto'
            projectPath: config.projectPath || process.cwd(),
            outputDir: config.outputDir || './audit-results',
            tools: config.tools || {
                evm: ['slither', 'mythril', 'foundry'],
                solana: ['cargo-audit', 'clippy', 'anchor-test']
            },
            includeFormal: config.includeFormal || false, // Include Certora/formal verification
            parallel: config.parallel !== false, // Run tools in parallel by default
            aiModel: config.aiModel || 'claude-sonnet-4-5',
            verbosity: config.verbosity || 'normal', // 'silent', 'normal', 'verbose'
            ...config
        };

        this.logger = new Logger(this.config.verbosity);
        this.results = {
            evm: null,
            solana: null,
            aiAnalysis: null,
            metadata: {
                startTime: null,
                endTime: null,
                duration: null,
                chain: this.config.chain,
                projectPath: this.config.projectPath
            }
        };
    }

    /**
     * Main audit execution method
     */
    async runAudit() {
        try {
            this.logger.info('🔍 Starting blockchain security audit...');
            this.results.metadata.startTime = new Date();

            // Detect chain type if auto
            if (this.config.chain === 'auto') {
                this.config.chain = await this.detectChainType();
                this.logger.info(`Detected chain type: ${this.config.chain}`);
            }

            // Run chain-specific audits
            await this.runChainAudits();

            // AI-powered analysis
            await this.runAIAnalysis();

            // Generate report
            const report = await this.generateReport();

            this.results.metadata.endTime = new Date();
            this.results.metadata.duration =
                this.results.metadata.endTime - this.results.metadata.startTime;

            this.logger.success(`✅ Audit completed in ${this.formatDuration(this.results.metadata.duration)}`);

            return {
                success: true,
                results: this.results,
                reportPath: report.path
            };

        } catch (error) {
            this.logger.error(`❌ Audit failed: ${error.message}`);
            throw error;
        }
    }

    /**
     * Detect chain type based on project files
     */
    async detectChainType() {
        const files = await this.getProjectFiles();

        const hasSolidity = files.some(f => f.endsWith('.sol'));
        const hasRust = files.some(f => f.endsWith('.rs'));
        const hasAnchor = await this.fileExists(path.join(this.config.projectPath, 'Anchor.toml'));
        const hasFoundry = await this.fileExists(path.join(this.config.projectPath, 'foundry.toml'));
        const hasHardhat = await this.fileExists(path.join(this.config.projectPath, 'hardhat.config.js'));

        if (hasAnchor || (hasRust && !hasSolidity)) {
            return 'solana';
        } else if (hasSolidity || hasFoundry || hasHardhat) {
            return 'evm';
        }

        throw new Error('Unable to detect chain type. Please specify with --chain flag.');
    }

    /**
     * Run chain-specific audits
     */
    async runChainAudits() {
        if (this.config.chain === 'evm' || this.config.chain === 'both') {
            this.logger.info('🔧 Running EVM security audit...');
            const evmAuditor = new EVMAuditor(this.config);
            this.results.evm = await evmAuditor.audit();
            this.logger.success(`✓ EVM audit completed (${this.results.evm.findings.length} findings)`);
        }

        if (this.config.chain === 'solana' || this.config.chain === 'both') {
            this.logger.info('🔧 Running Solana security audit...');
            const solanaAuditor = new SolanaAuditor(this.config);
            this.results.solana = await solanaAuditor.audit();
            this.logger.success(`✓ Solana audit completed (${this.results.solana.findings.length} findings)`);
        }
    }

    /**
     * AI-powered analysis using Claude
     */
    async runAIAnalysis() {
        this.logger.info('🤖 Running AI-powered vulnerability analysis...');

        const aiAnalyzer = new AIAnalyzer({
            model: this.config.aiModel,
            verbosity: this.config.verbosity
        });

        // Combine all findings
        const allFindings = [
            ...(this.results.evm?.findings || []),
            ...(this.results.solana?.findings || [])
        ];

        // Read source files for context
        const sourceFiles = await this.getRelevantSourceFiles(allFindings);

        // Perform AI analysis
        this.results.aiAnalysis = await aiAnalyzer.analyze({
            findings: allFindings,
            sourceFiles,
            chain: this.config.chain,
            projectPath: this.config.projectPath
        });

        this.logger.success('✓ AI analysis completed');
    }

    /**
     * Generate comprehensive audit report
     */
    async generateReport() {
        this.logger.info('📄 Generating audit report...');

        const reportGenerator = new ReportGenerator({
            outputDir: this.config.outputDir,
            format: this.config.reportFormat || 'markdown', // markdown, pdf, html
            verbosity: this.config.verbosity
        });

        const report = await reportGenerator.generate(this.results);

        this.logger.success(`✓ Report generated: ${report.path}`);

        return report;
    }

    /**
     * Get all project files
     */
    async getProjectFiles() {
        const { glob } = require('glob');
        const patterns = [
            '**/*.sol',
            '**/*.rs',
            'Cargo.toml',
            'foundry.toml',
            'hardhat.config.js',
            'Anchor.toml'
        ];

        const files = [];
        for (const pattern of patterns) {
            const matches = await glob(pattern, {
                cwd: this.config.projectPath,
                ignore: ['node_modules/**', 'target/**', 'out/**', 'artifacts/**']
            });
            files.push(...matches);
        }

        return files;
    }

    /**
     * Get relevant source files for findings
     */
    async getRelevantSourceFiles(findings) {
        const fileSet = new Set();

        for (const finding of findings) {
            if (finding.file) {
                fileSet.add(finding.file);
            }
        }

        const sourceFiles = {};
        for (const file of fileSet) {
            const filePath = path.join(this.config.projectPath, file);
            try {
                sourceFiles[file] = await fs.readFile(filePath, 'utf-8');
            } catch (error) {
                this.logger.warn(`Could not read file: ${file}`);
            }
        }

        return sourceFiles;
    }

    /**
     * Check if file exists
     */
    async fileExists(filePath) {
        try {
            await fs.access(filePath);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Format duration in human-readable format
     */
    formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);

        if (hours > 0) {
            return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        } else {
            return `${seconds}s`;
        }
    }

    /**
     * Get audit statistics
     */
    getStatistics() {
        const allFindings = [
            ...(this.results.evm?.findings || []),
            ...(this.results.solana?.findings || [])
        ];

        const stats = {
            total: allFindings.length,
            critical: 0,
            high: 0,
            medium: 0,
            low: 0,
            informational: 0,
            byTool: {},
            byCategory: {}
        };

        for (const finding of allFindings) {
            // Count by severity
            const severity = finding.severity?.toLowerCase() || 'informational';
            stats[severity] = (stats[severity] || 0) + 1;

            // Count by tool
            const tool = finding.tool || 'unknown';
            stats.byTool[tool] = (stats.byTool[tool] || 0) + 1;

            // Count by category
            const category = finding.category || 'uncategorized';
            stats.byCategory[category] = (stats.byCategory[category] || 0) + 1;
        }

        return stats;
    }
}

module.exports = AuditOrchestrator;
