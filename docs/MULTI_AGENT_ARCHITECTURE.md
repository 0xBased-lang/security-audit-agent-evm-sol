# Multi-Agent Security Audit Architecture

**Purpose**: Professional blockchain security auditing framework using Claude Code's native multi-agent orchestration
**Approach**: Option B + C - Comprehensive architecture with proper agent design
**Research Date**: 2025-01-20

---

## 🎯 Core Insight from Research

### What We Learned About Claude Code Agents

**From Anthropic's Multi-Agent Research System**:
- Lead agent (Orchestrator) coordinates 3-5 specialized sub-agents
- Sub-agents operate in **parallel** for speed
- Each sub-agent has **clear objectives** and **explicit output formats**
- Lead agent synthesizes findings and determines next steps
- **90% performance improvement** using multi-agent vs single-agent

**From Community (wshobson/agents)**:
- 85 specialized agents organized across 63 plugins
- **Model assignment strategy**: Haiku for fast/deterministic tasks, Sonnet for complex reasoning
- **Progressive disclosure**: Load only what's needed (minimize token usage)
- **Granular isolation**: Each plugin loads only its specific agents/skills
- **Orchestration chains**: E.g., backend-architect → database-architect → frontend-developer → test-automator → security-auditor

**Key Configuration Pattern**:
```markdown
---
name: security-scanner
description: "Scans smart contracts for vulnerabilities using static analysis"
tools: Read, Grep, Glob, Bash
model: sonnet  # or haiku for simpler tasks
---
System prompt with specific instructions...
```

---

## 🏗️ Proposed Multi-Agent Security Architecture

### Agent Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│           Lead Security Orchestrator (Sonnet)            │
│                                                          │
│  Responsibilities:                                       │
│  - Analyze user's audit request                         │
│  - Determine which security sub-agents to activate      │
│  - Coordinate parallel execution                        │
│  - Synthesize findings from all agents                  │
│  - Identify attack chains & compound risks              │
│  - Generate final comprehensive report                  │
└────────────┬────────────────────────────────────────────┘
             │
             ├──> Spawns Sub-Agents in Parallel:
             │
    ┌────────┴──────────┬──────────────┬────────────────┐
    ▼                   ▼              ▼                ▼
┌─────────┐     ┌──────────────┐  ┌──────────┐  ┌────────────┐
│ Static  │     │ Adversarial  │  │  False   │  │   Report   │
│Analysis │     │   Testing    │  │Positive  │  │ Generator  │
│ Agent   │     │    Agent     │  │ Filter   │  │   Agent    │
│(Sonnet) │     │   (Sonnet)   │  │ (Haiku)  │  │  (Haiku)   │
└────┬────┘     └──────┬───────┘  └─────┬────┘  └─────┬──────┘
     │                 │                │              │
     │ coordinates:    │ coordinates:   │              │
     ▼                 ▼                │              │
┌─────────────┐   ┌─────────────┐      │              │
│Tool Agents: │   │Tool Agents: │      │              │
│• Slither    │   │• Invariant  │      │              │
│• Mythril    │   │  Checker    │      │              │
│• Foundry    │   │• MEV Hunter │      │              │
│• Echidna    │   │• Flash Loan │      │              │
│(Haiku)      │   │  Detector   │      │              │
└─────────────┘   │(Haiku)      │      │              │
                  └─────────────┘      │              │
                                       │              │
                  All findings flow to: │              │
                                       ▼              ▼
                              ┌──────────────────────────┐
                              │  Synthesis & Reporting   │
                              │   (Lead Orchestrator)    │
                              └──────────────────────────┘
