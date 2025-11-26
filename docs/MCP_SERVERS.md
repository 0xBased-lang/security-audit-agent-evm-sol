# MCP Servers Documentation

> **Model Context Protocol (MCP) Integration for EVM Security Framework**

This document describes the three specialized MCP servers that enhance the security audit framework with real-time data, tool orchestration, and economic exploit simulation.

---

## Overview

The framework provides **3 specialized MCP servers**:

1. **vulnerability-feed** - Vulnerability database and exploit patterns
2. **evm-analysis** - Static analysis tool orchestration
3. **adversarial** - Economic exploit simulation

These servers are automatically activated when using the `evm-security` skill or when auditing contracts.

---

## Installation

### 1. Install MCP SDK

```bash
cd /Users/seman/Desktop/security\ audit/security-audit-agent-evm-sol
pip install -r requirements-mcp.txt
```

### 2. Verify Configuration

The `.mcp.json` file in the repository root configures all three servers:

```bash
cat .mcp.json
```

### 3. Test Server Availability

```bash
# Test vulnerability feed server
python -m src.mcp_servers.vulnerability_feed.server

# Test EVM analysis server
python -m src.mcp_servers.evm_analysis.server

# Test adversarial server
python -m src.mcp_servers.adversarial.server
```

---

## Server 1: Vulnerability Feed MCP

### Purpose

Provides real-time access to:
- CVE database for blockchain vulnerabilities
- Historical exploit patterns from 2024
- MEV attack signatures
- Flash loan attack vectors
- Oracle manipulation patterns

### Available Tools

#### `search_vulnerabilities`

Search the vulnerability database by keywords, severity, or category.

**Parameters**:
- `keywords` (required): Search terms (e.g., "reentrancy", "oracle", "MEV")
- `severity` (optional): Filter by CRITICAL | HIGH | MEDIUM | LOW
- `category` (optional): Filter by MEV | Oracle | Flash Loan | Governance | Reentrancy | Access Control

**Example**:
```javascript
// Search for oracle vulnerabilities
{
  "keywords": "oracle",
  "severity": "CRITICAL"
}
```

**Returns**:
```markdown
## Vulnerability Search Results

**Query**: oracle
**Matches**: 1

### CVE-2024-ORACLE-001: Oracle Manipulation via Flash Loan

- **Severity**: CRITICAL
- **Category**: Oracle
- **2024 Losses**: $52M
- **Description**: Single-source price oracle vulnerable to flash loan manipulation

**Affected Functions**: getPrice, getLPTokenPrice, consult

**Indicators**:
  - Uniswap V2 TWAP only
  - no multi-oracle validation
  - single pool dependency

**Mitigation**: Use Chainlink Price Feeds with TWAP fallback and multi-oracle consensus
```

---

#### `get_mev_patterns`

Fetch MEV attack patterns with detection methods.

**Parameters**:
- `pattern_type` (optional): sandwich | arbitrage | liquidation_sniping | all

**Example**:
```javascript
{
  "pattern_type": "sandwich"
}
```

**Returns**: Attack sequence, profitability assessment, detection methods, prevention strategies

---

#### `get_vulnerability_stats`

Get 2024 vulnerability statistics and loss amounts by category.

**Returns**:
```markdown
## 2024 Blockchain Vulnerability Statistics

**Total Tracked Losses**: $1,424.96M
**Total Vulnerabilities**: 6

### Losses by Category

| Category | Losses | % of Total | Count |
|----------|--------|------------|-------|
| Access Control | $953.20M | 66.9% | 1 |
| MEV | $289.76M | 20.3% | 1 |
| Oracle | $52.00M | 3.6% | 1 |
```

---

#### `check_function_vulnerability`

Check if a function name matches known vulnerable patterns.

**Parameters**:
- `function_name` (required): Function to check (e.g., "swap", "withdraw", "initialize")

**Example**:
```javascript
{
  "function_name": "withdraw"
}
```

**Returns**: Matching vulnerabilities with severity, indicators, and mitigation

---

## Server 2: EVM Analysis MCP

### Purpose

Orchestrates static analysis tools for comprehensive vulnerability detection:
- **Slither**: 90+ pattern-based detectors
- **Mythril**: Symbolic execution for deep path analysis
- **Foundry**: Fuzz testing and invariant checks
- **Echidna**: Property-based fuzzing (optional)

### Available Tools

#### `run_slither`

Run Slither static analysis on Solidity contracts.

**Parameters**:
- `contract_path` (required): Path to contract file or project directory
- `detectors` (optional): all | high | medium | low | critical
- `exclude` (optional): Comma-separated detector names to exclude

