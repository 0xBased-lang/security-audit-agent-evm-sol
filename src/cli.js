#!/usr/bin/env node

/**
 * CLI - Command-line interface for the security audit framework
 */

const { program } = require('commander');
const chalk = require('chalk');
const ora = require('ora');
const path = require('path');
const AuditOrchestrator = require('./core/AuditOrchestrator');
const pkg = require('../package.json');

program
    .name('blockchain-audit')
    .description('AI-powered blockchain security auditing framework for EVM and Solana')
    .version(pkg.version);

program
    .command('audit')
    .description('Run security audit on a blockchain project')
    .option('-c, --chain <type>', 'Chain type: evm, solana, or auto', 'auto')
    .option('-p, --project <path>', 'Project path', process.cwd())
    .option('-o, --output <dir>', 'Output directory', './audit-results')
    .option('--format <format>', 'Report format: markdown, html, json', 'markdown')
    .option('--tools <tools>', 'Comma-separated list of tools to use')
    .option('--include-formal', 'Include formal verification (Certora)')
    .option('--parallel', 'Run tools in parallel', true)
    .option('--no-parallel', 'Run tools sequentially')
    .option('-v, --verbose', 'Verbose output')
    .option('-q, --quiet', 'Quiet mode')
    .action(async (options) => {
        try {
            const spinner = ora('Initializing audit...').start();

            // Parse tools if specified
            let tools = undefined;
            if (options.tools) {
                const toolList = options.tools.split(',').map(t => t.trim());
                tools = {
                    evm: toolList.filter(t => ['slither', 'mythril', 'echidna', 'foundry', 'certora'].includes(t)),
                    solana: toolList.filter(t => ['cargo-audit', 'clippy', 'anchor-test'].includes(t))
                };
            }

            const config = {
                chain: options.chain,
                projectPath: path.resolve(options.project),
                outputDir: path.resolve(options.output),
                reportFormat: options.format,
                tools,
                includeFormal: options.includeFormal,
                parallel: options.parallel,
                verbosity: options.verbose ? 'verbose' : options.quiet ? 'silent' : 'normal'
            };

            spinner.stop();

            const orchestrator = new AuditOrchestrator(config);
            const result = await orchestrator.runAudit();

            if (result.success) {
                console.log('\n' + chalk.green.bold('✅ Audit completed successfully!'));
                console.log(chalk.cyan(`📄 Report: ${result.reportPath}`));

                const stats = orchestrator.getStatistics();
                console.log('\n' + chalk.bold('Summary:'));
                console.log(`  Total findings: ${stats.total}`);
                console.log(`  ${chalk.red('Critical')}: ${stats.critical}`);
                console.log(`  ${chalk.yellow('High')}: ${stats.high}`);
                console.log(`  ${chalk.blue('Medium')}: ${stats.medium}`);
                console.log(`  ${chalk.green('Low')}: ${stats.low}`);
                console.log(`  ${chalk.gray('Informational')}: ${stats.informational}`);

                if (result.results.aiAnalysis) {
                    console.log('\n' + chalk.bold('AI Risk Assessment:'));
                    console.log(`  Risk Level: ${chalk.yellow(result.results.aiAnalysis.riskAssessment.level)}`);
                    console.log(`  Deployment: ${result.results.aiAnalysis.riskAssessment.deploymentRecommendation}`);
                }

                process.exit(0);
            }
        } catch (error) {
            console.error(chalk.red('\n❌ Audit failed:'), error.message);
            if (options.verbose) {
                console.error(error.stack);
            }
            process.exit(1);
        }
    });

program
    .command('report')
    .description('Generate report from existing audit results')
    .option('-i, --input <file>', 'Input JSON results file')
    .option('-o, --output <dir>', 'Output directory', './audit-results')
    .option('--format <format>', 'Report format: markdown, html, json', 'markdown')
    .action(async (options) => {
        const fs = require('fs').promises;
        const ReportGenerator = require('./reports/ReportGenerator');

        try {
            console.log(chalk.cyan('Generating report...'));

            const results = JSON.parse(await fs.readFile(options.input, 'utf-8'));

            const generator = new ReportGenerator({
                outputDir: options.output,
                format: options.format
            });

            const report = await generator.generate(results);

            console.log(chalk.green(`✅ Report generated: ${report.path}`));
        } catch (error) {
            console.error(chalk.red('❌ Report generation failed:'), error.message);
            process.exit(1);
        }
    });

program
    .command('tools')
    .description('Check installed security tools')
    .action(async () => {
        const { exec } = require('child_process');
        const { promisify } = require('util');
        const execAsync = promisify(exec);

        console.log(chalk.bold('\nChecking installed tools...\n'));

        const tools = [
            { name: 'slither', command: 'slither --version', chain: 'EVM' },
            { name: 'mythril', command: 'myth version', chain: 'EVM' },
            { name: 'echidna', command: 'echidna --version', chain: 'EVM' },
            { name: 'foundry', command: 'forge --version', chain: 'EVM' },
            { name: 'cargo-audit', command: 'cargo audit --version', chain: 'Solana' },
            { name: 'clippy', command: 'cargo clippy --version', chain: 'Solana' },
            { name: 'anchor', command: 'anchor --version', chain: 'Solana' }
        ];

        for (const tool of tools) {
            try {
                await execAsync(tool.command);
                console.log(chalk.green('✓'), chalk.bold(tool.name), chalk.gray(`(${tool.chain})`));
            } catch (error) {
                console.log(chalk.red('✗'), chalk.bold(tool.name), chalk.gray(`(${tool.chain}) - Not installed`));
            }
        }

        console.log('\n');
    });

program.parse();
