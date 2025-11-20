# Adversarial Agent Framework for Smart Contract Security

> **Advanced MEV, Economic Exploit, and Cross-Protocol Vulnerability Detection**
> Going beyond traditional static analysis to catch the "hard" bugs

**Status**: Research Complete | Architecture Design In Progress | Implementation Phase 1

---

## 🎯 Executive Summary

Traditional security tools (Slither, Mythril, etc.) are excellent at catching code-level vulnerabilities (reentrancy, overflow, missing checks). However, **studies show most big losses come from higher-level issues**:

- **$1.42 Billion lost in 2024** from vulnerabilities that static analyzers miss
- **$953.2M** from access control (often economic exploitation)
- **$289.76M** (51.56%) from MEV sandwich attacks alone
- **$52M** from oracle manipulation across 37 incidents

This framework introduces an **adversarial agent system** that simulates attackers in a DeFi environment to discover:

✅ Economic exploits (oracle manipulation, pool imbalance, free options)
✅ MEV vulnerabilities (sandwiches, liquidation sniping, ordering attacks)
✅ Cross-protocol attacks (composability edges, rehypothecation loops)
✅ Flash loan attack vectors
✅ Liquidity manipulation strategies
✅ Governance attacks

---

## 📊 Research Findings (2024-2025)

### MEV Landscape

| Metric | Value | Source |
|--------|-------|--------|
| **Annual MEV Volume** | $3B+ | 2025 data |
| **Solana MEV (Q2 2025)** | $271M | Helius Report |
| **Ethereum MEV (Q2 2025)** | $129M | MEV data |
| **Arbitrage Txs (Solana/year)** | 90M+ | Jito detection |
| **Average Arb Profit** | $1.58 | Jito data |
| **Sandwich Attack Losses** | $289.76M | DeFi analysis |

### Vulnerability Breakdown (2024)

| Category | Losses | Incidents | Detection Gap |
|----------|--------|-----------|---------------|
| Access Control | $953.2M | Many | ⚠️ High |
| Logic Errors | $63.8M | Many | ⚠️ Critical |
| Reentrancy | $35.7M | Multiple | ✅ Well-covered |
| Flash Loans | $33.8M | Multiple | ⚠️ High |
| Oracle Manipulation | $52M | 37 | ⚠️ Critical |
| Input Validation | $14.6M | Multiple | ✅ Covered |

**Key Insight**: The largest losses come from emergent behavior problems, not just "this function is unsafe."

---

