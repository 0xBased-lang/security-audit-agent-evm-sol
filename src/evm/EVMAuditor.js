/**
 * EVMAuditor - Coordinates EVM/Solidity security tools
 */

const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs').promises;
const path = require('path');
const Logger = require('../core/Logger');

const execAsync = promisify(exec);

class EVMAuditor {
    constructor(config) {
        this.config = config;
        this.logger = new Logger(config.verbosity);
        this.tools = config.tools?.evm || ['slither', 'foundry'];
        this.findings = [];
    }

    /**
     * Run complete EVM audit
     */
    async audit() {
        this.logger.section('EVM Security Audit');

        const results = {
            findings: [],
            tools: {},
            metadata: {
                startTime: new Date(),
                chain: 'evm',
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
            case 'slither':
                return await this.runSlither();
            case 'mythril':
                return await this.runMythril();
            case 'echidna':
                return await this.runEchidna();
            case 'foundry':
                return await this.runFoundry();
            case 'certora':
                return await this.runCertora();
            default:
                throw new Error(`Unknown tool: ${tool}`);
        }
    }

    /**
     * Run Slither static analysis
     */
    async runSlither() {
        const outputPath = path.join(this.config.outputDir, 'slither.json');

        // Check if contracts directory exists, otherwise use project path
        const contractsDir = path.join(this.config.projectPath, 'contracts');
        let targetPath;
        try {
            await fs.access(contractsDir);
            targetPath = contractsDir;
        } catch {
            // No contracts directory, use project path directly
            targetPath = this.config.projectPath;
        }

        try {
            // Find Solidity files
            const solidityFiles = await this.findSolidityFiles();
            if (solidityFiles.length === 0) {
                return { findings: [], raw: null };
            }

            const command = `slither "${targetPath}" --json "${outputPath}" --filter-paths "node_modules"`;

            this.logger.verbose(`Executing: ${command}`);
            await execAsync(command, { cwd: this.config.projectPath });

            // Parse results
            const rawOutput = await fs.readFile(outputPath, 'utf-8');
            const slitherOutput = JSON.parse(rawOutput);

            return {
                findings: this.parseSlitherFindings(slitherOutput),
                raw: slitherOutput
            };

        } catch (error) {
            // Slither returns non-zero exit code when it finds issues
            if (error.stdout) {
                try {
                    const rawOutput = await fs.readFile(outputPath, 'utf-8');
                    const slitherOutput = JSON.parse(rawOutput);
                    return {
                        findings: this.parseSlitherFindings(slitherOutput),
                        raw: slitherOutput
                    };
                } catch (parseError) {
                    throw error;
                }
            }
            throw error;
        }
    }

    /**
     * Parse Slither findings into standard format
     */
    parseSlitherFindings(slitherOutput) {
        const findings = [];

        if (!slitherOutput.results || !slitherOutput.results.detectors) {
            return findings;
        }

        for (const detector of slitherOutput.results.detectors) {
            const finding = {
                tool: 'slither',
                severity: this.mapSlitherSeverity(detector.impact),
                confidence: detector.confidence,
                title: detector.check,
                description: detector.description,
                category: this.categorizeSlitherCheck(detector.check),
                elements: detector.elements,
                file: this.extractFileFromElements(detector.elements),
                line: this.extractLineFromElements(detector.elements),
                codeSnippet: this.extractCodeSnippet(detector.elements),
                remediation: this.getSlitherRemediation(detector.check),
                references: [`https://github.com/crytic/slither/wiki/Detector-Documentation#${detector.check}`]
            };

            findings.push(finding);
        }

        return findings;
    }

    /**
     * Map Slither severity to standard format
     */
    mapSlitherSeverity(impact) {
        const mapping = {
            'High': 'critical',
            'Medium': 'high',
            'Low': 'medium',
            'Informational': 'low'
        };
        return mapping[impact] || 'medium';
    }

    /**
     * Categorize Slither check types
     */
    categorizeSlitherCheck(check) {
        const categories = {
            'reentrancy': ['reentrancy-eth', 'reentrancy-no-eth', 'reentrancy-benign'],
            'access-control': ['suicidal', 'unprotected-upgrade', 'arbitrary-send-eth'],
            'arithmetic': ['divide-before-multiply', 'weak-prng'],
            'external-calls': ['unchecked-transfer', 'unchecked-lowlevel', 'unchecked-send'],
            'logic-errors': ['incorrect-equality', 'dangerous-strict-equalities'],
            'best-practices': ['naming-convention', 'solc-version', 'pragma']
        };

        for (const [category, checks] of Object.entries(categories)) {
            if (checks.includes(check)) {
                return category;
            }
        }

        return 'other';
    }

    /**
     * Run Mythril symbolic execution
     */
    async runMythril() {
        const solidityFiles = await this.findSolidityFiles();
        if (solidityFiles.length === 0) {
            return { findings: [], raw: null };
        }

        const findings = [];

        // Run Mythril on each contract (can be slow)
        for (const file of solidityFiles.slice(0, 5)) { // Limit to first 5 contracts
            try {
                const command = `myth analyze ${file} -o json --max-depth 50`;
                this.logger.verbose(`Analyzing ${file} with Mythril...`);

                const { stdout } = await execAsync(command, {
                    cwd: this.config.projectPath,
                    timeout: 300000 // 5 minute timeout per contract
                });

                const mythrilOutput = JSON.parse(stdout);
                findings.push(...this.parseMythrilFindings(mythrilOutput, file));

            } catch (error) {
                this.logger.warn(`Mythril failed on ${file}: ${error.message}`);
            }
        }

        return { findings, raw: null };
    }

    /**
     * Parse Mythril findings
     */
    parseMythrilFindings(mythrilOutput, file) {
        const findings = [];

        if (!mythrilOutput.issues) {
            return findings;
        }

        for (const issue of mythrilOutput.issues) {
            findings.push({
                tool: 'mythril',
                severity: this.mapMythrilSeverity(issue.severity),
                title: issue.title,
                description: issue.description,
                category: this.categorizeMythrilIssue(issue.swc_id),
                file,
                line: issue.lineno,
                swc_id: issue.swc_id,
                references: [`https://swcregistry.io/docs/SWC-${issue.swc_id}`]
            });
        }

        return findings;
    }

    /**
     * Map Mythril severity
     */
    mapMythrilSeverity(severity) {
        const mapping = {
            'High': 'critical',
            'Medium': 'high',
            'Low': 'medium'
        };
        return mapping[severity] || 'medium';
    }

    /**
     * Categorize Mythril issues by SWC ID
     */
    categorizeMythrilIssue(swcId) {
        const categories = {
            'reentrancy': ['SWC-107'],
            'access-control': ['SWC-105', 'SWC-106', 'SWC-115'],
            'arithmetic': ['SWC-101'],
            'logic-errors': ['SWC-110', 'SWC-123'],
            'external-calls': ['SWC-104']
        };

        for (const [category, swcs] of Object.entries(categories)) {
            if (swcs.includes(swcId)) {
                return category;
            }
        }

        return 'other';
    }

    /**
     * Run Foundry tests
     */
    async runFoundry() {
        try {
            const command = 'forge test --json';
            const { stdout } = await execAsync(command, {
                cwd: this.config.projectPath
            });

            const testResults = JSON.parse(stdout);
            return {
                findings: this.parseFoundryResults(testResults),
                raw: testResults
            };

        } catch (error) {
            this.logger.warn(`Foundry not found or tests failed: ${error.message}`);
            return { findings: [], raw: null };
        }
    }

    /**
     * Parse Foundry test results
     */
    parseFoundryResults(testResults) {
        const findings = [];

        // Convert test failures to findings
        if (testResults.failures) {
            for (const failure of testResults.failures) {
                findings.push({
                    tool: 'foundry',
                    severity: 'high',
                    title: `Test failed: ${failure.test}`,
                    description: failure.reason || 'Test assertion failed',
                    category: 'test-failure',
                    file: failure.contract
                });
            }
        }

        return findings;
    }

    /**
     * Run Echidna fuzzing
     */
    async runEchidna() {
        // Placeholder - requires specific test setup
        this.logger.info('Echidna requires manual property setup');
        return { findings: [], raw: null };
    }

    /**
     * Run Certora formal verification
     */
    async runCertora() {
        // Placeholder - requires CVL specs
        this.logger.info('Certora requires specification files');
        return { findings: [], raw: null };
    }

    /**
     * Find all Solidity files in project
     */
    async findSolidityFiles() {
        const { glob } = require('glob');
        return await glob('**/*.sol', {
            cwd: this.config.projectPath,
            ignore: ['node_modules/**', 'artifacts/**', 'cache/**']
        });
    }

    /**
     * Helper methods
     */
    extractFileFromElements(elements) {
        if (!elements || elements.length === 0) return null;
        return elements[0].source_mapping?.filename_short || null;
    }

    extractLineFromElements(elements) {
        if (!elements || elements.length === 0) return null;
        return elements[0].source_mapping?.lines?.[0] || null;
    }

    extractCodeSnippet(elements) {
        if (!elements || elements.length === 0) return null;
        // Would need to read file and extract lines
        return null;
    }

    getSlitherRemediation(check) {
        const remediations = {
            'reentrancy-eth': 'Apply checks-effects-interactions pattern or use ReentrancyGuard',
            'tx-origin': 'Use msg.sender instead of tx.origin for authentication',
            'unchecked-transfer': 'Use SafeERC20 library for token transfers',
            'suicidal': 'Add access control to selfdestruct functions'
        };
        return remediations[check] || 'Review and fix according to best practices';
    }
}

module.exports = EVMAuditor;
