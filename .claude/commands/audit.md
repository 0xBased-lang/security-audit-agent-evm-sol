# Security Audit Command

You are tasked with performing a comprehensive blockchain security audit using the integrated framework.

## Your Task

1. **Detect Project Type**:
   - Check for Solidity files (.sol) → EVM project
   - Check for Rust files (.rs) and Anchor.toml → Solana project
   - Check for both → Ask user which to audit

2. **Run Security Analysis**:
   - Execute appropriate security tools based on chain type
   - Use the AuditOrchestrator from `src/core/AuditOrchestrator.js`
   - Pass the project path from $ARGUMENTS or current directory

3. **Analyze Results**:
   - Review all findings from automated tools
   - Apply AI-powered analysis for:
     - False positive detection
     - Severity validation
     - Exploit chain identification
     - Risk prioritization

4. **Generate Report**:
   - Create comprehensive markdown report
   - Include executive summary
   - List all findings by severity
   - Provide remediation recommendations

5. **Interactive Review** (if findings found):
   - Ask user which findings they want to discuss in detail
   - Provide code fixes for selected vulnerabilities
   - Explain attack vectors and impact

## Command Execution

```bash
# Run audit
node src/cli.js audit --project $ARGUMENTS --format markdown

# If no argument, use current directory
node src/cli.js audit --format markdown
```

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
