# Unified Security Framework Guide

**Status**: Phase 2 Implementation - Week 1 Complete ✅
**Version**: 2.0
**Date**: 2025-01-20

## Overview

The Unified Security Framework provides a single entry point for comprehensive blockchain security auditing that integrates:

1. **Traditional Static/Dynamic Analysis** (Phase 1 - 15+ tools)
2. **Adversarial Agent Testing** (Phase 1 + 2 - Economic exploits, MEV)
3. **Multi-Chain Support** (100% chain coverage via 5 adapters)
4. **AI-Powered Synthesis** (Claude-powered analysis)

## Quick Start

### Installation

```bash
# Install dependencies
npm install

# Verify tools are available
npm run tools
```

### Basic Usage

#### Python Module

```python
from src.unified_framework import UnifiedSecurityFramework
from src.config import AuditConfig

# Quick audit (2-5 min)
framework = UnifiedSecurityFramework(config=AuditConfig.quick())
report = await framework.audit('./my-project')

# Standard audit (30-60 min)
framework = UnifiedSecurityFramework(config=AuditConfig.standard())
report = await framework.audit('./my-project')

# Deep audit (2-4 hours)
framework = UnifiedSecurityFramework(config=AuditConfig.deep())
report = await framework.audit('./my-project')
```

#### Command Line

```bash
# Quick audit
python -m src --quick ./my-project

# Standard audit
python -m src ./my-project

# Deep audit
python -m src --deep ./my-project

# Custom configuration
python -m src --chain polygon --iterations 5000 ./my-project

# Specify tools
python -m src --tools slither,mythril ./my-project
```

## Architecture

### Python-First Design

The unified framework uses a **Python-first architecture**:

```
┌──────────────────────────────────────────────┐
│     Unified Security Framework (Python)      │
│  - Orchestration                             │
│  - Configuration                             │
│  - Result aggregation                        │
└──────────┬───────────────────────┬───────────┘
           │                       │
           ▼                       ▼
┌──────────────────┐    ┌──────────────────────┐
│  JavaScript      │    │  Adversarial System  │
│  Bridge          │    │  (Python)            │
│                  │    │                      │
│  Calls npm       │    │  - Multi-chain sim   │
│  commands        │    │  - Agent swarms      │
│                  │    │  - Search algorithms │
└──────────────────┘    └──────────────────────┘
```

**Why Python-first?**
- Better ML/RL support for adversarial agents
- Superior async capabilities
- Native Anthropic SDK
- Easier scientific computing integration

### Component Structure

```
src/
├── unified_framework.py      # Main orchestrator
├── unified_cli.py            # CLI interface
├── config.py                 # Configuration management
├── schemas/                  # Data structures
│   ├── vulnerability.py      # Unified vulnerability schema
│   └── __init__.py
├── bridges/                  # Cross-language integration
│   ├── javascript_bridge.py  # JS → Python bridge
│   └── __init__.py
├── adversarial/             # Phase 1 + 2 adversarial
│   ├── orchestrator.py
│   ├── simulation/
│   │   ├── adapters/        # Multi-chain support
│   │   │   ├── anvil_adapter.py      ✅
│   │   │   ├── hardhat_adapter.py    ✅
│   │   │   ├── direct_rpc_adapter.py ✅
│   │   │   ├── revm_adapter.py       (Phase 2+)
│   │   │   └── tenderly_adapter.py   (Phase 2+)
│   │   └── ...
│   └── ...
└── core/                    # Phase 1 traditional (JS)
    ├── AuditOrchestrator.js
    └── ...
```

## Audit Modes

### Quick Mode (2-5 minutes)
```python
config = AuditConfig.quick()
```

**Includes:**
- ✅ Traditional static analysis (Slither, Mythril, etc.)
- ✅ AI analysis
- ❌ Adversarial testing (disabled)

**Use when:**
- Rapid feedback needed
- CI/CD pre-commit hooks
- Initial vulnerability scan

---

### Standard Mode (30-60 minutes) [DEFAULT]
```python
config = AuditConfig.standard()
```

**Includes:**
- ✅ Traditional static analysis
- ✅ Basic adversarial testing (1000 iterations)
- ✅ AI synthesis
- ✅ Cross-referencing and deduplication

**Use when:**
- Regular security audits
- Pre-deployment checks
- Comprehensive vulnerability assessment

**What it tests:**
- All traditional vulnerabilities (OWASP Top 10)
- Basic economic exploits (flash loans, oracle manipulation)
- MEV vulnerabilities (sandwich attacks)
- Protocol invariant violations

---

### Deep Mode (2-4 hours)
```python
config = AuditConfig.deep()
```

**Includes:**
- ✅ Traditional static analysis
- ✅ Deep adversarial testing (10,000 iterations)
- ✅ Advanced agent swarms (9+ agent archetypes)
- ✅ Historical MEV pattern learning
- ✅ Cross-protocol attack analysis
- ✅ Full feasibility filtering

**Use when:**
- High-value protocols (>$10M TVL)
- Before mainnet deployment
- Post-incident analysis
- Comprehensive security assessment

## Configuration

