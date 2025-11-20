"""
Base Agent Class

Abstract base class for all agents in the adversarial framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging


class BaseAgent(ABC):
    """
    Base Agent

    All agents (attackers, defenders, meta-agent) inherit from this class.

    Agents have:
    - Knowledge: Information about the environment and protocols
    - Strategy: Approach to achieving their goal
    - Actions: Set of actions they can perform
    - Learning: Ability to improve over time
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        environment: Optional[Any] = None
    ):
        """
        Initialize base agent

        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type of agent (attacker, defender, meta)
            environment: Simulation environment (optional)
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.environment = environment
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

        # Agent state
        self.knowledge_base: Dict[str, Any] = {}
        self.action_history: List[Any] = []
        self.performance_metrics: Dict[str, float] = {
            'total_profit': 0.0,
            'success_rate': 0.0,
            'actions_taken': 0,
        }

    @abstractmethod
    def perceive(self, state: Any) -> Dict[str, Any]:
        """
        Perceive the current environment state

        Args:
            state: Current environment state

        Returns:
            Processed observations
        """
        pass

    @abstractmethod
    def decide(self, observations: Dict[str, Any]) -> Any:
        """
        Decide on an action based on observations

        Args:
            observations: Processed observations from perceive()

        Returns:
            Action to take
        """
        pass

    @abstractmethod
    def act(self, action: Any) -> Any:
        """
        Execute an action in the environment

        Args:
            action: Action to execute

        Returns:
            Result of the action
        """
        pass

    def learn(self, experience: Dict[str, Any]):
        """
        Learn from experience (optional, can be overridden)

        Args:
            experience: Experience tuple (state, action, reward, next_state)
        """
        # Default: no learning (can be overridden by subclasses)
        pass

    def update_metrics(self, result: Any):
        """
        Update performance metrics

        Args:
            result: Result from action execution
        """
        self.performance_metrics['actions_taken'] += 1

        if hasattr(result, 'success') and result.success:
            if hasattr(result, 'profit'):
                self.performance_metrics['total_profit'] += float(result.profit)

        # Update success rate
        if self.performance_metrics['actions_taken'] > 0:
            successes = sum(
                1 for action in self.action_history
                if hasattr(action, 'success') and action.success
            )
            self.performance_metrics['success_rate'] = (
                successes / self.performance_metrics['actions_taken']
            )

    def get_metrics(self) -> Dict[str, float]:
        """Get agent performance metrics"""
        return self.performance_metrics.copy()

    def reset(self):
        """Reset agent state"""
        self.action_history = []
        self.performance_metrics = {
            'total_profit': 0.0,
            'success_rate': 0.0,
            'actions_taken': 0,
        }

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.agent_id}, type={self.agent_type})"