## 🏗️ Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│              ADVERSARIAL SECURITY FRAMEWORK                  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Claude AI Orchestrator (Meta-Agent)         │   │
│  │  • Strategy Selection                               │   │
│  │  • Multi-Agent Coordination                        │   │
│  │  • Learning from Results                           │   │
│  └──────────────┬──────────────────────────────────────┘   │
│                 │                                            │
│       ┌─────────┴─────────┐                                │
│       │                   │                                 │
│  ┌────▼──────┐      ┌────▼──────┐                         │
│  │  Attacker │      │ Defender  │                         │
│  │  Agents   │      │  Agent    │                         │
│  └────┬──────┘      └────┬──────┘                         │
│       │                   │                                 │
│  ┌────▼───────────────────▼──────┐                        │
│  │   Simulation Environment      │                        │
│  │  • EVM Fork (Anvil/REVM)     │                        │
│  │  • Solana Local Validator    │                        │
│  │  • Real-Time State           │                        │
│  └────┬──────────────────────────┘                        │
│       │                                                     │
│  ┌────▼──────────────────────────┐                        │
│  │   Strategy Template Library   │                        │
│  │  • Sandwich Attacks           │                        │
│  │  • Oracle Manipulation        │                        │
│  │  • Flash Loan Exploits        │                        │
│  │  • Liquidation Sniping        │                        │
│  │  • Cross-Protocol Arbs        │                        │
│  └────┬──────────────────────────┘                        │
│       │                                                     │
│  ┌────▼──────────────────────────┐                        │
│  │     Search Algorithms         │                        │
│  │  • Evolutionary Search        │                        │
│  │  • MCTS (Tree Search)        │                        │
│  │  • RL (DQN/PPO)              │                        │
│  │  • Solver-Guided (Z3/SMT)    │                        │
│  └────┬──────────────────────────┘                        │
│       │                                                     │
│  ┌────▼──────────────────────────┐                        │
│  │    Invariant & Oracle System  │                        │
│  │  • Protocol Invariants        │                        │
│  │  • Economic Constraints       │                        │
│  │  • Safety Properties          │                        │
│  └───────────────────────────────┘                        │
└──────────────────────────────────────────────────────────┘
```

---

## 🔬 Component Deep Dive

### 1. Simulation Environment Layer

#### EVM Environment
```
Technology Stack:
├── Foundry Anvil: Local blockchain fork
├── REVM: Rust EVM implementation
├── Alloy: Modern Ethereum library (replaces ethers-rs)
├── Cryo: Blockchain data extraction
└── web3-ethereum-defi: Protocol interactions
```

**Key Features**:
- Mainnet fork at specific block height
- Historical trace replay from MEV-inspect-rs
- High-performance transaction simulation (60% faster with Alloy)
- Support for transaction bundles (Flashbots-style)
- Real-time state updates

**Actions Available to Agents**:
```python
# High-level actions (not raw opcodes)
actions = [
    swap(tokenA, tokenB, amount, pool, router),
    borrow(asset, amount, protocol, collateral),
    provide_liquidity(pool, amounts),
    flash_loan(token, amount, callback),
    liquidate(user, protocol, collateral_token),
    manipulate_oracle(pool, amount, direction),
    build_bundle([tx1, tx2, ...], position='before')
]
```

#### Solana Environment
```
Technology Stack:
├── solana-program-test: Local validator
├── Anchor: Framework integration
├── Jito: Bundle/MEV support
└── SolanaFM: Transaction analysis
```

**Actions Available**:
```rust
// Solana-specific actions
actions = [
    send_instruction(program_id, accounts, data),
    compose_cpi_chain(programs),
    create_jito_bundle(txs, tip),
    manipulate_price_feed(oracle, value),
    drain_pool(pool_address, method)
]
```

---

### 2. Strategy Template Library

#### Template Structure
```python
class StrategyTemplate:
    """Base class for attack strategies"""

    def __init__(self, name, category, parameters):
        self.name = name
        self.category = category  # 'sandwich', 'oracle', 'flash_loan', etc.
        self.parameters = parameters  # Mutable params for evolution
        self.success_rate = 0.0
        self.avg_profit = 0.0

    def generate_transactions(self, env_state):
        """Generate transaction sequence for this strategy"""
        raise NotImplementedError

    def check_preconditions(self, env_state):
        """Verify strategy can be executed"""
        raise NotImplementedError

    def calculate_profit(self, initial_state, final_state):
        """Calculate profit from strategy execution"""
        raise NotImplementedError
```

#### Pre-Built Strategy Templates

**1. Sandwich Attack**
```python
class SandwichAttack(StrategyTemplate):
    """
    Classic MEV sandwich:
    1. Detect victim transaction in mempool
    2. Front-run: Buy token before victim
    3. Let victim execute (raises price)
    4. Back-run: Sell token at higher price
    """

    parameters = {
        'pool': UniswapV2Pool,
        'token_in': WETH,
        'token_out': DAI,
        'victim_amount': float,
        'front_run_amount': float,  # Evolved by search
        'slippage_tolerance': float,  # Evolved
        'gas_price_multiplier': float,  # Evolved
    }

    def generate_transactions(self, victim_tx):
        front_run = swap(
            WETH, DAI,
            amount=self.parameters['front_run_amount'],
            gas_price=victim_tx.gas_price * self.parameters['gas_price_multiplier']
        )

        back_run = swap(
            DAI, WETH,
            amount=front_run.output_amount,
            gas_price=victim_tx.gas_price * 0.99
        )

        return [front_run, victim_tx, back_run]
```

**2. Oracle Manipulation + Borrow**
```python
class OracleManipulationAttack(StrategyTemplate):
    """
    Flash loan oracle manipulation:
    1. Flash loan large amount
    2. Manipulate oracle price (swap in low-liquidity pool)
    3. Borrow from protocol using manipulated price
    4. Restore price
    5. Repay flash loan
    6. Profit from under-collateralized borrow
    """

    parameters = {
        'flash_loan_amount': float,
        'manipulation_pool': address,  # Low liquidity pool
        'target_protocol': address,  # Lending protocol
        'borrow_asset': address,
        'price_deviation_target': float,  # How much to manipulate
    }

    def generate_transactions(self, env_state):
        # Flash loan callback chain
        return [
            flash_loan(USDC, self.parameters['flash_loan_amount']),
            # In callback:
            swap(USDC, TARGET, amount=flash_loan_amount, pool=manipulation_pool),
            borrow(TARGET, amount=max_possible, protocol=target_protocol),
            swap(TARGET, USDC, amount=remaining, pool=manipulation_pool),
            # End callback, flash loan repaid
        ]
