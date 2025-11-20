"""
Attacker Agents

Agents that attempt to exploit protocols for testing purposes.
"""

from typing import Any, Dict, Optional
import random
from .base_agent import BaseAgent
from ..strategies.sandwich import SandwichAttack
from ..strategies.oracle_manipulation import OracleManipulation
from ..strategies.flash_loan import FlashLoanAttack


class AttackerAgent(BaseAgent):
    """
    Attacker Agent

    An agent that attempts to exploit a protocol using a specific strategy.

    Each attacker agent specializes in one attack type (sandwich, oracle
    manipulation, flash loan, etc.) and tries to maximize profit through
    parameter optimization.

    Example:
        agent = AttackerAgent(
            agent_id='sandwich_bot_1',
            strategy=SandwichAttack(),
            environment=env
        )

        # Run attack
        observations = agent.perceive(env.get_state())
        action = agent.decide(observations)
        result = agent.act(action)
    """

    def __init__(
        self,
        agent_id: str,
        strategy: Any,
        environment: Optional[Any] = None,
        aggression: float = 0.5
    ):
        """
        Initialize attacker agent

        Args:
            agent_id: Unique identifier
            strategy: Attack strategy template
            environment: Simulation environment
            aggression: How aggressive (0=conservative, 1=very aggressive)
        """
        super().__init__(
            agent_id=agent_id,
            agent_type='attacker',
            environment=environment
        )

        self.strategy = strategy
        self.aggression = aggression

        # Attacker-specific state
        self.successful_attacks: int = 0
        self.failed_attacks: int = 0

    def perceive(self, state: Any) -> Dict[str, Any]:
        """
        Perceive the environment to identify opportunities

        Args:
            state: Current environment state

        Returns:
            Observations including opportunities, risks, etc.
        """
        observations = {
            'state': state,
            'opportunities': [],
            'risks': [],
            'optimal_parameters': {}
        }

        # Check if strategy preconditions are met
        if self.strategy.check_preconditions(state):
            observations['opportunities'].append({
                'type': self.strategy.category,
                'strategy': self.strategy.name,
                'viable': True
            })

        # Analyze current market conditions
        observations['market_conditions'] = self._analyze_market(state)

        return observations

    def decide(self, observations: Dict[str, Any]) -> Any:
        """
        Decide whether and how to attack

        Args:
            observations: Observations from perceive()

        Returns:
            Action (strategy execution) or None
        """
        # Check if there are opportunities
        if not observations['opportunities']:
            return None

        # Adjust strategy parameters based on observations
        self._adjust_strategy_parameters(observations)

        # Decide whether to attack based on aggression level
        if random.random() < self.aggression:
            return self.strategy
        else:
            # Conservative: only attack if highly profitable
            estimated_profit = self._estimate_profit(observations)
            if estimated_profit > 1000:  # $1000 threshold
                return self.strategy

        return None

    def act(self, action: Any) -> Any:
        """
        Execute the attack

        Args:
            action: Strategy to execute

        Returns:
            Result of the attack
        """
        if action is None:
            return None

        if not self.environment:
            raise ValueError("Agent has no environment to act in")

        # Execute strategy
        self.logger.info(f"Executing {action.name} attack...")
        result = action.execute(self.environment)

        # Update statistics
        if result.success:
            self.successful_attacks += 1
            self.logger.info(f"✓ Attack successful: ${result.profit:,.2f} profit")
        else:
            self.failed_attacks += 1
            self.logger.debug(f"✗ Attack failed: {result.error}")

        # Record action
        self.action_history.append(result)
        self.update_metrics(result)

        return result

    def learn(self, experience: Dict[str, Any]):
        """
        Learn from attack results to improve future attacks

        Args:
            experience: Attack experience (state, action, result)
        """
        result = experience.get('result')

        if not result:
            return

        # If attack was successful, slightly mutate strategy for diversity
        if result.success and result.profit > 0:
            # Keep successful parameters
            self.knowledge_base['successful_parameters'] = (
                self.strategy.parameters.copy()
            )

        # If attack failed, try different parameters
        elif not result.success:
            # Mutate strategy to try something different
            self.strategy = self.strategy.mutate(mutation_rate=0.2)

    def _analyze_market(self, state: Any) -> Dict[str, Any]:
        """Analyze market conditions"""
        return {
            'volatility': 'normal',  # Placeholder
            'liquidity': 'sufficient',  # Placeholder
            'competition': 'moderate',  # Placeholder
        }

    def _adjust_strategy_parameters(self, observations: Dict[str, Any]):
        """Adjust strategy parameters based on observations"""
        # Placeholder: in full implementation, this would optimize parameters
        # based on current market conditions
        pass

    def _estimate_profit(self, observations: Dict[str, Any]) -> float:
        """Estimate potential profit from attack"""
        # Placeholder: in full implementation, this would calculate
        # expected profit based on current state
        return random.uniform(0, 10000)

    def get_success_rate(self) -> float:
        """Get attack success rate"""
        total = self.successful_attacks + self.failed_attacks
        if total == 0:
            return 0.0
        return self.successful_attacks / total


class AttackerAgentFactory:
    """
    Factory for creating attacker agents

    Simplifies creation of agents for different attack types.

    Example:
        factory = AttackerAgentFactory()

        sandwich_agent = factory.create_agent(
            strategy_type='sandwich',
            environment=env
        )

        oracle_agent = factory.create_agent(
            strategy_type='oracle_manipulation',
            environment=env
        )
    """

    def __init__(self):
        self.agent_counter = 0

    def create_agent(
        self,
        strategy_type: str,
        environment: Optional[Any] = None,
        aggression: float = 0.5,
        **strategy_kwargs
    ) -> AttackerAgent:
        """
        Create an attacker agent

        Args:
            strategy_type: Type of attack strategy
            environment: Simulation environment
            aggression: Aggression level (0-1)
            **strategy_kwargs: Additional strategy parameters

        Returns:
            AttackerAgent instance
        """
        self.agent_counter += 1
        agent_id = f"{strategy_type}_agent_{self.agent_counter}"

        # Create strategy based on type
        if strategy_type == 'sandwich':
            strategy = SandwichAttack(**strategy_kwargs)
        elif strategy_type == 'oracle_manipulation':
            strategy = OracleManipulation(**strategy_kwargs)
        elif strategy_type == 'flash_loan':
            strategy = FlashLoanAttack(**strategy_kwargs)
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        # Create agent
        agent = AttackerAgent(
            agent_id=agent_id,
            strategy=strategy,
            environment=environment,
            aggression=aggression
        )

        return agent

    def create_agent_swarm(
        self,
        strategy_types: list[str],
        environment: Optional[Any] = None,
        swarm_size: int = 10
    ) -> list[AttackerAgent]:
        """
        Create a swarm of attacker agents

        Args:
            strategy_types: List of strategy types
            environment: Simulation environment
            swarm_size: Number of agents per strategy type

        Returns:
            List of attacker agents
        """
        agents = []

        for strategy_type in strategy_types:
            for i in range(swarm_size):
                # Vary aggression levels
                aggression = random.uniform(0.3, 0.9)

                agent = self.create_agent(
                    strategy_type=strategy_type,
                    environment=environment,
                    aggression=aggression
                )

                agents.append(agent)

        return agents
