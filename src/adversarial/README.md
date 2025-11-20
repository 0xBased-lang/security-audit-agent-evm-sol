# Adversarial Agent Framework

Advanced MEV, economic exploit, and cross-protocol vulnerability detection system.

## Directory Structure

```
adversarial/
├── agents/              # Agent implementations
│   ├── base_agent.py
│   ├── attacker_agents.py
│   ├── defender_agent.py
│   └── meta_agent.py
├── strategies/          # Attack strategy templates
│   ├── sandwich.py
│   ├── oracle_manipulation.py
│   ├── flash_loan.py
│   ├── liquidation.py
│   ├── arbitrage.py
│   └── governance.py
├── search/              # Search algorithms
│   ├── evolutionary.py
│   ├── mcts.py
│   ├── drl.py
│   └── solver_guided.py
├── simulation/          # Blockchain simulation
│   ├── evm_environment.py
│   ├── solana_environment.py
│   └── forking.py
├── invariants/          # Invariant definitions
│   ├── amm_invariants.py
│   ├── lending_invariants.py
│   └── oracle_invariants.py
└── orchestrator.py      # Main coordinator
```

## Status

- **Research**: ✅ Complete
- **Architecture Design**: ✅ Complete
- **Implementation**: 🚧 Phase 1 MVP in progress
- **Testing**: ⏳ Pending
- **Documentation**: 🚧 In progress

## Quick Start

```python
from adversarial import AdversarialOrchestrator

# Initialize framework
orchestrator = AdversarialOrchestrator(
    chain='evm',
    project_path='./contracts',
    fork_block=18000000
)

# Run adversarial testing
results = orchestrator.run_adversarial_test(
    strategies=['sandwich', 'oracle_manipulation', 'flash_loan'],
    search_algorithm='evolutionary',
    max_iterations=1000
)

# Get findings
print(f"Vulnerabilities found: {len(results.vulnerabilities)}")
print(f"Invariants broken: {results.invariants_violated}")
print(f"Economic impact: ${results.max_exploit_profit}")
```

## See Also

- [ADVERSARIAL_AGENTS.md](../../docs/ADVERSARIAL_AGENTS.md) - Complete documentation
- [ADVERSARIAL_QUICKSTART.md](../../docs/ADVERSARIAL_QUICKSTART.md) - Getting started guide
- [Strategy Templates](./strategies/) - Pre-built attack strategies
- [Examples](../../examples/adversarial/) - Example usage

## Current Status: Phase 1 MVP

**Goal**: Basic adversarial testing for AMM protocols

**Completed**:
- ✅ Research and architecture design
- ✅ Documentation framework
- ⏳ Simulation environment (in progress)

**Next**:
- ⏳ Strategy template system
- ⏳ Evolutionary search implementation
- ⏳ Integration with main framework
