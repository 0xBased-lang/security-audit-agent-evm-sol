"""
Adversarial Testing Orchestrator

Main coordinator for adversarial agent-based security testing.
Manages simulation environments, agent coordination, and result analysis.
"""

from typing import List, Dict, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum

from .simulation.evm_environment import EVMEnvironment
from .simulation.solana_environment import SolanaEnvironment
from .agents.attacker_agents import AttackerAgentFactory
from .agents.defender_agent import DefenderAgent
from .agents.meta_agent import MetaAgent
from .search.evolutionary import EvolutionarySearch
from .search.mcts import MCTSSearch
from .search.drl import DRLSearch


class SearchAlgorithm(Enum):
    EVOLUTIONARY = "evolutionary"
    MCTS = "mcts"
    DRL = "drl"
    HYBRID = "hybrid"


@dataclass
class AdversarialTestConfig:
    """Configuration for adversarial testing"""
    chain: str  # 'evm' or 'solana'
    project_path: str
    fork_block: Optional[int] = None
    strategies: List[str] = None
    search_algorithm: str = "evolutionary"
    max_iterations: int = 1000
    population_size: int = 100
    parallel_agents: int = 4
    use_historical_mev: bool = True
    ai_orchestration: bool = True


@dataclass
class AdversarialTestResults:
    """Results from adversarial testing"""
    vulnerabilities: List[Dict[str, Any]]
    invariants_violated: List[str]
    max_exploit_profit: float
    successful_strategies: List[Dict[str, Any]]
    attack_sequences: List[List[Any]]
    metrics: Dict[str, Any]
    recommendations: List[str]