**Example**:
```javascript
{
  "contract_path": "/Users/seman/Desktop/contracts_CLEAN",
  "detectors": "high"
}
```

**Returns**: Grouped findings by severity with file locations and recommendations

---

#### `run_mythril`

Run Mythril symbolic execution for deep path analysis.

**Parameters**:
- `contract_path` (required): Path to Solidity contract file
- `max_depth` (optional): Maximum recursion depth (default: 12, deep: 22)
- `timeout` (optional): Analysis timeout in seconds (default: 300)

**Example**:
```javascript
{
  "contract_path": "contracts/RewardDistributor.sol",
  "max_depth": 22,
  "timeout": 600
}
```

**Returns**: Security issues with severity ratings and locations

---

#### `run_foundry_fuzz`

Run Foundry fuzz testing on smart contracts.

**Parameters**:
- `project_path` (required): Path to Foundry project directory
- `fuzz_runs` (optional): Number of iterations (default: 1000, deep: 10000)
- `match_test` (optional): Regex pattern to match specific tests

**Example**:
```javascript
{
  "project_path": "/Users/seman/Desktop/contracts_CLEAN",
  "fuzz_runs": 10000
}
```

**Returns**: Test results with pass/fail status and coverage

---

#### `get_slither_detectors`

List all 90+ Slither detectors with descriptions.

**Returns**: Complete list of available detectors

---

#### `check_tool_availability`

Check which security tools are installed.

**Returns**:
```markdown
## Security Tool Availability

- **slither**: ✅ Installed
- **myth**: ❌ Not installed
- **forge**: ✅ Installed
- **echidna**: ❌ Not installed

### Installation Instructions

**Mythril**: `pip install mythril`
**Echidna**: `https://github.com/crytic/echidna`
```

---

## Server 3: Adversarial MCP

### Purpose

Simulates economic exploits and calculates attack profitability:
- Sandwich attacks (MEV)
- Flash loan attacks
- Oracle manipulation
- Governance attacks
- Liquidation sniping

### Available Tools

#### `simulate_sandwich_attack`

Simulate sandwich attack profitability.

**Parameters**:
- `victim_swap_amount` (required): Size of victim's swap in USD
- `pool_liquidity` (required): Total pool liquidity in USD
- `slippage_protection` (optional): Max slippage tolerance % (0-100)
- `gas_price_gwei` (optional): Current gas price in Gwei

**Example**:
```javascript
{
  "victim_swap_amount": 50000,
  "pool_liquidity": 2000000,
  "slippage_protection": 0.5,
  "gas_price_gwei": 50
}
```

**Returns**:
```markdown
## 🥪 Sandwich Attack Simulation

### Attack Analysis

- **Frontrun Amount**: $150,000.00 (3x victim size)
- **Price Impact on Victim**: 3.75%
- **Victim Loss**: $1,875.00
- **Gas Cost**: $100.00
- **Expected Profit**: $1,400.00

### ✅ Attack Blocked

Victim's slippage protection (0.5%) would **prevent** this attack.
```

---

#### `simulate_flash_loan_attack`

Simulate flash loan attack feasibility.

**Parameters**:
- `borrow_amount` (required): Amount to borrow in USD
- `attack_profit_estimate` (required): Estimated profit before fees in USD
- `flash_loan_provider` (optional): aave | balancer | dydx

**Example**:
```javascript
{
  "borrow_amount": 500000,
  "attack_profit_estimate": 50000,
  "flash_loan_provider": "aave"
}
```

**Returns**: Cost analysis, net profit, feasibility assessment

---

#### `simulate_oracle_manipulation`

Simulate oracle price manipulation attack.

**Parameters**:
- `pool_liquidity` (required): Target pool liquidity in USD
- `price_deviation_needed` (required): Required price deviation %
- `liquidatable_positions` (required): Value of positions that become liquidatable in USD
- `liquidation_bonus_pct` (optional): Liquidation bonus % (default: 10)

**Example**:
```javascript
{
  "pool_liquidity": 1000000,
  "price_deviation_needed": 10,
  "liquidatable_positions": 5000000,
  "liquidation_bonus_pct": 10
}
```

**Returns**: Manipulation cost, profit analysis, TWAP bypass assessment, mitigation

---

#### `calculate_mev_profitability`

Calculate MEV extraction profitability.

**Parameters**:
- `attack_type` (required): sandwich | arbitrage | liquidation
- `capital_required` (required): Capital needed in USD
- `expected_profit` (required): Expected profit before costs in USD
- `gas_cost_usd` (required): Estimated gas cost in USD

**Returns**: Net profit, ROI, competition-adjusted expected value

---

#### `get_attack_template`

Get detailed attack template with sequence and requirements.

**Parameters**:
- `attack_type` (required): sandwich | flash_loan | oracle_manipulation | governance_attack | liquidation_sniping

**Returns**: Attack sequence, requirements, profitability factors

---

#### `analyze_protocol_vulnerabilities`

Analyze protocol for common attack vectors.

**Parameters**:
- `protocol_type` (required): dex | lending | governance | staking
- `has_oracle` (optional): Boolean - does protocol use oracles?
- `oracle_type` (optional): chainlink | uniswap_v2_twap | uniswap_v3_twap | custom | none

**Example**:
```javascript
{
  "protocol_type": "lending",
  "has_oracle": true,
  "oracle_type": "uniswap_v2_twap"
}
```

**Returns**: Risk assessment for all relevant attack types with mitigation recommendations

---

## Usage in Claude Code

### Automatic Activation

MCP servers are **automatically activated** when:
- Working with `.sol` files
- Using the `evm-security` skill
- Running security audits

No manual configuration needed!

### Manual Invocation

You can explicitly request MCP server tools:

```
"Check the vulnerability database for reentrancy attacks"
→ Uses vulnerability-feed MCP: search_vulnerabilities