```

### Agent Roles & Responsibilities

#### 1. **Lead Security Orchestrator** (Sonnet - Complex Reasoning)
**Location**: `.claude/agents/security-orchestrator.md`

**Responsibilities**:
- Analyze user's security audit request
- Determine scope (EVM vs Solana, contract complexity)
- Spawn appropriate sub-agents based on project type
- Coordinate parallel execution
- Collect and synthesize findings from all agents
- Identify attack chains (vulnerabilities that compound)
- Detect false positives by cross-referencing
- Prioritize findings by severity + feasibility
- Generate executive summary
- Provide strategic remediation recommendations

**Why Sonnet**: Complex reasoning needed for synthesis, attack chain detection, strategic analysis

---

#### 2. **Static Analysis Agent** (Sonnet - Complex Coordination)
**Location**: `.claude/agents/static-analysis-agent.md`

**Responsibilities**:
- Coordinate all static analysis tools
- Spawn tool-specific agents (Slither, Mythril, etc.)
- Collect results from tool agents
- Normalize findings to common format
- Identify high-confidence issues (found by multiple tools)
- Return structured findings to orchestrator

**Sub-agents it coordinates**:
- Slither Agent (Haiku)
- Mythril Agent (Haiku)
- Foundry Agent (Haiku)
- Echidna Agent (Haiku)
- Certora Agent (Haiku, optional)

**Why Sonnet**: Needs to reason about which tools to use, coordinate multiple tool agents, interpret conflicting results

---

#### 3. **Slither Analysis Agent** (Haiku - Fast, Deterministic)
**Location**: `.claude/agents/slither-agent.md`

**Responsibilities**:
- Execute Slither on target contracts
- Parse JSON output
- Extract vulnerabilities
- Map to standard severity levels
- Return findings in structured format

**Tools**: Bash, Read, Write
**Model**: Haiku (fast execution, deterministic task)

**Example Task**:
```
Input: /path/to/contract.sol
Output: {
  "findings": [
    {
      "type": "reentrancy",
      "severity": "HIGH",
      "location": "contract.sol:42",
      "description": "...",
      "detected_by": "slither"
    }
  ]
}
```

---

#### 4. **Adversarial Testing Agent** (Sonnet - Complex Strategy)
**Location**: `.claude/agents/adversarial-agent.md`

**Responsibilities**:
- Design economic attack scenarios
- Spawn specialized attack agents
- Simulate MEV exploitation
- Test protocol invariants
- Check flash loan vulnerabilities
- Oracle manipulation testing
- Return exploit sequences with profit estimates

**Sub-agents it coordinates**:
- MEV Hunter Agent (Haiku)
- Flash Loan Detector Agent (Haiku)
- Oracle Manipulation Agent (Haiku)
- Invariant Checker Agent (Haiku)

**Why Sonnet**: Strategy design, determining which attacks to test, complex scenario orchestration

---

#### 5. **MEV Hunter Agent** (Haiku - Focused Execution)
**Location**: `.claude/agents/mev-hunter-agent.md`

**Responsibilities**:
- Test for sandwich attack vulnerabilities
- Check liquidation sniping opportunities
- Analyze arbitrage exploitation potential
- Simulate frontrunning scenarios
- Return exploitation sequences if found

**Tools**: Bash (for simulation), Read
**Model**: Haiku

**Example Finding**:
```json
{
  "type": "sandwich_attack",
  "severity": "CRITICAL",
  "profit_potential": "12.5 ETH",
  "attack_sequence": [
    "1. Frontrun swap with 100 ETH",
    "2. User's swap executes at manipulated price",
    "3. Backrun to extract profit"
  ],
  "feasibility": 92
}
```

---

#### 6. **False Positive Filter Agent** (Haiku - Pattern Matching)
**Location**: `.claude/agents/false-positive-filter.md`

**Responsibilities**:
- Review all findings from other agents
- Identify known false positive patterns
- Check if "vulnerable" code is actually protected
- Filter out low-value informational findings
- Return filtered list with reasoning

**Why Haiku**: Deterministic pattern matching, fast execution

**Example Patterns**:
- "Reentrancy" but uses ReentrancyGuard
- "tx.origin" in view-only function
- "Unchecked call" but return value is checked later
- "Integer overflow" but uses Solidity 0.8+

---

#### 7. **Report Generator Agent** (Haiku - Template-Based)
**Location**: `.claude/agents/report-generator.md`

**Responsibilities**:
- Receive structured findings from orchestrator
- Generate markdown report
- Create severity-based sections
- Format vulnerability details
- Generate remediation recommendations
- Create executive summary

**Why Haiku**: Template-based generation, fast execution

---

### Tool-Level Agents (All Haiku)

**Principle**: One agent per security tool for focused execution

```
.claude/agents/tools/
├── slither-agent.md         # Slither static analysis
├── mythril-agent.md         # Mythril symbolic execution
├── foundry-agent.md         # Foundry fuzzing
├── echidna-agent.md         # Echidna property testing
├── clippy-agent.md          # Rust/Solana linting
├── cargo-audit-agent.md     # Solana dependency scanning
└── anchor-agent.md          # Anchor framework lints
```

**Each tool agent**:
- Single responsibility
- Clear input/output format
- Fast execution (Haiku)
- Returns structured data

---

## 🔄 Workflow: How Agents Coordinate

### User Request: `/audit ./my-defi-protocol`

**Step 1: Lead Orchestrator Analyzes**
```
Lead Orchestrator (Sonnet):
- Reads project structure
- Detects: "EVM project, Hardhat-based, DeFi protocol"
- Decides: "Need static analysis + adversarial testing"
- Determines: "Medium complexity, full audit appropriate"
```

**Step 2: Spawn Sub-Agents in Parallel**
```
Lead Orchestrator spawns:
├─> Static Analysis Agent (Sonnet)
│   ├─> Slither Agent (Haiku)
│   ├─> Mythril Agent (Haiku)
│   └─> Foundry Agent (Haiku)
│
└─> Adversarial Testing Agent (Sonnet)
    ├─> MEV Hunter Agent (Haiku)
    ├─> Flash Loan Detector (Haiku)
    └─> Invariant Checker (Haiku)

