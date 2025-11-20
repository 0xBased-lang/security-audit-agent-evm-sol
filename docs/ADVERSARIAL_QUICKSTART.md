# Adversarial Agent Framework - Quick Start

> **Get started with advanced MEV and economic exploit detection in 15 minutes**

---

## 🎯 What You'll Build

By the end of this guide, you'll run an adversarial agent that:
- Simulates MEV attacks on your DeFi protocol
- Discovers oracle manipulation vulnerabilities
- Tests for flash loan exploits
- Generates a comprehensive security report

---

## Prerequisites

- Python 3.10+
- Foundry (for EVM) or Solana CLI (for Solana)
- 16GB RAM recommended
- Anthropic API key (for AI orchestration)

---

## Installation

### 1. Install Core Dependencies

```bash
# Already in project root
cd security-audit-agent-evm-sol

# Install Python dependencies
pip install -r requirements-adversarial.txt
```

### 2. Install Blockchain Tools

**EVM**:
```bash
# Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Cryo (blockchain data)
cargo install cryo_cli
```

**Solana**:
```bash
# Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Anchor
cargo install --git https://github.com/coral-xyz/anchor --tag v0.29.0 anchor-cli --locked
```

---

## Quick Start Example: Testing an AMM

### Step 1: Setup Environment

```python
# test_adversarial.py

from adversarial import AdversarialOrchestrator, AdversarialTestConfig

# Configure test
config = AdversarialTestConfig(
    chain='evm',
    project_path='./examples/vulnerable-amm',
    fork_block=18500000,  # Recent Ethereum mainnet block
    strategies=['sandwich', 'oracle_manipulation'],
    search_algorithm='evolutionary',
    max_iterations=500,
    population_size=50
)

# Create orchestrator
orchestrator = AdversarialOrchestrator(config)
```

### Step 2: Run Adversarial Test

```python
# Run the test
print("🔍 Starting adversarial testing...")
results = orchestrator.run_adversarial_test()

# Print results
print(f"\n✅ Test Complete!")
print(f"Vulnerabilities found: {len(results.vulnerabilities)}")
print(f"Max exploit profit: ${results.max_exploit_profit:,.2f}")
print(f"Invariants broken: {len(results.invariants_violated)}")

# Show vulnerabilities
for i, vuln in enumerate(results.vulnerabilities, 1):
    print(f"\n🚨 Vulnerability {i}:")
    print(f"   Type: {vuln['type']}")
    print(f"   Severity: {vuln['severity']}")
    print(f"   Profit: ${vuln['profit']:,.2f}")
    print(f"   Description: {vuln['description']}")
```

### Step 3: Review Recommendations

```python
# Get defender recommendations
print("\n💡 Recommendations:")
for i, rec in enumerate(results.recommendations, 1):
    print(f"{i}. {rec}")

# Save detailed report
orchestrator.generate_report(
    output_path='./adversarial-report.md',
    format='markdown'
)
```

---

## Example Output

```
🔍 Starting adversarial testing...
[INFO] Adversarial orchestrator initialized for evm
[INFO] Initializing agents...
[INFO] Created sandwich attacker agent
[INFO] Created oracle_manipulation attacker agent
[INFO] Starting evolutionary search...
[INFO] Generation 1/500: Best fitness = 15234.5
[INFO] Generation 50/500: Best fitness = 45821.2
[INFO] Generation 100/500: Best fitness = 128450.7
...
[INFO] Search complete. Analyzing results...

✅ Test Complete!
Vulnerabilities found: 7
Max exploit profit: $287,432.50
Invariants broken: 3

🚨 Vulnerability 1:
   Type: sandwich
   Severity: HIGH
   Profit: $287,432.50
   Description: Sandwich attack on low-liquidity pool exploiting
                price impact of large swaps

🚨 Vulnerability 2:
   Type: oracle_manipulation
   Severity: CRITICAL
   Profit: $145,234.00
   Description: Flash loan oracle manipulation allowing under-
                collateralized borrowing

💡 Recommendations:
1. Implement TWAP oracle instead of spot price
2. Add minimum liquidity requirements for price feeds
3. Implement flash loan protection (same-block borrow restrictions)
4. Add price deviation checks (max 5% per block)
5. Use multi-oracle architecture (Chainlink + Uniswap TWAP)
```

---

## Testing Different Attack Vectors

### Sandwich Attacks

```python
config = AdversarialTestConfig(
    chain='evm',
    project_path='./my-amm',
    strategies=['sandwich'],
    search_algorithm='evolutionary',
    max_iterations=1000
)
```

### Oracle Manipulation

```python
config = AdversarialTestConfig(
    chain='evm',
    project_path='./my-lending-protocol',
    strategies=['oracle_manipulation'],
    search_algorithm='mcts',  # Better for complex sequences
    max_iterations=500
)
```

### Flash Loan Exploits

```python
config = AdversarialTestConfig(
    chain='evm',
    project_path='./my-defi-protocol',
    strategies=['flash_loan', 'oracle_manipulation', 'liquidation'],
    search_algorithm='hybrid',  # Combine multiple algorithms
    max_iterations=2000
)
```

### Multi-Protocol Attacks

