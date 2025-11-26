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

                // Export JSON for Claude Code analysis
                await orchestrator.outputJSON();
                console.log(chalk.cyan('📁 JSON findings exported for Claude Code analysis'));

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
    .command('run-tools')
    .description('Run security tools and output JSON (for Claude Code integration)')
    .option('-c, --chain <type>', 'Chain type: evm, solana, or auto', 'auto')
    .option('-p, --project <path>', 'Project path', process.cwd())
    .option('-o, --output <file>', 'Output JSON file', './audit-results/findings.json')
    .option('--tools <tools>', 'Comma-separated list of tools to use')
    .action(async (options) => {
        try {
            console.log(chalk.cyan('Running security tools (JSON output for Claude Code)...'));

            // Parse tools if specified
            let tools = undefined;
            if (options.tools) {
                const toolList = options.tools.split(',').map(t => t.trim());
                tools = {
                    evm: toolList.filter(t => ['slither', 'mythril', 'echidna', 'foundry'].includes(t)),
                    solana: toolList.filter(t => ['cargo-audit', 'clippy', 'anchor-test'].includes(t))
                };
            }

            const config = {
                chain: options.chain,
                projectPath: path.resolve(options.project),
                outputDir: path.dirname(path.resolve(options.output)),
                tools,
                verbosity: 'normal'
            };

            const orchestrator = new AuditOrchestrator(config);

            // Detect chain and run audits
            if (config.chain === 'auto') {
                config.chain = await orchestrator.detectChainType();
            }
            await orchestrator.runChainAudits();

            // Output JSON for Claude Code
            const jsonPath = await orchestrator.outputJSON(path.resolve(options.output));

            console.log(chalk.green('✅ Tools completed'));
            console.log(chalk.cyan(`📁 Findings: ${jsonPath}`));
            console.log(chalk.gray('\nClaude Code can now read this JSON to analyze findings.'));

        } catch (error) {
            console.error(chalk.red('❌ Tool execution failed:'), error.message);
            process.exit(1);
        }
    });

program
    .command('adversarial')
    .description('Run adversarial security testing (MEV, flash loans, oracle manipulation)')
    .option('-p, --project <path>', 'Project path', process.cwd())
    .option('-m, --mode <mode>', 'Audit mode: quick, standard, deep', 'standard')
    .option('-o, --output <dir>', 'Output directory', './audit-results')
    .option('-s, --strategies <strategies>', 'Comma-separated strategies', 'mev,flash_loan,oracle_manipulation,invariants')
    .option('--fork-url <url>', 'RPC URL for mainnet fork')
    .option('--fork-block <block>', 'Block number to fork from')
    .action(async (options) => {
        const { spawn } = require('child_process');

        console.log(chalk.cyan('Running adversarial security testing...'));
        console.log(chalk.gray(`  Mode: ${options.mode}`));
        console.log(chalk.gray(`  Strategies: ${options.strategies}`));

        const args = [
            '-m', 'src.adversarial.unified_orchestrator',
            '--project', path.resolve(options.project),
            '--mode', options.mode,
            '--output', path.resolve(options.output),
            '--strategies', options.strategies
        ];

        if (options.forkUrl) {
            args.push('--fork-url', options.forkUrl);
        }
        if (options.forkBlock) {
            args.push('--fork-block', options.forkBlock);
        }

        const pythonProcess = spawn('python', args, {
            cwd: path.resolve(__dirname, '..'),
            stdio: 'inherit'
        });

        pythonProcess.on('close', (code) => {
            if (code === 0) {
                console.log(chalk.green('\n✅ Adversarial testing complete'));
                console.log(chalk.cyan(`📁 Results: ${options.output}/adversarial-findings.json`));
                console.log(chalk.gray('\nClaude Code can now read and analyze these findings.'));
            } else {
                console.error(chalk.red(`\n❌ Adversarial testing failed with code ${code}`));
            }
            process.exit(code);
        });

        pythonProcess.on('error', (err) => {
            console.error(chalk.red('Failed to start adversarial testing:'), err.message);
            console.log(chalk.yellow('\nTip: Make sure Python is installed and in your PATH'));
            process.exit(1);
        });
    });

program
    .command('invariants')
    .description('Run Foundry invariant tests')
    .option('-p, --project <path>', 'Project path', process.cwd())
    .option('-r, --runs <number>', 'Number of fuzz runs', '256')
    .option('-d, --depth <number>', 'Call depth', '15')
    .option('--match <pattern>', 'Test pattern to match', 'Invariant')
    .action(async (options) => {
        const { spawn } = require('child_process');

        console.log(chalk.cyan('Running Foundry invariant tests...'));
        console.log(chalk.gray(`  Fuzz runs: ${options.runs}`));
        console.log(chalk.gray(`  Call depth: ${options.depth}`));

        const args = [
            'test',
            '--match-contract', options.match,
            '--fuzz-runs', options.runs,
            '--fuzz-seed', Date.now().toString(),
            '-vvv'
        ];

        const forgeProcess = spawn('forge', args, {
            cwd: path.resolve(options.project),
            stdio: 'inherit'
        });

        forgeProcess.on('close', (code) => {
            if (code === 0) {
                console.log(chalk.green('\n✅ All invariants held'));
            } else {
                console.log(chalk.red('\n❌ Invariant violations detected!'));
            }
            process.exit(code);
        });

        forgeProcess.on('error', (err) => {
            console.error(chalk.red('Failed to run Foundry:'), err.message);
            console.log(chalk.yellow('\nTip: Install Foundry with: curl -L https://foundry.paradigm.xyz | bash'));
            process.exit(1);
        });
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