All agents execute IN PARALLEL → 90% time savings
```

**Step 3: Tool Agents Execute**
```
Slither Agent:
- Runs: slither ./contracts --json output.json
- Parses: 15 findings
- Returns: Structured JSON to Static Analysis Agent

Mythril Agent:
- Runs: myth analyze Contract.sol
- Parses: 8 findings (3 overlap with Slither)
- Returns: Structured JSON to Static Analysis Agent

MEV Hunter Agent:
- Simulates: Sandwich attack on swapExactTokensForTokens()
- Finds: 12.5 ETH profit potential
- Returns: Exploit sequence to Adversarial Agent
```

**Step 4: Mid-Level Agents Synthesize**
```
Static Analysis Agent (Sonnet):
- Receives: 15 from Slither, 8 from Mythril, 6 from Foundry
- Cross-references: 3 findings confirmed by multiple tools
- Deduplicates: 20 unique findings total
- Returns: Structured findings to Lead Orchestrator

Adversarial Testing Agent (Sonnet):
- Receives: 1 MEV vulnerability, 2 flash loan risks, 1 invariant violation
- Assesses: Feasibility scores for each
- Determines: 2 are HIGH feasibility, 2 are theoretical
- Returns: Structured findings to Lead Orchestrator
```

**Step 5: Lead Orchestrator Synthesizes**
```
Lead Orchestrator (Sonnet):
- Receives: 20 static findings + 4 adversarial findings
- Spawns: False Positive Filter Agent (Haiku)
  - Filters: 5 findings are false positives
  - Returns: 19 real vulnerabilities

- Analyzes: Attack chains
  - Identifies: "Reentrancy + MEV = compound critical risk"
  - Identifies: "Flash loan + oracle manipulation = $5M exploit"

- Prioritizes: By severity + feasibility + impact
  1. CRITICAL: Flash loan attack ($5M potential)
  2. CRITICAL: Reentrancy with MEV amplification
  3. HIGH: Oracle manipulation
  ... (16 more)

- Spawns: Report Generator Agent (Haiku)
  - Generates: Comprehensive markdown report
  - Returns: report.md

- Presents to user:
  "🔴 Found 2 CRITICAL vulnerabilities, including a flash loan attack
   with $5M profit potential. Full report: audit-results/report.md"
```

**Total Time**:
- Sequential: ~15 minutes (run each tool one by one)
- **Parallel (multi-agent): ~3 minutes** (90% time savings)

---

## 📁 File Structure

```
.claude/
├── agents/
│   ├── security-orchestrator.md           # Lead (Sonnet)
│   │
│   ├── static-analysis-agent.md           # Mid-level (Sonnet)
│   ├── adversarial-agent.md               # Mid-level (Sonnet)
│   ├── false-positive-filter.md           # Utility (Haiku)
│   ├── report-generator.md                # Utility (Haiku)
│   │
│   └── tools/                             # Tool agents (all Haiku)
│       ├── slither-agent.md
│       ├── mythril-agent.md
│       ├── foundry-agent.md
│       ├── echidna-agent.md
│       ├── mev-hunter-agent.md
│       ├── flash-loan-detector-agent.md
│       ├── invariant-checker-agent.md
│       ├── clippy-agent.md                # Solana
│       └── cargo-audit-agent.md           # Solana
│
├── commands/
│   ├── audit.md                           # Main entry point
│   ├── quick-audit.md                     # Static only
│   └── deep-audit.md                      # Full adversarial
│
└── skills/
    ├── vulnerability-knowledge/           # VULNERABILITIES.md reference
    └── tool-integration/                  # TOOL_INTEGRATION.md reference
