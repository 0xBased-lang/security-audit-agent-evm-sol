# Security Audit Command

You are tasked with performing a comprehensive blockchain security audit using the **Multi-Agent Security Framework**.

## Your Task

Run a security audit using the multi-agent orchestration system by spawning the **security-orchestrator** agent.

## Execution Steps

1. **Parse Arguments**:
   - Extract project path from $ARGUMENTS (default: current directory)
   - Detect audit mode: --quick, --standard, --deep (default: standard)

2. **Spawn Security Orchestrator**:
   Use the Task tool to spawn the security-orchestrator agent:

```
Use Task tool with:
- subagent_type: "security-orchestrator"
- description: "Security audit of [project_path]"
- prompt: "Perform a [mode] security audit on the project at [project_path].

  Project path: [project_path]
  Audit mode: [mode]

  Instructions:
  1. Detect chain type (EVM/Solana/Multi-chain) by examining files
  2. Spawn appropriate analysis agents in parallel
  3. Collect and synthesize all findings
  4. Generate comprehensive security report

  Return complete findings with severity classifications."
```

3. **Present Results**:
   After the security-orchestrator completes:
   - Show summary statistics
   - List critical/high findings
   - Provide risk assessment
   - Offer to dive deeper or provide fixes

## Example Usage

```
User: /audit examples/vulnerable-evm/1-reentrancy.sol

You: I'll perform a security audit using our multi-agent system.

[Spawns security-orchestrator agent via Task tool]

[Security orchestrator detects EVM, spawns static-analysis-agent and adversarial-agent]

[Agents execute and return findings]

You present results:

📊 Security Audit Complete

Project: examples/vulnerable-evm/1-reentrancy.sol
Chain: EVM (Solidity)
Mode: Standard

Findings:
- CRITICAL: 1
- HIGH: 0
- MEDIUM: 0
- LOW: 0

🔴 CRITICAL Issues:
1. Reentrancy vulnerability in withdraw() function
   - Location: 1-reentrancy.sol:30
   - Detected by: slither-agent, foundry-agent
   - Description: External call before state update allows reentrancy attack
   - Impact: Complete fund drainage possible
   - Fix: Use checks-effects-interactions pattern or ReentrancyGuard

Risk Level: CRITICAL - DO NOT DEPLOY

Would you like me to provide code fixes or explain the attack vector?
```

## Arguments

- **Project path**: First argument after /audit (required)
- **--quick**: Fast audit (2-5 min, traditional tools only)
- **--standard**: Standard audit (5-10 min, traditional + adversarial) [DEFAULT]
- **--deep**: Deep audit (15-30 min, exhaustive analysis)
- **--format**: Output format (markdown, html, json) [DEFAULT: markdown]

## Wave Mode for Large Audits

For projects with >2000 LOC or >20 contracts, activate wave mode for comprehensive analysis:

### Wave Activation Criteria
- Complexity score >= 0.7
- File count > 20
- Multiple operation types required

### Wave Execution Strategy

**Wave 1: Discovery & Fast Analysis** (2-5 min)
```markdown
Parallel agents:
- Run pre-audit hook: ./.claude/hooks/pre-audit.sh [path] [mode]
- Spawn static-analysis-agent with mode=quick
- Identify high-risk contracts and functions
- Create initial findings list
```

**Wave 2: Deep Static Analysis** (5-10 min)
```markdown
Based on Wave 1 results:
- Focus Mythril on high-risk contracts (top 5)
- Run extended Foundry fuzz tests
- Analyze cross-contract interactions
```

**Wave 3: Adversarial Testing** (5-10 min)
```markdown
Spawn in parallel:
- mev-hunter-agent: sandwich, frontrunning, liquidation
- flash-loan-detector: price manipulation, governance
- invariant-checker: 32 protocol invariants
```

**Wave 4: Synthesis & Reporting** (2-5 min)
```markdown
- Combine all findings from Waves 1-3
- Filter false positives
- Identify attack chains
- Calculate security score
- Generate comprehensive report
- Run post-audit hook: ./.claude/hooks/post-audit.sh
```

### Wave Mode Example

```
User: /audit ./large-defi-protocol --deep

Claude Code detects:
- 45 Solidity files
- 8,500 LOC
- DeFi protocol with AMM, lending, governance

Activates wave mode:

Wave 1: Discovery [████████░░] 80%
  - Found 23 potential issues
  - Identified 8 high-risk contracts

Wave 2: Deep Analysis [██████░░░░] 60%
  - Running Mythril on Pool.sol, Vault.sol...
  - 3 new critical findings

Wave 3: Adversarial [████░░░░░░] 40%
  - Testing MEV vulnerabilities
  - Simulating flash loan attacks

Wave 4: Synthesis [██░░░░░░░░] 20%
  - Combining 47 findings
  - Filtering 12 false positives
  - Generating report

Complete! Security Score: 62/100 (Grade: D)
Critical: 2 | High: 5 | Medium: 15 | Low: 13
```

## Hooks Integration

### Pre-Audit Hook
```bash
./.claude/hooks/pre-audit.sh [project-path] [mode]
```
Validates tools, project structure, and estimates complexity.

### Post-Audit Hook
```bash
./.claude/hooks/post-audit.sh ./audit-results [project-name]
```
Generates summary report, calculates security score, sends notifications.

## Notes

- The security-orchestrator agent handles all orchestration
- Chain detection is automatic (EVM vs Solana)
- Agents run in parallel for optimal performance
- Results are synthesized and deduplicated automatically
- Wave mode auto-activates for large/complex projects
- Hooks provide environment validation and reporting