```

**3. Cross-Protocol Arbitrage**
```python
class CrossProtocolArbitrage(StrategyTemplate):
    """
    Multi-DEX arbitrage:
    1. Detect price discrepancy between DEXes
    2. Buy on cheaper DEX
    3. Sell on expensive DEX
    4. Profit from price difference
    """

    parameters = {
        'dex_a': UniswapV2,
        'dex_b': SushiSwap,
        'token_path': [WETH, USDC, DAI],
        'amount': float,
        'min_profit_threshold': float,
    }
```

**4. Liquidation Sniping**
```python
class LiquidationSniper(StrategyTemplate):
    """
    Profit from liquidations:
    1. Monitor under-collateralized positions
    2. Front-run other liquidators
    3. Execute liquidation with bonus
    """

    parameters = {
        'protocol': Aave,
        'target_user': address,
        'collateral_token': address,
        'debt_token': address,
        'gas_price_multiplier': float,
    }
```

**5. Free Option Exploit**
```python
class FreeOptionExploit(StrategyTemplate):
    """
    Exploit protocols allowing free options:
    1. Place large order
    2. Wait for price movement
    3. Cancel if unfavorable, execute if favorable
    """
```

**6. Governance Attack**
```python
class GovernanceAttack(StrategyTemplate):
    """
    Flash loan governance attack:
    1. Flash loan governance tokens
    2. Vote on malicious proposal
    3. Proposal passes (if enough votes)
    4. Return tokens
    """

    parameters = {
        'governance_token': address,
        'flash_loan_amount': float,
        'proposal_id': int,
        'vote_direction': bool,
    }
```

---

### 3. Search Algorithms

#### 3.1 Evolutionary Search

Best for: Initial strategy discovery and parameter optimization

```python
class EvolutionarySearch:
    """
    Genetic algorithm for strategy evolution
    Based on: AlphaFuzz, ContractFuzzer research
    """

    def __init__(self, population_size=100, mutation_rate=0.1):
        self.population = []  # Strategy instances
        self.generation = 0

    def evolve(self, environment, iterations=100):
        """
        1. Select: Keep top-K performing strategies
        2. Crossover: Combine successful strategies
        3. Mutate: Random parameter changes
        4. Evaluate: Test all strategies in simulation
        """

        for gen in range(iterations):
            # Evaluate fitness
            fitness_scores = []
            for strategy in self.population:
                profit, broken_invariants = environment.execute(strategy)
                fitness = alpha * profit + beta * broken_invariants
                fitness_scores.append(fitness)

            # Selection
            top_k = select_top_k(self.population, fitness_scores, k=20)

            # Crossover
            offspring = []
            for i in range(self.population_size - len(top_k)):
                parent1, parent2 = random.sample(top_k, 2)
                child = crossover(parent1, parent2)
                offspring.append(child)

            # Mutation
            for strategy in offspring:
                if random.random() < self.mutation_rate:
                    mutate(strategy)

            # New generation
            self.population = top_k + offspring
            self.generation += 1

        return self.get_best_strategy()

    def crossover(self, strategy1, strategy2):
        """Combine parameters from two strategies"""
        child_params = {}
        for key in strategy1.parameters:
            child_params[key] = random.choice([
                strategy1.parameters[key],
                strategy2.parameters[key]
            ])
        return Strategy(strategy1.name, child_params)

    def mutate(self, strategy):
        """Randomly modify strategy parameters"""
        param_to_mutate = random.choice(list(strategy.parameters.keys()))

        if isinstance(strategy.parameters[param_to_mutate], float):
            # Gaussian mutation for floats
            strategy.parameters[param_to_mutate] *= random.gauss(1.0, 0.1)
        elif isinstance(strategy.parameters[param_to_mutate], int):
            # Random walk for ints
            strategy.parameters[param_to_mutate] += random.randint(-10, 10)