```

---

## 🎯 Agent Configuration Examples

### Example 1: Lead Security Orchestrator

**File**: `.claude/agents/security-orchestrator.md`

```markdown
---
name: security-orchestrator
description: "Lead security agent that coordinates comprehensive smart contract audits"
tools: Read, Grep, Glob, Bash, Write, Task
model: sonnet
---

You are the Lead Security Orchestrator for blockchain security audits.

## Your Responsibilities

1. **Analyze Request**: Determine project type (EVM/Solana), complexity, scope
2. **Strategic Planning**: Decide which sub-agents to activate
3. **Coordinate Execution**: Spawn sub-agents in parallel for efficiency
4. **Synthesize Findings**: Collect and analyze results from all agents
5. **Identify Compound Risks**: Detect attack chains and vulnerabilities that amplify each other
6. **Prioritize**: Rank findings by severity, feasibility, and potential impact
7. **Generate Report**: Provide comprehensive security assessment

## Available Sub-Agents

- `static-analysis-agent`: Coordinates Slither, Mythril, Foundry, Echidna
- `adversarial-agent`: Coordinates MEV, flash loan, invariant testing
- `false-positive-filter`: Reviews findings for known false positives
- `report-generator`: Creates formatted markdown reports

## Workflow

When user requests `/audit <path>`:

1. Analyze project structure
2. Spawn static-analysis-agent AND adversarial-agent IN PARALLEL
3. Collect findings from both agents
4. Spawn false-positive-filter to review findings
5. Identify attack chains (e.g., reentrancy + MEV)
6. Prioritize vulnerabilities
7. Spawn report-generator
8. Present findings to user with severity summary

## Output Format

Present results as:
- Executive summary with overall risk level
- Critical findings first
- Exploit chains highlighted
- Remediation priorities
- Link to full report

## Knowledge Base

Reference these for context:
- `docs/VULNERABILITIES.md`: 40+ EVM, 20+ Solana vulnerability patterns
- `docs/TOOL_INTEGRATION.md`: Tool usage and interpretation guides
```

---

### Example 2: Slither Tool Agent

**File**: `.claude/agents/tools/slither-agent.md`

```markdown
---
name: slither-agent
description: "Executes Slither static analyzer and parses results"
tools: Bash, Read, Write
model: haiku
---

You are the Slither Analysis Agent. Your job is to run Slither and return structured findings.

## Execution Steps

1. **Run Slither**:
   ```bash
   slither <contract_path> --json output.json
   ```

2. **Parse Output**:
   - Read output.json
   - Extract vulnerabilities
   - Map to standard format

3. **Return Findings**:
   Return JSON array:
   ```json
   {
     "tool": "slither",
     "findings": [
       {
         "type": "reentrancy",
         "severity": "HIGH",
         "location": "Bank.sol:42:10",
         "function": "withdraw",
         "description": "Reentrancy in withdraw function",
         "confidence": "high",
         "detected_by": "slither"
       }
     ]
   }
   ```

## Error Handling

If Slither fails:
- Check if Slither is installed: `which slither`
- Check if contracts compile
- Return error with diagnostic info

## Severity Mapping

Map Slither impact to standard:
- High → CRITICAL or HIGH
- Medium → MEDIUM
- Low → LOW
- Informational → INFO
```

---

### Example 3: Adversarial Testing Agent

**File**: `.claude/agents/adversarial-agent.md`

```markdown
---
name: adversarial-agent
description: "Coordinates adversarial testing for economic exploits and MEV"
tools: Bash, Read, Write, Task
model: sonnet
---

You are the Adversarial Testing Agent. You coordinate specialized agents to find economic exploits.

## Your Responsibilities

