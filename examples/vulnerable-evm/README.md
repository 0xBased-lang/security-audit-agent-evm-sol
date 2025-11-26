# Vulnerable EVM Contract Examples

**WARNING: These contracts are DELIBERATELY VULNERABLE. DO NOT deploy to mainnet or use in production!**

## Purpose

These example contracts demonstrate common vulnerabilities for testing the Security Audit Framework. Each contract includes:
- The vulnerable implementation
- Attack contract demonstrating the exploit
- Fixed/secure implementation
- Detailed comments explaining the vulnerability

## Contracts

### 1. Reentrancy.sol

**Vulnerability:** Classic reentrancy attack
**Impact:** Complete fund drainage
**CWE:** CWE-841 (Improper Enforcement of Behavioral Workflow)

**Attack Flow:**
1. Attacker deposits ETH
2. Attacker calls `withdraw()`
3. In fallback function, attacker calls `withdraw()` again before balance is updated
4. Balance check passes because state not yet updated
5. Attacker drains all funds

**Real-world Examples:**
- The DAO hack ($60M)
- Lendf.Me ($25M)

**Fix:** Checks-Effects-Interactions pattern - update state before external calls

### 2. FlashLoanOracle.sol

**Vulnerability:** Price oracle manipulation via flash loans
**Impact:** Draining lending protocol liquidity
**Attack Vector:** Flash loan → manipulate DEX price → exploit price oracle → profit

**Attack Flow:**
1. Flash loan large amount of tokenA
2. Swap tokenA for tokenB on DEX (manipulates price)
3. Borrow maximum from lending protocol using inflated collateral value
4. Repay flash loan
5. Keep the over-borrowed funds

**Real-world Examples:**
- Harvest Finance ($34M)
- Cream Finance ($130M)
- Inverse Finance ($15M)

**Fix:** Use Time-Weighted Average Price (TWAP) oracles like Chainlink or Uniswap V3

### 3. AccessControl.sol

**Vulnerability:** Missing or incorrect access control
**Impact:** Unauthorized access to admin functions
**CWE:** CWE-284 (Improper Access Control)

**Vulnerabilities Demonstrated:**
1. Missing `onlyOwner` modifiers
2. Use of `tx.origin` instead of `msg.sender`
3. Public functions that should be internal/private
4. Uninitialized ownership
5. Unsafe delegatecall

**Attack Vectors:**
- Anyone can pause/unpause contract
- Anyone can transfer ownership
- Anyone can manipulate balances
- Phishing attacks via `tx.origin`
- Storage manipulation via delegatecall

**Fix:** Proper access control modifiers, use `msg.sender`, internal visibility

### 4. MEVSandwich.sol

**Vulnerability:** MEV sandwich attacks on AMM swaps
**Impact:** Loss of value to front-running bots (>$1B annually)
**Attack:** Front-run → victim's trade → back-run

**Attack Flow:**
1. MEV bot monitors mempool for large trades
2. Front-run: Bot submits higher gas transaction before victim
3. Victim's trade executes at worse price due to slippage
4. Back-run: Bot submits transaction to capture profit

**Real-world Examples:**
- Common on Uniswap V2 and similar AMMs
- Affects all traders without slippage protection
- Sophisticated bots extract $1B+ annually

**Fix:** Slippage protection with `minAmountOut` parameter

## Testing with the Audit Framework

### Run Full Audit

```bash
# Audit all vulnerable contracts
npm run audit examples/vulnerable-evm/

# Audit specific contract
npm run audit examples/vulnerable-evm/Reentrancy.sol
```

### Expected Findings

**Reentrancy.sol:**
- ✓ Reentrancy vulnerability detected
- ✓ External call before state update identified
- ✓ Missing reentrancy guard
- ✓ CEI pattern violation

**FlashLoanOracle.sol:**
- ✓ Flash loan attack vector identified
- ✓ Oracle manipulation vulnerability detected
- ✓ Spot price usage without TWAP
- ✓ Missing price staleness checks

**AccessControl.sol:**
- ✓ Missing access control modifiers
- ✓ tx.origin usage detected
- ✓ Public functions that should be private
- ✓ Unsafe delegatecall
- ✓ Uninitialized ownership

**MEVSandwich.sol:**
- ✓ Missing slippage protection
- ✓ MEV sandwich attack susceptibility
- ✓ Lack of minimum output amount check
- ✓ Front-running vulnerability

## Educational Value

These contracts serve multiple purposes:

1. **Framework Testing:** Validate the audit framework detects known vulnerabilities
2. **Agent Training:** Help agents learn to identify vulnerability patterns
3. **Education:** Teach developers about common smart contract vulnerabilities
4. **Benchmarking:** Measure detection rates and false positive rates

## Vulnerability Statistics

| Vulnerability Type | Severity | Detection Difficulty | Real-world Frequency |
|-------------------|----------|---------------------|---------------------|
| Reentrancy | CRITICAL | Easy | Common (Top 5) |
| Flash Loan Oracle | CRITICAL | Medium | Very Common |
| Access Control | HIGH | Easy | Very Common (Top 3) |
| MEV Sandwich | MEDIUM | Hard | Extremely Common |

## Compile Contracts

```bash
# Using Foundry
forge build

# Using Hardhat
npx hardhat compile
```

## Run Tests

```bash
# Foundry tests
forge test

# Hardhat tests
npx hardhat test
```

## Security Tools to Run

1. **Static Analysis:**
   ```bash
   slither examples/vulnerable-evm/
   mythril analyze examples/vulnerable-evm/Reentrancy.sol
   ```

2. **Formal Verification:**
   ```bash
   echidna examples/vulnerable-evm/Reentrancy.sol
   ```

3. **Fuzzing:**
   ```bash
   foundry test --fuzz-runs 10000
   ```

## References

- [Smart Contract Weakness Classification (SWC)](https://swcregistry.io/)
- [DASP Top 10](https://dasp.co/)
- [DeFi Hack Analysis](https://defihacks.com/)
- [Rekt News](https://rekt.news/) - Real attack breakdowns

## License

MIT - For educational purposes only

## Disclaimer

⚠️ **DO NOT USE IN PRODUCTION**

These contracts are intentionally vulnerable and should only be used for:
- Testing security tools
- Educational purposes
- Security research
- Framework development

Using these contracts in production will result in loss of funds.