```

#### 3.2 Monte Carlo Tree Search (MCTS)

Best for: Multi-step transaction sequences

```python
class MCTSAgent:
    """
    MCTS for transaction sequence optimization
    Based on: AlphaZero approach, RL-BES research
    """

    def __init__(self, exploration_constant=1.41):
        self.root = MCTSNode(state=initial_state)
        self.c = exploration_constant  # UCB1 constant

    def search(self, num_simulations=1000):
        """
        Four phases:
        1. Selection: Navigate tree using UCB1
        2. Expansion: Add new child nodes
        3. Simulation: Rollout to terminal state
        4. Backpropagation: Update statistics
        """

        for _ in range(num_simulations):
            node = self.select(self.root)
            reward = self.simulate(node)
            self.backpropagate(node, reward)

        return self.best_action(self.root)

    def select(self, node):
        """UCB1 selection"""
        while not node.is_terminal():
            if not node.is_fully_expanded():
                return self.expand(node)
            else:
                node = self.best_child(node)
        return node

    def ucb1(self, node, parent):
        """Upper Confidence Bound"""
        if node.visits == 0:
            return float('inf')

        exploit = node.total_reward / node.visits
        explore = self.c * math.sqrt(math.log(parent.visits) / node.visits)
        return exploit + explore

    def expand(self, node):
        """Add new action/child"""
        untried_actions = node.get_untried_actions()
        action = random.choice(untried_actions)
        child_state = node.state.apply_action(action)
        child = MCTSNode(state=child_state, parent=node, action=action)
        node.children.append(child)
        return child

    def simulate(self, node):
        """Random rollout to terminal state"""
        state = node.state.copy()
        while not state.is_terminal():
            action = random.choice(state.get_legal_actions())
            state = state.apply_action(action)

        return self.evaluate(state)  # Profit + invariants broken

    def backpropagate(self, node, reward):
        """Update statistics up the tree"""
        while node is not None:
            node.visits += 1
            node.total_reward += reward
            node = node.parent
```

#### 3.3 Deep Reinforcement Learning

Best for: Learning complex attack patterns

```python
class DRLAgent:
    """
    Deep RL for exploit discovery
    Based on: RLF (RL-guided Fuzzer), PPO, DQN research
    """

    def __init__(self, state_dim, action_dim, algorithm='PPO'):
        self.algorithm = algorithm

        if algorithm == 'PPO':
            self.agent = PPOAgent(state_dim, action_dim)
        elif algorithm == 'DQN':
            self.agent = DQNAgent(state_dim, action_dim)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def train(self, environment, episodes=1000):
        """
        Train agent to maximize reward:
        - Profit from exploits
        - Invariants broken
        - Minus gas costs
        """

        for episode in range(episodes):
            state = environment.reset()
            done = False
            episode_reward = 0

            while not done:
                # Choose action
                action = self.agent.select_action(state)

                # Execute in environment
                next_state, reward, done, info = environment.step(action)

                # Store experience
                self.agent.store_transition(state, action, reward, next_state, done)

                # Learn from experience
                if episode % 10 == 0:
                    self.agent.learn()

                state = next_state
                episode_reward += reward

            print(f"Episode {episode}: Reward = {episode_reward}")

        return self.agent

class PPOAgent:
    """Proximal Policy Optimization"""

    def __init__(self, state_dim, action_dim):
        self.actor = ActorNetwork(state_dim, action_dim)
        self.critic = CriticNetwork(state_dim)
        self.optimizer_actor = Adam(self.actor.parameters())
        self.optimizer_critic = Adam(self.critic.parameters())

    def select_action(self, state):
        """Sample action from policy"""
        state_tensor = torch.FloatTensor(state)
        action_probs = self.actor(state_tensor)
        dist = Categorical(action_probs)
        action = dist.sample()
        return action.item()

    def learn(self):
        """PPO update"""
        # ... PPO algorithm implementation
        pass
