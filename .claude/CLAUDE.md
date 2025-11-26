# Claude Code Configuration for Security Audit Framework

## Project Overview

This is an AI-powered blockchain security auditing framework for EVM (Ethereum, BSC, Polygon, etc.) and Solana smart contracts. The framework integrates 15+ free security tools and uses Claude AI for intelligent vulnerability analysis.

## Common Commands

### Setup
```bash
# Install dependencies
npm install

# Install security tools
npm run install:tools

# Check which tools are installed
npm run tools
```

### Running Audits
```bash
# Auto-detect chain and run audit
npm run audit -- --project ./path/to/project

# EVM-specific audit
npm run audit:evm -- --project ./path/to/evm-project

# Solana-specific audit
npm run audit:solana -- --project ./path/to/solana-project

# With specific tools
npm run audit -- --tools slither,mythril,foundry

# Generate HTML report
npm run audit -- --format html

# Verbose mode
npm run audit -- --verbose
```

### Report Generation
```bash
# Generate report from existing results
npm run report -- --input ./audit-results/results.json --format markdown
```

## Project Structure

```
├── src/
│   ├── core/              # Core orchestration (JavaScript)
│   │   ├── AuditOrchestrator.js  # Main coordinator
│   │   └── Logger.js             # Logging utility
│   ├── evm/               # EVM-specific auditors
│   │   └── EVMAuditor.js         # Slither, Mythril, Foundry, etc.
│   ├── solana/            # Solana-specific auditors
│   │   └── SolanaAuditor.js      # Cargo audit, Clippy, Anchor
│   ├── adversarial/       # Adversarial testing (Python)
│   │   ├── unified_orchestrator.py  # Main Python orchestrator
│   │   ├── strategies/            # Attack strategies (MEV, flash loans)
│   │   ├── invariants/            # Protocol invariant tests
│   │   └── agents/                # Agent definitions
│   ├── reports/           # Report generation
│   │   └── ReportGenerator.js    # Markdown, HTML, JSON reports
│   └── cli.js             # Command-line interface
├── .claude/               # Claude Code configuration
│   ├── agents/            # Agent markdown definitions
│   ├── hooks/             # Pre/post audit hooks
│   └── commands/          # Slash commands
├── docs/                  # Documentation
├── tests/                 # Test suites
│   ├── e2e/               # End-to-end tests
│   ├── integration/       # Integration tests
│   └── benchmarks/        # Performance benchmarks
└── examples/              # Example contracts
```

## Architecture

The framework uses a multi-layer architecture:

1. **CLI Layer**: User interface for running audits
2. **Orchestration Layer**: Coordinates all tools and analysis
3. **Tool Integration Layer**: Interfaces with security tools (Slither, Mythril, Clippy, etc.)
4. **AI Analysis Layer**: Claude-powered intelligent analysis
5. **Report Generation Layer**: Creates comprehensive reports

## Security Tools Integrated

### EVM Tools
- **Slither**: Primary static analyzer (90+ detectors)
- **Mythril**: Symbolic execution engine
- **Echidna**: Property-based fuzzing
- **Foundry**: Fast fuzzing and invariant testing
- **Certora**: Formal verification (optional)
- **Tenderly**: Transaction simulation

### Solana Tools
- **Cargo Audit**: Dependency vulnerability scanning
- **Clippy**: Rust linter with 450+ rules
- **Anchor**: Framework-specific security lints
- **solana-program-test**: Integration testing
- **Kangaroo**: Fuzzing (emerging)

## AI-Powered Analysis

The framework uses Claude to:
1. Correlate findings across multiple tools
2. Identify false positives
3. Assess exploitability of vulnerabilities
4. Provide risk assessment and prioritization
5. Generate remediation recommendations
6. Detect attack chains and compounding risks

## Environment Variables

Required:
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

Optional:
```bash
TENDERLY_API_KEY=your_tenderly_key
```

## Vulnerability Coverage

Based on OWASP Smart Contract Top 10 (2025):
1. Access Control ($953M losses in 2024)
2. Price Oracle Manipulation
3. Logic Errors
4. Reentrancy
5. Input Validation
6. Unchecked External Calls
7. Flash Loan Attacks
8. Integer Overflow/Underflow
9. Weak Randomness
10. Denial of Service

Plus 40+ EVM and 20+ Solana-specific vulnerability types.

## Code Style

- Use clear, descriptive variable names
- Add JSDoc comments for functions
- Handle errors explicitly
- Log progress for long-running operations
- Follow async/await patterns

## Testing Approach

When testing the framework:
1. Use example contracts from `examples/` directory
2. Test with both vulnerable and secure contracts
3. Verify tool outputs are correctly parsed
4. Check AI analysis for accuracy
5. Validate report generation

## Important Notes

- Always run `npm run tools` first to check tool availability
- EVM audits require Node.js 18+ and Python 3.8+
- Solana audits require Rust and Cargo
- Mythril is slow; use sparingly or with timeout
- AI analysis costs ~$0.50-2 per audit depending on findings
- Results are cached in `audit-results/` directory

## Known Limitations

- Cannot replace manual security audits for high-value protocols
- Some tools (Echidna, Certora) require manual setup
- Mythril symbolic execution can be very slow
- False positive rate varies by tool
- AI analysis quality depends on finding descriptions

## For Claude Code Development

When working on this project:
1. Test changes with example contracts before running on real projects
2. Use verbose mode (`--verbose`) to debug issues
3. Check logs in `audit-results/` if something fails
4. Validate JSON output format for new tool integrations
5. Update `VULNERABILITIES.md` when adding new detection patterns

## Common Issues

**"Tool not found"**: Run `npm run tools` to check installation
**"No contracts found"**: Verify project path is correct
**"AI analysis failed"**: Check ANTHROPIC_API_KEY is set
**Timeout errors**: Increase timeout in tool config or skip slow tools
**Out of memory**: Run fewer tools in parallel or use `--no-parallel`

## Support Resources

- Documentation: `docs/` directory
- Tool integration guides: `docs/TOOL_INTEGRATION.md`
- Vulnerability reference: `docs/VULNERABILITIES.md`
- Example contracts: `examples/` directory