### AuditConfig Options

```python
from src.config import AuditConfig

config = AuditConfig(
    # Audit mode
    mode="standard",  # "quick", "standard", "deep"

    # Traditional audit
    traditional_enabled=True,
    traditional_tools=None,  # None = all, or ["slither", "mythril"]
    traditional_timeout=600,  # seconds

    # Adversarial testing
    adversarial_enabled=True,
    adversarial_iterations=1000,
    adversarial_strategies=None,  # None = all
    adversarial_timeout=3600,

    # Chain configuration
    chain="ethereum",
    fork_block=None,  # Latest block if None
    simulation_adapter=None,  # Auto-select if None

    # AI analysis
    ai_enabled=True,
    ai_model="claude-sonnet-4",

    # Performance
    parallel_execution=True,
    max_workers=4,

    # Output
    output_dir="./audit-results",
    output_formats=["json", "markdown", "html"],
    verbose=False,
)
```

## Unified Vulnerability Schema

All findings are normalized to a unified schema:

```python
@dataclass
class UnifiedVulnerability:
    # Core identification
    id: str
    type: str
    severity: VulnerabilitySeverity  # CRITICAL, HIGH, MEDIUM, LOW, INFO

    # Description
    title: str
    description: str
    location: VulnerabilityLocation

    # Detection metadata
    detected_by: str
    detection_date: datetime
    confidence: float  # 0.0-1.0

    # Impact
    potential_loss_usd: Optional[float]

    # Exploitability (from Layer 8 - Feasibility Filter)
    feasibility_score: Optional[float]  # 0-100
    exploit_complexity: Optional[str]

    # Adversarial specific
    exploit_transaction_sequence: Optional[List[Dict]]
    profit_extracted: Optional[float]
    invariant_violated: Optional[str]

    # Remediation
    recommendation: str
    example_fix: Optional[str]

    # Cross-referencing
    confirmed_by: List[str]  # Other tools that found same issue
    related_vulnerabilities: List[str]
```

### Priority Scoring

Vulnerabilities are automatically prioritized using:

```python
priority_score = (
    severity * 0.4 +
    feasibility * 0.3 +
    impact * 0.2 +
    confidence * 0.1
)
```

## Multi-Chain Support

### Automatic Adapter Selection

The framework automatically selects the best simulation adapter:

```python
def select_adapter(chain: str) -> SimulationAdapter:
    if chain in ANVIL_SUPPORTED:
        return AnvilAdapter()  # Fastest (Foundry)
    elif has_tenderly_key():
        return TenderlyAdapter()  # 90+ chains
    elif has_hardhat_config(chain):
        return HardhatAdapter()  # Custom EVMs
    elif has_rpc_endpoint(chain):
        return DirectRPCAdapter()  # UNIVERSAL FALLBACK
    else:
        raise UnsupportedChainError()  # Should never happen
```

**100% Chain Coverage** - DirectRPC adapter works with ANY chain that has an RPC endpoint.

### Adapter Capabilities

| Adapter | Chains | Forking | Snapshots | Speed | Status |
|---------|--------|---------|-----------|-------|--------|
| **Anvil** | Ethereum, Polygon, Arbitrum, Optimism, Base | ✅ | ✅ | Very Fast | ✅ Functional |
| **Hardhat** | Custom EVMs | ✅ | ✅ | Medium | ✅ Functional |
| **DirectRPC** | **ANY** | ❌ | ❌ | Slow | ✅ Functional |
| **REVM** | Standard EVMs | ✅ | ✅ | Fastest | ⏳ Phase 2+ |
| **Tenderly** | 90+ chains | ✅ | ✅ | Fast | ⏳ Phase 2+ |

## Output Formats

### JSON Report
```bash
python -m src --format json ./project
```

Contains:
- All vulnerabilities (full details)
- Statistics and summaries
- Tool execution metadata
- Machine-readable format

### Markdown Report
```bash
python -m src --format markdown ./project
```

Contains:
- Executive summary
- Vulnerability breakdown by severity
- Recommendations
- Human-readable format

### HTML Report
```bash
python -m src --format html ./project
```

Contains:
- Interactive visualization
- Filterable vulnerability list
- Code highlighting
- Shareable format

## Integration with Claude Code

### Slash Commands (Coming Soon)

```bash
# Quick audit
/audit --quick ./project

# Standard audit
/audit ./project

# Deep audit
/audit --deep ./project

# Adversarial testing only
/adversarial --strategies sandwich,oracle_manipulation

# Setup continuous monitoring
/continuous setup
```

### Session Hooks (Coming Soon)

```bash
# .claude/hooks/session-start.sh
# Automatically run security baseline on session start
python -m src --quick . > /tmp/security-baseline.txt
```

## Error Handling

### 3-Layer Error Handling

1. **Tool Level**: Individual tool failures are caught and logged
   ```python
   try:
       slither_results = run_slither()
   except ToolError:
       log_warning("Slither unavailable")
       continue  # Skip gracefully
   ```

2. **Adapter Level**: Fallback to alternative adapters
   ```python
   try:
       adapter = AnvilAdapter()
   except AnvilNotFoundError:
       adapter = HardhatAdapter()  # Fallback
   ```

