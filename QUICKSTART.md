# Quick Start Guide

Get up and running with the AI-powered blockchain security auditing framework in minutes!

## Prerequisites

- **Node.js 18+**
- **Python 3.8+**
- **Rust/Cargo** (for Solana audits)
- **Anthropic API Key** (get one at https://console.anthropic.com/)

## Installation

### 1. Clone and Setup

```bash
cd security-audit-agent-evm-sol
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Install Security Tools

```bash
# Automated installation (recommended)
npm run install:tools

# Or manually install specific tools
pip install slither-analyzer mythril
curl -L https://foundry.paradigm.xyz | bash && foundryup
cargo install cargo-audit
```

### 4. Verify Installation

```bash
npm run tools
```

You should see checkmarks for installed tools.

## First Audit

### EVM Project

```bash
# Basic audit
npm run audit:evm -- --project ./path/to/your/evm-project

# With specific tools
npm run audit:evm -- --project ./contracts --tools slither,mythril

# Generate HTML report
npm run audit:evm -- --project ./contracts --format html --verbose
```

### Solana Project

```bash
# Basic audit
npm run audit:solana -- --project ./path/to/your/solana-program

# With specific tools
npm run audit:solana -- --project ./programs --tools cargo-audit,clippy
```

### Auto-Detect Chain

```bash
# Framework auto-detects chain type
npm run audit -- --project ./your-project
```

## Using with Claude Code

If using Claude Code:

```bash
# Run audit via Claude
/audit ./contracts

# The framework will:
# 1. Detect chain type
# 2. Run appropriate security tools
# 3. Perform AI analysis
# 4. Generate comprehensive report
```

## Understanding Results

After the audit completes, you'll see:

```
✅ Audit completed!

📊 Summary:
- Total findings: 23
- Critical: 2
- High: 5
- Medium: 10
- Low: 6

🔴 Critical Issues:
1. Reentrancy in withdraw() function
2. Unprotected initialize() allows takeover

📄 Report: ./audit-results/audit-report-2025-01-20.md
```

## Next Steps

1. **Review the Report**: Open the generated markdown/HTML report
2. **Fix Critical Issues**: Start with critical and high severity findings
3. **Run Again**: Re-audit after fixes to verify
4. **Learn More**: Read the full documentation in `docs/`

## Common Commands

```bash
# Check tool installation status
npm run tools

# Run audit with verbose output
npm run audit -- --verbose --project ./contracts

# Generate only JSON report
npm run audit -- --format json --project ./contracts

# Run specific tools only
npm run audit -- --tools slither,foundry --project ./contracts

# Include formal verification (slow)
npm run audit -- --include-formal --project ./contracts
```

## Troubleshooting

### "Tool not found"
- Run `npm run tools` to see which tools are missing
- Install missing tools: `npm run install:tools`

### "AI analysis failed"
- Verify `ANTHROPIC_API_KEY` is set in `.env`
- Check your API key has sufficient credits

### "No contracts found"
- Verify project path is correct
- Check contracts are in standard locations (`contracts/`, `src/`, `programs/`)

### Slow performance
- Mythril is slow; skip it for quick audits: `--tools slither,foundry`
- Use `--no-parallel` if parallel execution causes issues

## Cost Estimates

- **Security Tools**: 100% FREE
- **AI Analysis**: ~$0.50-$2.00 per audit (depends on findings)
- **Traditional Audit**: $50,000-$500,000+

**Savings: 99.9%+**

## Getting Help

- **Documentation**: See `docs/` directory
- **Examples**: Check `examples/` for sample contracts
- **Issues**: Report bugs on GitHub
- **Questions**: Open a discussion on GitHub

## What to Audit

### Before Mainnet Launch
- ✅ All smart contracts
- ✅ Upgrade mechanisms
- ✅ Access control systems
- ✅ Token economics
- ✅ Oracle integrations

### Before Major Updates
- ✅ Modified contracts
- ✅ New features
- ✅ Integration points

### Regularly
- ✅ Run in CI/CD pipeline
- ✅ After dependency updates
- ✅ When adding new features

## Security Notice

This framework is a powerful tool but should **NOT** be considered a complete replacement for professional security audits, especially for:
- High-value protocols (>$10M TVL)
- Novel mechanisms
- Cross-chain bridges
- Complex DeFi protocols

**Always consider professional audits for production systems handling significant value.**

---

**Ready to secure your blockchain project? Run your first audit now!**

```bash
npm run audit -- --project ./your-project
```
