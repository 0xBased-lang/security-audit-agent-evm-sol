# Security Audit Command

You are tasked with performing a comprehensive blockchain security audit using the **Unified Security Framework** (Phase 2).

## Your Task

1. **Detect Project Type**:
   - Check for Solidity files (.sol) → EVM project
   - Check for Rust files (.rs) and Anchor.toml → Solana project
   - Check for both → Ask user which to audit
   - Automatically detected by the framework

2. **Determine Audit Mode**:
   - Parse $ARGUMENTS for mode flags (--quick, --standard, --deep)
   - Default to **standard** if not specified
   - Quick: 2-5 min (traditional tools only)
   - Standard: 30-60 min (traditional + basic adversarial)
   - Deep: 2-4 hours (full 10-layer AASS)

3. **Run Security Analysis**:
   - Execute unified security framework
   - Combines traditional tools + adversarial testing
   - Automatic multi-chain adapter selection
   - Cross-references findings from all sources

4. **Analyze Results**:
   - Review findings from:
     - Traditional static analysis (Slither, Mythril, etc.)
     - Adversarial agents (economic exploits, MEV)
     - Protocol invariant violations
   - Apply AI-powered synthesis:
     - False positive detection
     - Vulnerability deduplication
     - Priority scoring
     - Exploit chain identification

5. **Generate Report**:
   - Comprehensive report in multiple formats
   - Statistics and risk assessment
   - Prioritized vulnerability list
   - Actionable remediation recommendations

6. **Interactive Review** (if findings found):
   - Present top critical/high findings
   - Ask user which findings they want to discuss
   - Provide code fixes for selected vulnerabilities
   - Explain attack vectors and real-world impact

## Command Execution

```bash
# Use the new unified framework (Python-based)

# Standard audit (default)
python -m src $ARGUMENTS

# Quick audit (if --quick in arguments)
python -m src --quick $ARGUMENTS

# Deep audit (if --deep in arguments)
python -m src --deep $ARGUMENTS

# If no arguments provided, audit current directory
python -m src .
```

**Note**: The unified framework automatically:
- Detects chain type
- Selects optimal simulation adapter
- Runs appropriate tools
- Generates JSON/markdown/HTML reports

## Response Format

After audit completes:

1. Show summary statistics (critical/high/medium/low counts)
2. List top 5 critical/high findings with brief description
3. Provide overall risk assessment
4. Ask: "Would you like me to dive deep into any specific findings or generate code fixes?"

## Additional Analysis

If vulnerabilities found:
- Cross-reference with OWASP Top 10 (2025)
- Check for common attack patterns (reentrancy, access control, etc.)
- Identify potential attack chains
- Assess real-world exploitability

## Reference Documentation

Use the following knowledge base:
- `/docs/VULNERABILITIES.md` - Complete vulnerability reference
- `/docs/TOOL_INTEGRATION.md` - Tool details

## Example Usage

```
User: /audit contracts/
You: Running comprehensive security audit on contracts/ directory...

     [Executes audit]

     ✅ Audit completed!

     📊 Summary:
     - Total findings: 23
     - Critical: 2
     - High: 5
     - Medium: 10
     - Low: 6

     🔴 Critical Issues:
     1. Reentrancy in withdraw() function (contracts/Bank.sol:45)
     2. Unprotected initialize() allows takeover (contracts/Proxy.sol:12)

     🟠 Top High Severity Issues:
     1. Missing access control on setAdmin()
     2. tx.origin used for authentication
     3. Unchecked external call return value
     4. Integer overflow in reward calculation
     5. Flash loan vulnerable governance

     Overall Risk: CRITICAL - DO NOT DEPLOY

     Would you like me to:
     1. Provide code fixes for critical issues?
     2. Explain any attack vectors in detail?
     3. Generate a full PDF report for stakeholders?
```

## Important Notes

- Always check if required tools are installed first
- For large projects, warn about execution time
- If API key missing, provide clear setup instructions
- Save all results to audit-results/ directory
- Timestamp all reports for version tracking