3. **System Level**: Graceful degradation
   ```python
   if traditional_failed and adversarial_failed:
       raise SystemError("Complete audit failure")
   elif traditional_failed:
       warn("Traditional audit unavailable")
       return_partial_results()
   ```

## Performance Optimization

### Parallelization

By default, tools run in parallel:

```python
# Traditional tools run in parallel
await asyncio.gather(
    run_slither(),
    run_mythril(),
    run_echidna(),
)
```

### Caching

Results are cached to avoid redundant work:

```bash
# Results cached in
./audit-results/cache/
```

### Resource Management

```python
config = AuditConfig(
    max_memory_mb=8192,       # Max memory usage
    max_execution_time=14400,  # 4 hours max
    max_workers=4,             # Parallel workers
)
```

## Examples

### Example 1: Quick Audit for CI/CD

```python
# ci_audit.py
import asyncio
from src.unified_framework import quick_audit

async def main():
    report = await quick_audit('./contracts')

    # Fail CI if critical vulnerabilities found
    if report.critical_count > 0:
        print(f"❌ {report.critical_count} critical vulnerabilities found")
        exit(1)
    else:
        print("✅ No critical vulnerabilities")
        exit(0)

asyncio.run(main())
```

### Example 2: Custom Configuration

```python
from src.unified_framework import UnifiedSecurityFramework
from src.config import AuditConfig

config = AuditConfig(
    mode='standard',
    chain='polygon',
    fork_block=50000000,
    traditional_tools=['slither', 'mythril'],  # Only these tools
    adversarial_iterations=2000,
    adversarial_strategies=['sandwich', 'oracle_manipulation'],
    output_dir='./security-reports',
)

framework = UnifiedSecurityFramework(config=config)
report = await framework.audit('./defi-protocol')
```

### Example 3: Programmatic Analysis

```python
from src.unified_framework import standard_audit

# Run audit
report = await standard_audit('./my-project')

# Analyze results
critical_vulns = report.get_critical_vulnerabilities()
exploitable = report.get_exploitable_vulnerabilities()

# Filter by type
reentrancy_bugs = [
    v for v in report.vulnerabilities
    if v.type == 'reentrancy'
]

# Get prioritized list
sorted_vulns = report.get_sorted_vulnerabilities()

# Generate custom report
for vuln in sorted_vulns[:10]:  # Top 10
    print(f"{vuln.severity}: {vuln.title}")
    print(f"  Priority: {vuln.get_priority_score():.1f}")
    print(f"  Location: {vuln.location.file}:{vuln.location.line}")
    print()
```

## Troubleshooting

### "npm not found"

Install Node.js and npm:
```bash
# Ubuntu/Debian
sudo apt install nodejs npm

# macOS
brew install node
```

### "Anvil not found"

Install Foundry:
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### "Tool X not available"

Check tool availability:
```bash
npm run tools
```

Install missing tools:
```bash
# Slither
pip install slither-analyzer

# Mythril
pip install mythril
```

### "AI synthesis failed"

Set ANTHROPIC_API_KEY:
```bash
export ANTHROPIC_API_KEY='your-api-key'
```

### "Out of memory"

Reduce parallelization:
```python
config = AuditConfig(
    max_workers=2,  # Reduce from 4
    max_memory_mb=4096,  # Lower limit
)
```

Or use quick mode:
```bash
python -m src --quick ./project
```

## Limitations

### Current Limitations (Phase 2, Week 1)

1. ❌ AI synthesis not yet implemented
2. ❌ Markdown/HTML report generation pending
3. ❌ Only 3 adversarial strategies (need 15+)
4. ❌ No historical MEV learning yet
5. ❌ Limited to 32 protocol invariants (need 100+)

### Known Issues

- Mythril symbolic execution is very slow (use with caution)
- Some tools may have false positives
- DirectRPC adapter cannot manipulate state (testing limitations)

## Roadmap

### Phase 2 (Current) - Weeks 2-8

- [x] Week 1: Unified orchestrator ✅
- [ ] Week 2-3: Enhanced adversarial agents (9+ archetypes)
- [ ] Week 4: Historical MEV pattern learning
- [ ] Week 5: Feasibility filtering (Layer 8)
- [ ] Week 6: AI synthesis implementation
- [ ] Week 7-8: Testing and optimization

### Phase 3 - Weeks 9-16

- [ ] LLM-guided strategy generation (Layer 3)
- [ ] Cross-protocol state graph analysis (Layer 4)
- [ ] Adaptive defense agent (Layer 7)
- [ ] REVM and Tenderly adapters

### Phase 4 - Weeks 17-24

- [ ] Multi-chain context awareness (Layer 9)
- [ ] Continuous monitoring (Layer 10)
- [ ] Production hardening

## Support

- **Documentation**: `docs/` directory
- **Examples**: `examples/` directory
- **Issues**: GitHub Issues
- **Architecture**: `docs/MASTER_INTEGRATION_ARCHITECTURE.md`

## License

See LICENSE file.
