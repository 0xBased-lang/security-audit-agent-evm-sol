# Example Contracts and Audits

This directory contains example smart contracts with known vulnerabilities for testing the audit framework.

## Structure

```
examples/
├── vulnerable-evm/       # EVM contracts with vulnerabilities
├── secure-evm/          # Secure EVM contract examples
├── vulnerable-solana/   # Solana programs with vulnerabilities
├── secure-solana/       # Secure Solana program examples
└── audit-reports/       # Example audit reports
```

## Testing the Framework

### EVM Examples

```bash
# Audit vulnerable EVM contract
npm run audit -- --project examples/vulnerable-evm --chain evm

# Audit secure EVM contract
npm run audit -- --project examples/secure-evm --chain evm
```

### Solana Examples

```bash
# Audit vulnerable Solana program
npm run audit -- --project examples/vulnerable-solana --chain solana

# Audit secure Solana program
npm run audit -- --project examples/secure-solana --chain solana
```

## Expected Results

### Vulnerable EVM Contract
Should detect:
- Reentrancy vulnerabilities
- Access control issues
- Integer overflow/underflow
- Unchecked external calls

### Vulnerable Solana Program
Should detect:
- Missing account validation
- PDA security issues
- Integer arithmetic without checks
- Missing discriminators

## Adding New Examples

1. Create contract in appropriate directory
2. Add README explaining the vulnerabilities
3. Include both vulnerable and fixed versions
4. Update this file with expected findings

## Learning Resources

Use these examples to:
- Learn about common vulnerabilities
- Test framework updates
- Demonstrate audit capabilities
- Train on vulnerability patterns