1. **Analyze Protocol**: Understand DeFi mechanics (AMM, lending, oracle, etc.)
2. **Determine Attack Vectors**: Decide which adversarial tests to run
3. **Spawn Attack Agents**: Activate MEV, flash loan, invariant agents in parallel
4. **Assess Feasibility**: Determine real-world exploitability
5. **Return Findings**: Structured exploit sequences with profit estimates

## Available Attack Agents

- `mev-hunter-agent`: Sandwich attacks, frontrunning, liquidation sniping
- `flash-loan-detector-agent`: Flash loan vulnerabilities
- `invariant-checker-agent`: Protocol invariant violations
- `oracle-manipulation-agent`: Price oracle attacks

## Workflow

1. Read contract code
2. Identify protocol type (AMM, lending, governance, etc.)
3. Spawn relevant attack agents IN PARALLEL
4. Collect exploit findings
5. Assess feasibility (0-100 score)
6. Return structured findings with attack sequences

## Output Format

```json
{
  "agent": "adversarial",
  "findings": [
    {
      "type": "flash_loan_attack",
      "severity": "CRITICAL",
      "profit_potential_eth": 45.3,
      "feasibility_score": 88,
      "attack_sequence": [
        "1. Flash loan 50M USDC from Aave",
        "2. Swap USDC → DAI to manipulate pool",
        "3. Trigger liquidation at manipulated price",
        "4. Buy liquidated collateral at discount",
        "5. Repay flash loan",
        "6. Profit: 45.3 ETH"
      ],
      "affected_function": "liquidate",
      "recommendation": "Add flash loan detection, implement TWAP oracle"
    }
  ]
}
```

## Knowledge Base

Reference:
- `docs/ADVERSARIAL_AGENTS.md`: MEV patterns, attack strategies
- `docs/MLSS_ARCHITECTURE_PART1.md`: Invariant checking methods
```

---

## 🚀 Implementation Plan

### Phase 1: Core Agent Infrastructure (Week 1)

**Day 1-2**: Lead Orchestrator
- Create `security-orchestrator.md`
- Test spawning sub-agents
- Verify coordination works

**Day 3**: Tool Agents (Haiku)
- Create Slither agent
- Create Mythril agent
- Test execution and output parsing

**Day 4**: Static Analysis Coordinator
- Create `static-analysis-agent.md`
- Test coordinating tool agents
- Verify result aggregation

**Day 5**: Integration Test
- Run complete workflow on example contract
- Verify findings are accurate
- Refine agent prompts

---

### Phase 2: Adversarial Agents (Week 2)

**Day 1-2**: Attack Agent Infrastructure
- Create MEV hunter agent
- Create flash loan detector agent
- Create invariant checker agent

**Day 3**: Adversarial Coordinator
- Create `adversarial-agent.md`
- Test coordinating attack agents
- Verify exploit detection

**Day 4-5**: Integration & Testing
- Test complete static + adversarial workflow
- Verify parallel execution works
- Measure time savings

---

### Phase 3: Utility Agents (Week 3)

**Day 1**: False Positive Filter
- Pattern database
- Known false positive detection
- Integration with orchestrator

**Day 2**: Report Generator
- Markdown template
- Severity-based grouping
- Executive summary generation

**Day 3-5**: Refinement & Testing
- Test on multiple example contracts
- Refine agent prompts based on results
- Performance optimization

---

## 📊 Expected Benefits

### Performance

**Sequential (Traditional)**:
```
Slither (3 min) → Mythril (5 min) → Foundry (4 min) → Adversarial (8 min)
Total: 20 minutes
```

**Parallel (Multi-Agent)**:
```
┌─ Slither (3 min) ─┐
├─ Mythril (5 min) ─┤
├─ Foundry (4 min) ─┤  All parallel
└─ Adversarial (8min)─┘
Total: 8 minutes (60% faster)
```

### Accuracy

- **Cross-referencing**: Findings confirmed by multiple agents = higher confidence
- **False positive filtering**: Dedicated agent reduces noise
- **Attack chain detection**: Orchestrator identifies compound risks
- **Feasibility scoring**: Adversarial agent assesses real-world exploitability

### User Experience

**Before** (Sequential):
```
Running Slither... ⏳
Running Mythril... ⏳
Running Foundry... ⏳
20 minutes later...
Found 15 issues
```

**After** (Multi-Agent):
```
Orchestrating security audit...
├─ Static analysis agents active ⚡
├─ Adversarial testing agents active ⚡
└─ Synthesis in progress...

