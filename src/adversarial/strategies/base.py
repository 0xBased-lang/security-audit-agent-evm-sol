"""
Base Strategy Template

Abstract base class for all attack strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from decimal import Decimal
import logging


@dataclass
class StrategyResult:
    """Result of executing a strategy"""
    success: bool
    profit: Decimal
    gas_used: int
    transactions: List[Any]
    invariant_violated: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"StrategyResult({status}, profit=${self.profit:,.2f}, gas={self.gas_used:,})"


class StrategyTemplate(ABC):
    """
    Abstract base class for attack strategies

    Strategies are parameterized attack patterns that can be:
    - Evolved by search algorithms
    - Composed into sequences
    - Learned from historical data
    - Customized for specific protocols

    Example:
        class MyAttack(StrategyTemplate):
            def __init__(self):
                super().__init__(
                    name='my_attack',
                    category='custom',
                    parameters={
                        'target': None,
                        'amount': 100000,
                    }
                )

            def generate_transactions(self, env_state):
                return [...]

            def check_preconditions(self, env_state):
                return True

            def calculate_profit(self, initial, final):
                return final.balance - initial.balance
    """

    def __init__(
        self,
        name: str,
        category: str,
        parameters: Dict[str, Any],
        description: str = "",
        tags: List[str] = None
    ):
        """
        Initialize strategy template

        Args:
            name: Strategy name
            category: Category (sandwich, oracle, flash_loan, etc.)
            parameters: Strategy parameters (will be evolved)
            description: Human-readable description
            tags: Tags for categorization
        """
        self.name = name
        self.category = category
        self.parameters = parameters
        self.description = description
        self.tags = tags or []
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def generate_transactions(self, env_state: Any) -> List[Any]:
        """
        Generate transaction sequence for this strategy

        Args:
            env_state: Current environment state

        Returns:
            List of transactions to execute
        """
        pass

    @abstractmethod
    def check_preconditions(self, env_state: Any) -> bool:
        """
        Check if strategy can be executed in current state

        Args:
            env_state: Current environment state

        Returns:
            True if strategy can be executed
        """
        pass

    @abstractmethod
    def calculate_profit(self, initial_state: Any, final_state: Any) -> Decimal:
        """
        Calculate profit from strategy execution

        Args:
            initial_state: State before execution
            final_state: State after execution

        Returns:
            Profit in USD
        """
        pass

    def execute(self, environment: Any) -> StrategyResult:
        """
        Execute the strategy in an environment

        Args:
            environment: Simulation environment

        Returns:
            StrategyResult with execution details
        """
        # Check preconditions
        if not self.check_preconditions(environment.get_state()):
            return StrategyResult(
                success=False,
                profit=Decimal(0),
                gas_used=0,
                transactions=[],
                error="Preconditions not met"
            )

        # Save initial state
        initial_state = environment.get_state()
        environment.snapshot(f"strategy_{self.name}")

        transactions = []
        total_gas = 0

        try:
            # Generate transaction sequence
            tx_sequence = self.generate_transactions(initial_state)

            # Execute each transaction
            for tx in tx_sequence:
                result = environment.execute_action(tx)
                transactions.append({
                    'action': tx,
                    'result': result
                })
                total_gas += result.gas_used

                if not result.success:
                    # Revert on failure
                    environment.revert(f"strategy_{self.name}")
                    return StrategyResult(
                        success=False,
                        profit=Decimal(0),
                        gas_used=total_gas,
                        transactions=transactions,
                        error=f"Transaction failed: {result.error}"
                    )

            # Calculate profit
            final_state = environment.get_state()
            profit = self.calculate_profit(initial_state, final_state)

            # Check for invariant violations
            invariant_violated = None
            if transactions[-1]['result'].state_changes.get('invariant_violations'):
                invariant_violated = transactions[-1]['result'].state_changes['invariant_violations'][0]

            return StrategyResult(
                success=True,
                profit=profit,
                gas_used=total_gas,
                transactions=transactions,
                invariant_violated=invariant_violated,
                metadata={
                    'strategy': self.name,
                    'category': self.category,
                    'parameters': self.parameters
                }
            )

        except Exception as e:
            self.logger.error(f"Strategy execution failed: {e}")
            environment.revert(f"strategy_{self.name}")
            return StrategyResult(
                success=False,
                profit=Decimal(0),
                gas_used=total_gas,
                transactions=transactions,
                error=str(e)
            )

    def mutate(self, mutation_rate: float = 0.1) -> 'StrategyTemplate':
        """
        Create a mutated version of this strategy

        Used by evolutionary algorithms to explore parameter space.

        Args:
            mutation_rate: Probability of mutating each parameter

        Returns:
            Mutated strategy
        """
        import random
        import copy

        mutated = copy.deepcopy(self)

        for param_name, param_value in mutated.parameters.items():
            if random.random() < mutation_rate:
                # Mutate this parameter
                if isinstance(param_value, (int, float)):
                    # Numeric parameter: add random noise
                    noise_factor = random.uniform(0.8, 1.2)
                    mutated.parameters[param_name] = param_value * noise_factor
                elif isinstance(param_value, bool):
                    # Boolean: flip
                    mutated.parameters[param_name] = not param_value
                # Add more types as needed

        return mutated

    def crossover(self, other: 'StrategyTemplate') -> 'StrategyTemplate':
        """
        Create offspring strategy by crossing over with another

        Args:
            other: Another strategy to cross with

        Returns:
            Offspring strategy
        """
        import random
        import copy

        if self.category != other.category:
            # Can't crossover different strategy types
            return copy.deepcopy(self)

        offspring = copy.deepcopy(self)

        # For each parameter, randomly choose from self or other
        for param_name in offspring.parameters:
            if param_name in other.parameters:
                if random.random() < 0.5:
                    offspring.parameters[param_name] = other.parameters[param_name]

        return offspring

    def to_dict(self) -> Dict[str, Any]:
        """Convert strategy to dictionary"""
        return {
            'name': self.name,
            'category': self.category,
            'parameters': self.parameters,
            'description': self.description,
            'tags': self.tags
        }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, params={len(self.parameters)})"
