# Adversarial Testing Command

Run adversarial agent testing to detect economic exploits, MEV vulnerabilities, and protocol violations.

## Usage

```
/adversarial [options] [project_path]
```

## Description

The adversarial testing system uses intelligent agents to actively search for exploits that traditional static analysis tools miss:

- **Economic Exploits**: Flash loans, oracle manipulation, pool imbalance
- **MEV Vulnerabilities**: Sandwich attacks, liquidation sniping, arbitrage exploitation
- **Protocol Violations**: Invariant breaking, state manipulation
- **Cross-Protocol Attacks**: Compound risks across multiple contracts

## Your Task

1. **Parse Arguments**:
   - Extract project path from $ARGUMENTS (default: current directory)
   - Parse optional flags: --strategies, --iterations, --chain

2. **Run Adversarial Testing**:
   ```bash
   # Run with specified options
   python -m src --no-traditional --iterations $ITERATIONS --strategies $STRATEGIES $PROJECT_PATH
   ```

3. **Analyze Results**:
   - Focus on adversarial findings (economic exploits)
   - Each finding includes:
     - Exploit transaction sequence
     - Profit extracted (in ETH/SOL)
     - Invariant violated
     - Feasibility score (0-100)

4. **Present Findings**:
   - Show exploits sorted by profitability
   - Explain attack mechanics
   - Demonstrate transaction sequences
   - Assess real-world feasibility

5. **Interactive Session**:
   - Ask user which exploits to analyze in detail
   - Show step-by-step transaction breakdown
   - Suggest defense mechanisms
   - Recommend protocol changes

## Command Options

Parse from $ARGUMENTS:

- `--strategies <list>`: Comma-separated strategies to test
  - `sandwich`: MEV sandwich attacks
  - `oracle_manipulation`: Price oracle exploits
  - `flash_loan`: Flash loan attacks
  - `all`: All available strategies (default)

- `--iterations <n>`: Number of search iterations
  - Default: 1000 (standard)
  - Quick: 100
  - Deep: 10000

- `--chain <chain>`: Blockchain network
  - ethereum, polygon, arbitrum, optimism, base, bsc, avalanche, solana
  - Auto-detected from project if not specified

## Example Usage

### Basic Adversarial Test
```
User: /adversarial
You: Running adversarial testing on current project...
     [Executes 1000 iterations with all strategies]
```

### Specific Strategies
```
User: /adversarial --strategies sandwich,oracle_manipulation
You: Testing sandwich and oracle manipulation attacks...
```

### Deep Search
```
User: /adversarial --iterations 5000
You: Running deep adversarial search (5000 iterations)...
```

## Output Interpretation

### Typical Output Format

```
🎯 Adversarial Testing Results

📊 Search Statistics:
- Iterations: 1000
- Strategies tested: 3
- Exploits found: 5
- Total profit extracted: 45.3 ETH

🔴 Critical Exploits:

1. Oracle Manipulation (Feasibility: 92/100)
   - Profit: 23.1 ETH
   - Attack: Manipulate Chainlink price feed via flash loan
   - Transactions:
     1. Flash borrow 50M USDC from Aave
     2. Swap USDC → DAI to manipulate pool price
     3. Trigger protocol liquidation using manipulated price
     4. Buy liquidated collateral at discount
     5. Repay flash loan
   - Invariant violated: "Oracle price should resist flash loan attacks"
   - Fix: Use TWAP with minimum update interval

2. Sandwich Attack (Feasibility: 88/100)
   - Profit: 12.8 ETH
   - Attack: Frontrun large swap transaction
   - ... [details]
```

### Key Metrics

**Feasibility Score (0-100)**:
- 0-30: Theoretical only (hard to execute)
- 31-60: Possible but requires specific conditions
- 61-85: Realistic under normal conditions
- 86-100: Easily exploitable in production

**Profit Extracted**:
- Shows maximum profit from successful exploit
- Helps prioritize fixes by financial impact

**Transaction Sequence**:
- Step-by-step attack execution
- Can be replayed for verification

## What Makes This Different

**Traditional Tools** (Slither, Mythril):
- Static code analysis
- Pattern matching
- Find code-level bugs

**Adversarial Agents**:
- Dynamic simulation
- Economic reasoning
- Find business logic exploits
- Discover MEV opportunities
- Test protocol assumptions

**Example**: Traditional tools won't find:
- "This protocol can be profitably exploited via oracle manipulation"
- "MEV bots can sandwich user transactions for 3% profit"
- "Flash loans make this liquidation mechanism vulnerable"

## Technical Details

### Agent-Based Search

The system uses:
1. **Swarm of specialized agents**: Each with different attack strategies
2. **Evolutionary algorithms**: Optimize attack parameters
3. **MCTS**: Explore multi-step transaction sequences
4. **Multi-chain simulation**: Test on forked mainnet state

### Simulation Adapters

Automatically selects best adapter:
- Anvil (Foundry): Fastest for standard chains
- Hardhat: Custom EVM configurations
- DirectRPC: Universal fallback for any chain

### Protocol Invariants

Tests 32+ invariants including:
- AMM: Constant product formula holds
- Lending: Always overcollateralized
- Oracle: Price manipulation resistant
- Governance: Quorum requirements enforced

## Reference Documentation

- `docs/ADVERSARIAL_AGENTS.md`: Complete adversarial system design
- `docs/MLSS_ARCHITECTURE_PART1.md`: Layer 1-4 detailed architecture
- `docs/UNIFIED_FRAMEWORK_GUIDE.md`: Integration guide

## Important Notes

1. **Requires simulation**: Must have Foundry/Anvil or RPC endpoint
2. **Time intensive**: Deep searches can take hours
3. **Mainnet state**: Forks from latest block (or specified block)
4. **No real transactions**: All testing is simulated

## Troubleshooting

**"Adapter not available"**:
- Install Foundry: `curl -L https://foundry.paradigm.xyz | bash && foundryup`
- Or set RPC URL: `export ETHEREUM_RPC_URL=https://...`

**"Simulation failed"**:
- Check chain is supported
- Verify RPC endpoint is accessible
- Try different adapter: `--adapter hardhat`

## Next Steps After Finding Exploits

1. **Validate**: Manually review transaction sequences
2. **Fix Protocol**: Implement recommended changes
3. **Re-test**: Run adversarial testing again to confirm fix
4. **Document**: Add to audit report for stakeholders

---

**Pro Tip**: Run adversarial testing AFTER fixing traditional tool findings. This catches the sophisticated exploits that survive basic security measures.