class AdversarialOrchestrator:
    """
    Main orchestrator for adversarial agent-based security testing

    This class coordinates:
    - Simulation environment setup
    - Multiple attacker agents
    - Defender agent
    - Meta-agent (Claude AI)
    - Search algorithms
    - Result analysis
    """

    def __init__(self, config: AdversarialTestConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.environment = self._setup_environment()
        self.attacker_agents = []
        self.defender_agent = None
        self.meta_agent = None
        self.search_engine = None

        self.logger.info(f"Adversarial orchestrator initialized for {config.chain}")

    def _setup_environment(self):
        """Setup blockchain simulation environment"""
        if self.config.chain == 'evm':
            return EVMEnvironment(
                project_path=self.config.project_path,
                fork_block=self.config.fork_block
            )
        elif self.config.chain == 'solana':
            return SolanaEnvironment(
                project_path=self.config.project_path
            )
        else:
            raise ValueError(f"Unsupported chain: {self.config.chain}")

    def run_adversarial_test(self) -> AdversarialTestResults:
        """
        Main entry point for adversarial testing

        Process:
        1. Setup agents and search engine
        2. Initialize strategies
        3. Run search algorithm
        4. Evaluate results
        5. Generate recommendations
        """

        self.logger.info("Starting adversarial security testing...")

        # Step 1: Setup
        self._initialize_agents()
        self._initialize_search_engine()

        # Step 2: Load historical MEV data if enabled
        if self.config.use_historical_mev:
            self._load_historical_patterns()

        # Step 3: Run search
        vulnerabilities = []
        successful_strategies = []

        self.logger.info(f"Running {self.config.search_algorithm} search...")

        if self.config.search_algorithm == "evolutionary":
            results = self._run_evolutionary_search()
        elif self.config.search_algorithm == "mcts":
            results = self._run_mcts_search()
        elif self.config.search_algorithm == "drl":
            results = self._run_drl_search()
        else:
            results = self._run_hybrid_search()

        # Step 4: Analyze results
        vulnerabilities = self._analyze_results(results)

        # Step 5: Defender analysis
        recommendations = self._get_defender_recommendations(vulnerabilities)

        # Step 6: Meta-agent synthesis
        if self.config.ai_orchestration:
            meta_analysis = self._run_meta_agent_analysis(vulnerabilities)
            recommendations.extend(meta_analysis['recommendations'])

        # Compile final results
        return AdversarialTestResults(
            vulnerabilities=vulnerabilities,
            invariants_violated=[v['invariant'] for v in vulnerabilities if 'invariant' in v],
            max_exploit_profit=max([v.get('profit', 0) for v in vulnerabilities], default=0),
            successful_strategies=[s for s in results['strategies'] if s['success']],
            attack_sequences=results['sequences'],
            metrics=results['metrics'],
            recommendations=recommendations
        )

    def _initialize_agents(self):
        """Initialize attacker and defender agents"""
        self.logger.info("Initializing agents...")

        # Create attacker agents for each strategy
        factory = AttackerAgentFactory()
        strategies = self.config.strategies or ['sandwich', 'oracle_manipulation', 'flash_loan']

        for strategy_type in strategies:
            agent = factory.create_agent(
                strategy_type=strategy_type,
                environment=self.environment
            )
            self.attacker_agents.append(agent)
            self.logger.info(f"Created {strategy_type} attacker agent")

        # Create defender agent
        self.defender_agent = DefenderAgent(
            environment=self.environment,
            protocol_config=self._load_protocol_config()
        )

        # Create meta-agent if AI orchestration enabled
        if self.config.ai_orchestration:
            self.meta_agent = MetaAgent(
                model='claude-sonnet-4-5',
                attacker_agents=self.attacker_agents,
                defender_agent=self.defender_agent
            )

    def _initialize_search_engine(self):
        """Initialize search algorithm"""
        algorithm = self.config.search_algorithm

        if algorithm == "evolutionary":
            self.search_engine = EvolutionarySearch(
                population_size=self.config.population_size,
                mutation_rate=0.1,
                crossover_rate=0.7
            )
        elif algorithm == "mcts":
            self.search_engine = MCTSSearch(
                exploration_constant=1.41,
                num_simulations=self.config.max_iterations
            )
        elif algorithm == "drl":
            self.search_engine = DRLSearch(
                algorithm='PPO',
                episodes=self.config.max_iterations
            )
        else:
            # Hybrid approach
            self.search_engine = self._create_hybrid_search()

    def _run_evolutionary_search(self):
        """Run evolutionary algorithm search"""
        self.logger.info("Starting evolutionary search...")

        results = self.search_engine.evolve(
            environment=self.environment,
            agents=self.attacker_agents,
            iterations=self.config.max_iterations,
            parallel=self.config.parallel_agents
        )

        return results

    def _run_mcts_search(self):
        """Run Monte Carlo Tree Search"""
        self.logger.info("Starting MCTS search...")

        results = self.search_engine.search(
            environment=self.environment,
            agents=self.attacker_agents,
            num_simulations=self.config.max_iterations
        )

        return results

    def _run_drl_search(self):
        """Run Deep Reinforcement Learning search"""
        self.logger.info("Starting DRL training...")

        results = self.search_engine.train(
            environment=self.environment,
            agents=self.attacker_agents,
            episodes=self.config.max_iterations
        )

        return results

    def _run_hybrid_search(self):
        """Run hybrid multi-algorithm search"""
        self.logger.info("Starting hybrid search...")

        # Combine multiple search strategies
        # 1. Evolutionary for initial exploration
        # 2. MCTS for promising paths
        # 3. DRL for refinement

        results = {
            'strategies': [],
            'sequences': [],
            'metrics': {}
        }

        # Phase 1: Evolutionary (50% of iterations)
        evo_results = EvolutionarySearch().evolve(
            environment=self.environment,
            agents=self.attacker_agents,
            iterations=self.config.max_iterations // 2
        )
        results['strategies'].extend(evo_results['strategies'])

        # Phase 2: MCTS on top strategies (30% of iterations)
        top_strategies = sorted(
            evo_results['strategies'],
            key=lambda s: s['fitness'],
            reverse=True
        )[:10]

        for strategy in top_strategies:
            mcts_results = MCTSSearch().search_from_strategy(
                strategy=strategy,
                environment=self.environment,
                num_simulations=self.config.max_iterations // 10
            )
            results['sequences'].extend(mcts_results['sequences'])

        # Phase 3: DRL refinement (20% of iterations)
        drl_results = DRLSearch().refine(
            initial_strategies=results['strategies'],
            environment=self.environment,
            episodes=self.config.max_iterations // 5
        )
        results['strategies'].extend(drl_results['strategies'])

        return results

    def _load_historical_patterns(self):
        """Load historical MEV patterns from mev-inspect-rs data"""
        self.logger.info("Loading historical MEV patterns...")

        # This would integrate with mev-inspect-rs
        # For now, placeholder
        pass

    def _analyze_results(self, search_results):
        """Analyze search results to identify vulnerabilities"""
        vulnerabilities = []

        for strategy in search_results['strategies']:
            if strategy.get('success') and strategy.get('profit', 0) > 0:
                vulnerability = {
                    'type': strategy['type'],
                    'profit': strategy['profit'],
                    'gas_cost': strategy.get('gas_used', 0),
                    'transactions': strategy['transactions'],
                    'invariant': strategy.get('invariant_violated'),
                    'severity': self._calculate_severity(strategy),
                    'description': self._generate_description(strategy),
                    'exploit_sequence': strategy.get('sequence', [])
                }
                vulnerabilities.append(vulnerability)

        return vulnerabilities

    def _calculate_severity(self, strategy):
        """Calculate vulnerability severity"""
        profit = strategy.get('profit', 0)
        invariant = strategy.get('invariant_violated')

        if invariant and invariant.get('severity') == 'CRITICAL':
            return 'CRITICAL'
        elif profit > 100000:  # > $100k
            return 'HIGH'
        elif profit > 10000:   # > $10k
            return 'MEDIUM'
        else:
            return 'LOW'

    def _generate_description(self, strategy):
        """Generate human-readable description of exploit"""
        return f"{strategy['type']} exploit generating ${strategy.get('profit', 0):.2f} profit"

    def _get_defender_recommendations(self, vulnerabilities):
        """Get recommendations from defender agent"""
        if not self.defender_agent:
            return []

        return self.defender_agent.generate_recommendations(vulnerabilities)

    def _run_meta_agent_analysis(self, vulnerabilities):
        """Run AI meta-agent for synthesis and novel insights"""
        if not self.meta_agent:
            return {'recommendations': []}

        return self.meta_agent.analyze_and_recommend(vulnerabilities)

    def _load_protocol_config(self):
        """Load protocol-specific configuration"""
        # Placeholder
        return {}

    def _create_hybrid_search(self):
        """Create hybrid search engine"""
        # Placeholder
        return None


# Convenience function
def run_adversarial_test(
    chain: str,
    project_path: str,
    **kwargs
) -> AdversarialTestResults:
    """
    Convenience function to run adversarial test

    Usage:
        results = run_adversarial_test(
            chain='evm',
            project_path='./contracts',
            strategies=['sandwich', 'oracle_manipulation'],
            max_iterations=1000
        )
    """
    config = AdversarialTestConfig(
        chain=chain,
        project_path=project_path,
        **kwargs
    )

    orchestrator = AdversarialOrchestrator(config)
    return orchestrator.run_adversarial_test()