```

#### 3.4 SMT Solver-Guided Search

Best for: Mathematical exploits in AMMs, stable pools

```python
class SolverGuidedSearch:
    """
    Use Z3/SMT solver for constraint-based exploit discovery
    """

    def __init__(self):
        self.solver = z3.Solver()

    def find_arbitrage(self, pools):
        """
        Find arbitrage opportunity using constraint solving:

        Variables: trade sizes x1, x2, ..., xn
        Constraints:
        - Pool formulas (constant product, stable swap, etc.)
        - Balance constraints
        - No negative trades
        Objective: Maximize final_balance - initial_balance
        """

        # Define variables
        trades = [z3.Real(f'trade_{i}') for i in range(len(pools))]
        initial_balance = z3.Real('initial')
        final_balance = z3.Real('final')

        # Add constraints
        for i, pool in enumerate(pools):
            self.add_pool_constraints(pool, trades[i])

        # Non-negative trades
        for trade in trades:
            self.solver.add(trade >= 0)

        # Objective: maximize profit
        profit = final_balance - initial_balance
        self.solver.maximize(profit)

        if self.solver.check() == z3.sat:
            model = self.solver.model()
            return self.extract_strategy(model, trades)
        else:
            return None

    def add_pool_constraints(self, pool, trade_amount):
        """Add constraints for specific pool type"""
        if pool.type == 'UniswapV2':
            # Constant product: x * y = k
            # After trade: (x + Δx) * (y - Δy) = k
            pass
        elif pool.type == 'Curve':
            # Stable swap invariant
            pass
```

---

### 4. Invariant & Oracle System

#### Invariant Definition

```python
class Invariant:
    """
    Define protocol safety properties
    """

    def __init__(self, name, check_function, severity='HIGH'):
        self.name = name
        self.check = check_function
        self.severity = severity
        self.violations = []

    def verify(self, state):
        """Check if invariant holds"""
        try:
            result = self.check(state)
            if not result:
                self.violations.append({
                    'timestamp': time.time(),
                    'state': state.copy(),
                    'block': state.block_number
                })
            return result
        except Exception as e:
            logging.error(f"Invariant check failed: {e}")
            return False

# Example invariants

AMM_INVARIANTS = [
    Invariant(
        name="Constant Product",
        check_function=lambda state: (
            state.pool.reserve0 * state.pool.reserve1 >=
            state.pool.k * (1 - state.pool.fee_rate)
        ),
        severity='CRITICAL'
    ),

    Invariant(
        name="No User Profit Without Trading",
        check_function=lambda state: (
            state.user_balance <= state.user_initial_balance + state.user_earned_fees
        ),
        severity='CRITICAL'
    ),

    Invariant(
        name="LP Token Value Preservation",
        check_function=lambda state: (
            state.lp_token_value >= state.lp_initial_value * 0.99  # Allow 1% slippage
        ),
        severity='HIGH'
    )
]

LENDING_INVARIANTS = [
    Invariant(
        name="Solvency",
        check_function=lambda state: (
            state.total_collateral_value * state.collateral_factor >=
            state.total_borrowed_value
        ),
        severity='CRITICAL'
    ),

    Invariant(
        name="No Undercollateralized Borrows",
        check_function=lambda state: all(
            user.collateral_value * state.collateral_factor >= user.borrowed_value
            for user in state.users
        ),
        severity='CRITICAL'
    ),

    Invariant(
        name="Interest Accrual Sanity",
        check_function=lambda state: (
            state.total_interest_accrued <= state.total_borrowed * state.max_apr * state.time_elapsed
        ),
        severity='HIGH'
    )
]

ORACLE_INVARIANTS = [
    Invariant(
        name="Price Deviation Bounded",
        check_function=lambda state: (
            abs(state.oracle_price - state.reference_price) / state.reference_price < 0.10
        ),
        severity='HIGH'
    ),

    Invariant(
        name="Oracle Freshness",
        check_function=lambda state: (
            state.current_timestamp - state.oracle_last_update < state.staleness_threshold
        ),
        severity='MEDIUM'
    )
]
```

---

### 5. Reward Function Design

```python
def calculate_reward(initial_state, final_state, invariants_broken, gas_used, txs_count):
    """
    Multi-objective reward function
    """

    # Profit component (α = 1.0)
    profit = final_state.attacker_balance - initial_state.attacker_balance
    profit_reward = profit * 1.0

    # Invariant violation bonus (β = 10000.0)
    # Heavily reward finding vulnerabilities
    invariant_reward = len(invariants_broken) * 10000.0

    # Critical vulnerability extra bonus
    critical_violations = [inv for inv in invariants_broken if inv.severity == 'CRITICAL']
    critical_bonus = len(critical_violations) * 50000.0

    # Gas cost penalty (γ = 0.01)
    # Encourage efficient exploits
    gas_penalty = gas_used * 0.01

    # Transaction count penalty (δ = 100)
    # Encourage simpler exploits
    tx_penalty = txs_count * 100

    total_reward = (
        profit_reward +
        invariant_reward +
        critical_bonus -
        gas_penalty -
        tx_penalty
    )

    return total_reward, {
        'profit': profit_reward,
        'invariants': invariant_reward,
        'critical': critical_bonus,
        'gas_cost': -gas_penalty,
        'tx_cost': -tx_penalty,
        'total': total_reward
    }