```python
config = AdversarialTestConfig(
    chain='evm',
    project_path='./my-protocol',
    strategies=['arbitrage', 'sandwich', 'flash_loan'],
    search_algorithm='drl',  # Deep RL for complex patterns
    max_iterations=5000,
    use_historical_mev=True  # Learn from real MEV data
)
```

---

## Understanding Results

### Vulnerability Severity

- **CRITICAL**: Invariant violation + high profit (>$100k)
  - Action: Fix immediately before deployment

- **HIGH**: Economic exploit with significant profit ($10k-$100k)
  - Action: Fix before mainnet deployment

- **MEDIUM**: Exploitable but limited profit ($1k-$10k)
  - Action: Recommended to fix

- **LOW**: Theoretical exploit with minimal profit (<$1k)
  - Action: Document and monitor

### Invariant Violations

When invariants are broken, it means fundamental protocol assumptions failed:

```python
# Example invariants that might be violated:
- "Constant product: x * y >= k"
- "Total collateral >= Total borrows * collateral_factor"
- "Oracle price deviation < 10%"
- "No user profit without providing value"
```

### Attack Sequences

Each vulnerability includes the exact transaction sequence:

```python
vulnerability['exploit_sequence'] = [
    {
        'action': 'flash_loan',
        'token': 'USDC',
        'amount': 10000000,
    },
    {
        'action': 'swap',
        'from': 'USDC',
        'to': 'TARGET',
        'amount': 10000000,
        'pool': '0x...',
    },
    {
        'action': 'borrow',
        'asset': 'ETH',
        'amount': 500,
        'protocol': 'AaveV3',
    },
    # ... more steps
]
```

---

## Advanced Usage

### Custom Strategy Templates

Create your own attack strategies:

```python
from adversarial.strategies import StrategyTemplate

class MyCustomAttack(StrategyTemplate):
    """Custom attack strategy"""

    def __init__(self):
        super().__init__(
            name='my_attack',
            category='custom',
            parameters={
                'target_pool': None,
                'attack_amount': 100000,
                'profit_threshold': 1000,
            }
        )

    def generate_transactions(self, env_state):
        """Generate transaction sequence"""
        return [
            # Your attack logic here
        ]

    def check_preconditions(self, env_state):
        """Check if attack is possible"""
        return env_state.has_sufficient_liquidity()

    def calculate_profit(self, initial, final):
        """Calculate profit"""
        return final.balance - initial.balance

# Use your custom strategy
config = AdversarialTestConfig(
    chain='evm',
    project_path='./my-protocol',
    strategies=[MyCustomAttack()],
    max_iterations=1000
)
```

### Custom Invariants

Define protocol-specific invariants:

```python
from adversarial.invariants import Invariant

# Define custom invariant
my_invariant = Invariant(
    name="My Protocol Invariant",
    check_function=lambda state: (
        state.protocol.total_value_locked >=
        state.protocol.minimum_tvl
    ),
    severity='CRITICAL'
)

# Add to environment
orchestrator.environment.add_invariant(my_invariant)
```

### Integration with CI/CD

```yaml
# .github/workflows/adversarial-test.yml
name: Adversarial Security Test

on: [push, pull_request]

jobs:
  adversarial-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Foundry
        uses: foundry-rs/foundry-toolchain@v1

      - name: Install dependencies
        run: pip install -r requirements-adversarial.txt

      - name: Run adversarial tests
        run: python scripts/run_adversarial_tests.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: adversarial-report
          path: adversarial-report.md
```

---

## Troubleshooting

### "Simulation environment not found"
```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Verify
forge --version
```

### "Out of memory"
```python
# Reduce population size or iterations
config = AdversarialTestConfig(
    population_size=20,  # Instead of 100
    max_iterations=200,  # Instead of 1000
    parallel_agents=2    # Instead of 4
)
```

### "No vulnerabilities found"
```python
# Increase search depth
config = AdversarialTestConfig(
    max_iterations=5000,  # More exploration
    search_algorithm='hybrid',  # Multi-strategy
    use_historical_mev=True  # Learn from real attacks
)
```

---

## Next Steps

1. **Read Full Documentation**: [ADVERSARIAL_AGENTS.md](./ADVERSARIAL_AGENTS.md)
2. **Explore Examples**: `examples/adversarial/`
3. **Custom Strategies**: Create protocol-specific attacks
4. **Integrate with Main Framework**: Combine with static analysis
5. **Join Community**: Share findings and improvements

---

## Performance Tips

### For Faster Results
- Use `search_algorithm='evolutionary'` (fastest)
- Reduce `population_size` and `max_iterations`
- Disable `use_historical_mev` for quick tests
- Focus on specific strategy types

### For Maximum Coverage
- Use `search_algorithm='hybrid'`
- Increase `max_iterations` to 5000+
- Enable `use_historical_mev=True`
- Test all strategy types
- Run multiple rounds with different seeds

---

## Cost Estimates

| Configuration | Time | Compute Cost | API Cost |
|--------------|------|--------------|----------|
| Quick test (500 iterations) | 5-10 min | Negligible | $0.50 |
| Standard test (2000 iterations) | 30-60 min | Minimal | $2-5 |
| Comprehensive (5000 iterations) | 2-4 hours | Low | $10-20 |
| Full hybrid (10000 iterations) | 6-12 hours | Medium | $50-100 |

---

**Ready to find vulnerabilities that traditional tools miss? Start testing now!**

```bash
python test_adversarial.py
```