"Run Slither on my contracts"
→ Uses evm-analysis MCP: run_slither

"Simulate a sandwich attack on this DEX"
→ Uses adversarial MCP: simulate_sandwich_attack
```

---

## Integration with Agents

MCP servers work seamlessly with the framework's agents:

### Static Analysis Agent
**Uses**: `evm-analysis` MCP
- Runs Slither, Mythril in parallel
- Aggregates results
- Filters false positives

### Adversarial Agent
**Uses**: `adversarial` MCP + `vulnerability-feed` MCP
- Simulates MEV attacks
- Calculates profitability
- References historical exploits

### Security Orchestrator
**Uses**: All 3 MCP servers
- Coordinates comprehensive audits
- Synthesizes findings from all sources
- Generates final reports

---

## Troubleshooting

### MCP Server Not Starting

**Issue**: Server fails to start
**Solution**:
```bash
# Check Python version (3.8+ required)
python --version

# Install MCP SDK
pip install mcp>=0.9.0

# Test server directly
python -m src.mcp_servers.vulnerability_feed.server
```

### Tool Not Available in EVM Analysis

**Issue**: "Slither is not installed"
**Solution**:
```bash
# Install missing tools
pip install slither-analyzer  # For Slither
pip install mythril          # For Mythril
curl -L https://foundry.paradigm.xyz | bash  # For Foundry
```

### Slow MCP Response

**Issue**: MCP calls taking too long
**Solutions**:
- Reduce Mythril max_depth (use 12 instead of 22)
- Reduce Foundry fuzz_runs (use 1000 instead of 10000)
- Exclude low-priority Slither detectors

---

## Performance Benchmarks

| MCP Server | Typical Response Time | Token Usage |
|------------|----------------------|-------------|
| vulnerability-feed | <1 second | 500-2K tokens |
| evm-analysis (Slither) | 10-60 seconds | 2-5K tokens |
| evm-analysis (Mythril) | 1-5 minutes | 3-8K tokens |
| adversarial (simulation) | <1 second | 1-3K tokens |

---

## Advanced Configuration

### Custom Vulnerability Database

Add custom vulnerabilities to `vulnerability_feed/server.py`:

```python
VULNERABILITY_DB["CVE-CUSTOM-001"] = {
    "title": "Your Custom Vulnerability",
    "severity": "HIGH",
    "category": "Custom",
    # ... rest of fields
}
```

### Custom Attack Templates

Add custom attack scenarios to `adversarial/server.py`:

```python
ATTACK_TEMPLATES["custom_attack"] = {
    "name": "Custom Attack Name",
    "description": "Attack description",
    "attack_sequence": [...],
    "requirements": {...},
    "profitability_factors": [...]
}
```

---

## Future Enhancements (Weeks 3-6)

- **Week 3**: Integrate with unified orchestrator for JS↔Python bridge
- **Week 4**: Add real-time blockchain data feeds (Etherscan, Dune Analytics)
- **Week 5**: Implement caching layer for faster responses
- **Week 6**: Add support for Solana vulnerabilities

---

## Support

**Framework Repository**: `/Users/seman/Desktop/security audit/security-audit-agent-evm-sol`

**MCP Server Issues**: Check logs in server output or run with `--verbose` flag

**Version**: 1.0.0 (2025-01)