```

---

## 🎮 Agent Types

### 1. Attacker Agents (Red Team)

**Specialized Agents**:
- `SandwichAgent`: MEV sandwich attacks
- `OracleAgent`: Price manipulation
- `FlashLoanAgent`: Flash loan exploits
- `LiquidationAgent`: Liquidation sniping
- `ArbitrageAgent`: Cross-protocol arbs
- `GovernanceAgent`: Governance attacks

Each agent:
- Has specific strategy templates
- Uses appropriate search algorithm
- Optimizes for maximum exploit profit
- Reports successful attack vectors

### 2. Defender Agent (Blue Team)

**Responsibilities**:
- Monitor simulation results
- Identify successful attack patterns
- Suggest mitigations:
  - Parameter changes (fees, caps, delays)
  - Code-level fixes (access control, validation)
  - Architectural changes (oracle design, governance)
- Run "what-if" scenarios with proposed fixes
- Generate security recommendations

### 3. Meta-Agent (Claude AI Orchestrator)

**Responsibilities**:
- Coordinate multiple agent types
- Learn from historical MEV data
- Prioritize attack strategies to explore
- Synthesize findings across agents
- Generate human-readable reports
- Suggest novel attack vectors

---

## 📖 Implementation Roadmap

### Phase 1: MVP (4 weeks) ✅ IN PROGRESS

**Goal**: Basic adversarial testing for one AMM protocol

**Components**:
- [x] Foundry mainnet fork environment
- [ ] 3 strategy templates (sandwich, arb, flash loan)
- [ ] Evolutionary search algorithm
- [ ] 5 basic invariants
- [ ] Simple reward function
- [ ] Basic reporting

**Test Case**: Uniswap V2 fork with known vulnerabilities

---

### Phase 2: Multi-Strategy (6 weeks)

**Goal**: Expand to 10+ attack strategies

**Components**:
- [ ] All 6 agent types
- [ ] 15+ strategy templates
- [ ] MCTS implementation
- [ ] Enhanced reward function
- [ ] Cross-protocol testing
- [ ] MEV pattern learning from historical data

**Test Cases**: Uniswap, Sushiswap, Curve

---

### Phase 3: RL Integration (8 weeks)

**Goal**: Add deep RL for novel exploit discovery

**Components**:
- [ ] DRL agent (PPO/DQN)
- [ ] Experience replay
- [ ] Multi-agent coordination
- [ ] Continuous learning
- [ ] State encoding for neural networks

---

### Phase 4: Solana Support (6 weeks)

**Goal**: Full Solana adversarial testing

**Components**:
- [ ] Solana local validator integration
- [ ] Solana-specific strategies
- [ ] Jito bundle simulation
- [ ] Anchor program testing
- [ ] Cross-chain attack detection

---

### Phase 5: Production Hardening (4 weeks)

**Goal**: Production-ready framework

**Components**:
- [ ] Comprehensive documentation
- [ ] CI/CD integration
- [ ] Performance optimization
- [ ] Cloud deployment options
- [ ] Web dashboard
- [ ] API for external integration

---

## 📚 Technology Stack

### Core Framework
```
Language: Python 3.10+
Agent Framework: LangChain / AutoGen / Custom
AI Model: Claude Sonnet 4.5 (orchestration)
RL Library: Stable-Baselines3 / RLLib
```

### EVM Stack
```
Simulation: Foundry Anvil
EVM Implementation: REVM
Ethereum Library: Alloy (Rust) + py-alloy
Data Extraction: Cryo
Protocol Interaction: web3-ethereum-defi
Historical MEV: mev-inspect-rs integration
```

### Solana Stack
```
Simulation: solana-program-test
Framework: Anchor
MEV: Jito integration
Analysis: SolanaFM API
```

### Search Algorithms
```
Evolutionary: DEAP / PyGAD
MCTS: Custom implementation
RL: Stable-Baselines3 (PPO, DQN)
Solver: Z3-solver (SMT)
```

### Data & Analytics
```
Time-Series: Pandas, NumPy
Visualization: Matplotlib, Plotly
Economics: cadCAD (optional)
Storage: PostgreSQL, Redis
```

---

## 🎯 Success Metrics

### Vulnerability Discovery
- **Novel exploits found**: Target 10+ new attack vectors
- **Invariant violations**: 100% coverage of defined invariants
- **False positive rate**: < 10%
- **Time to discovery**: < 1 hour per protocol

### Performance
- **Simulations per second**: > 100 (EVM), > 50 (Solana)
- **Strategy evolution**: 1000+ generations in 24 hours
- **Memory usage**: < 16GB for full test suite
- **Parallelization**: 8+ agents running concurrently

### Economic Impact
- **Potential savings**: > $1M in prevented exploits
- **Cost per audit**: < $500 (compute + API)
- **Time savings**: 90% reduction vs manual testing
- **Coverage improvement**: 5x more attack vectors vs traditional tools

---

## ⚠️ Limitations & Ethical Considerations

### Current Limitations
- **Computational cost**: High for extensive searches
- **Novel attack patterns**: May miss completely new exploit types
- **Oracle accuracy**: Depends on invariant definitions
- **State space explosion**: Infinite possible transaction sequences

### Ethical Guidelines
- **Responsible disclosure**: Report findings to protocol teams
- **No public exploit code**: Don't publish ready-to-use exploits
- **Testing only**: Never execute against mainnet
- **White-hat focus**: Build for defense, not offense
- **Bug bounties**: Encourage reporting through proper channels

---

## 📊 Comparison with Existing Approaches

| Approach | Vulnerability Types | Discovery Method | Coverage | Cost |
|----------|-------------------|------------------|----------|------|
| **Static Analysis** | Code-level bugs | Pattern matching | High | Low |
| **Symbolic Execution** | Logic bugs | Path exploration | Medium | Medium |
| **Fuzzing** | Crash bugs | Random inputs | Medium | Low |
| **Formal Verification** | Invariant violations | Mathematical proof | Very High | High |
| **Manual Audit** | All types | Expert review | Highest | Very High |
| **Our Framework** | Economic + MEV + Logic | Adversarial simulation | High | Low-Medium |

**Unique Advantages**:
- ✅ Finds emergent vulnerabilities from protocol interactions
- ✅ Simulates real attacker behavior with economic incentives
- ✅ Tests against actual MEV strategies from historical data
- ✅ Continuous learning from new attack patterns
- ✅ Multi-protocol and cross-chain attack detection

---

## 🔗 References & Research

### Key Papers
1. **FlashGuard** (2024): Real-time flash loan attack detection
2. **FlashSyn** (2024): Automated flash loan exploit synthesis
3. **ETHPLOIT** (2020): Fuzzing-based exploit generation
4. **ContractFuzzer** (2018): Smart contract fuzzing framework
5. **AlphaFuzz** (2021): MCTS-guided fuzzing
6. **RLF** (2022): RL-guided fuzzer for transaction sequences
7. **Multi-Agent RL** (2025): HGAT + MARL for vulnerability detection

### Tools Referenced
- **mev-inspect-rs**: MEV detection and classification
- **Foundry/Anvil**: Simulation environment
- **REVM/Alloy**: High-performance EVM
- **Cryo**: Blockchain data extraction
- **cadCAD**: Economic simulation
- **web3-ethereum-defi**: Protocol integration

### Industry Data Sources
- Flashbots MEV data
- Dune Analytics MEV dashboards
- Immunefi vulnerability reports
- OWASP Smart Contract Top 10 (2025)
- Rekt.news exploit database

---

## 🚀 Getting Started

See [ADVERSARIAL_QUICKSTART.md](./ADVERSARIAL_QUICKSTART.md) for:
- Environment setup
- First adversarial test
- Example attack scenarios
- Custom strategy creation
- Integration with existing framework

---

**Status**: Research complete, design in progress, MVP implementation starting

**Next Steps**:
1. ✅ Complete research documentation
2. ⏳ Implement simulation environment
3. ⏳ Create strategy template system
4. ⏳ Integrate evolutionary search
5. ⏳ Build MVP with 3 attack strategies
6. ⏳ Test on Uniswap V2 fork

---

*This document will be updated as implementation progresses.*