8 minutes later...

🔴 CRITICAL: Flash loan attack ($5M potential)
🔴 CRITICAL: Reentrancy + MEV compound risk
🟠 HIGH: Oracle manipulation (3 instances)

19 vulnerabilities found, 2 require immediate attention
Full report: audit-results/report.md
```

---

## 🎓 Key Architecture Decisions

### Why Multi-Agent > Monolithic

**Monolithic Approach** (What we almost built):
```python
# One big orchestrator doing everything
class UnifiedSecurityFramework:
    def audit(self):
        results_slither = run_slither()
        results_mythril = run_mythril()
        results_adversarial = run_adversarial()
        synthesis = synthesize_everything()
        return report
```

**Problems**:
- Sequential execution (slow)
- Single point of failure
- Hard to optimize specific tasks
- Token inefficient (one massive context)
- Hard to iterate on individual components

**Multi-Agent Approach**:
```
Lead Orchestrator spawns:
  ├─ Static Agent (coordinates tool agents)
  ├─ Adversarial Agent (coordinates attack agents)
  └─ Report Agent

Each has focused responsibility, can use appropriate model (Haiku/Sonnet)
Parallel execution, modular, easy to enhance
```

**Benefits**:
- 60-90% faster (parallel execution)
- Each agent optimized for its task
- Easy to add new agents/tools
- Token efficient (progressive disclosure)
- Easier to maintain and improve

---

### Model Assignment Strategy

**Sonnet (Complex Reasoning)**:
- Lead Security Orchestrator
- Static Analysis Agent (coordinates tools)
- Adversarial Agent (designs attacks)
- Any agent needing strategic thinking

**Haiku (Fast, Deterministic)**:
- All tool agents (Slither, Mythril, etc.)
- Attack agents (MEV hunter, flash loan detector)
- False positive filter
- Report generator
- Any pattern-matching or template-based task

**Why this split**:
- Haiku: 3x faster, 5x cheaper
- Most tasks are deterministic (run tool, parse output)
- Only synthesis/strategy needs Sonnet
- Total cost: ~70% cheaper than all-Sonnet

---

## ✅ Success Criteria

**By end of Week 3, user should be able to**:

1. Type `/audit ./my-defi-protocol`
2. Multi-agent system activates automatically
3. Parallel execution completes in <10 minutes
4. Receives comprehensive report with:
   - Critical vulnerabilities highlighted
   - Attack chains identified
   - Feasibility scores for exploits
   - Prioritized remediation plan
5. All findings are actionable and accurate

**Framework provides**:
- Professional-grade security analysis
- 60%+ faster than sequential execution
- Higher accuracy through cross-referencing
- Economic exploit detection
- FREE (no external audit costs)
- Works for EVM and Solana

---

## 📚 Knowledge Base Integration

**Agents reference**:
- `docs/VULNERABILITIES.md` - What to look for
- `docs/TOOL_INTEGRATION.md` - How to run tools
- `docs/ADVERSARIAL_AGENTS.md` - Attack patterns
- `docs/MLSS_ARCHITECTURE_PART1-3.md` - Advanced techniques

**These documents become**:
- Training material for agents
- Pattern libraries for detection
- Remediation guides
- Context for analysis

**Not**:
- Implementation code (we don't build the orchestrator, Claude is the orchestrator)
- API integrations (Claude Code handles tool calling)

---

## 🎯 Next Steps

### Immediate (This Week)

1. **Create Lead Orchestrator Agent** (`.claude/agents/security-orchestrator.md`)
2. **Create First Tool Agent** (`.claude/agents/tools/slither-agent.md`)
3. **Test on Example Contract** (vulnerable ERC20 with known reentrancy)
4. **Verify it works** (finds the bug, reports accurately)

### If Week 1 Succeeds

5. Add more tool agents (Mythril, Foundry)
6. Create Static Analysis coordinator
7. Test parallel execution
8. Build adversarial agents

**Focus**: Build agents that leverage Claude Code's native capabilities, not custom Python orchestrators.

---

**This is the comprehensive, professional architecture you wanted. Ready to build it?** 🚀
