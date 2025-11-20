"""
Monte Carlo Tree Search (MCTS)

Tree search algorithm for finding optimal transaction sequences.
Particularly effective for discovering complex multi-step exploits.
"""

import math
import random
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class MCTSNode:
    """Node in the MCTS tree"""
    state: Any  # Environment state
    parent: Optional['MCTSNode'] = None
    action: Optional[Any] = None  # Action that led to this state
    children: List['MCTSNode'] = field(default_factory=list)
    visits: int = 0
    total_reward: Decimal = Decimal(0)
    untried_actions: List[Any] = field(default_factory=list)

    @property
    def average_reward(self) -> Decimal:
        """Calculate average reward"""
        if self.visits == 0:
            return Decimal(0)
        return self.total_reward / Decimal(self.visits)

    def uct_score(self, exploration_constant: float = 1.41) -> float:
        """
        Calculate UCT (Upper Confidence Bound for Trees) score

        UCT = average_reward + C * sqrt(ln(parent_visits) / visits)
        """
        if self.visits == 0:
            return float('inf')  # Unvisited nodes have max priority

        if self.parent is None or self.parent.visits == 0:
            return float(self.average_reward)

        exploitation = float(self.average_reward)
        exploration = exploration_constant * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )

        return exploitation + exploration


class MCTSSearch:
    """
    Monte Carlo Tree Search Algorithm

    MCTS explores the space of possible transaction sequences by:
    1. Selection: Navigate tree using UCT to balance exploration/exploitation
    2. Expansion: Add new child node for untried action
    3. Simulation: Rollout random actions to terminal state
    4. Backpropagation: Update rewards back up the tree

    This is particularly effective for:
    - Finding complex multi-step exploits
    - Discovering non-obvious transaction orderings
    - Handling large action spaces
    - Adaptive exploration based on promising paths

    Example:
        search = MCTSSearch(
            exploration_constant=1.41,
            num_simulations=1000
        )

        results = search.search(
            environment=env,
            agents=attacker_agents,
            num_simulations=10000
        )
    """

    def __init__(
        self,
        exploration_constant: float = 1.41,
        num_simulations: int = 1000,
        max_depth: int = 10,
        rollout_depth: int = 5
    ):
        """
        Initialize MCTS search

        Args:
            exploration_constant: UCT exploration parameter (higher = more exploration)
            num_simulations: Number of MCTS iterations
            max_depth: Maximum search depth
            rollout_depth: Depth of random rollouts
        """
        self.exploration_constant = exploration_constant
        self.num_simulations = num_simulations
        self.max_depth = max_depth
        self.rollout_depth = rollout_depth

        self.logger = logging.getLogger(__name__)

        # Search state
        self.root: Optional[MCTSNode] = None
        self.best_sequence: List[Any] = []
        self.best_reward: Decimal = Decimal(0)

    def search(
        self,
        environment: Any,
        agents: List[Any],
        num_simulations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run MCTS search

        Args:
            environment: Simulation environment
            agents: List of attacker agents (provide possible actions)
            num_simulations: Number of simulations (overrides init value)

        Returns:
            Dictionary with results:
                - strategies: List of discovered strategies
                - sequences: Best transaction sequences
                - metrics: Search metrics
        """
        num_sims = num_simulations or self.num_simulations
        self.logger.info(f"Starting MCTS search ({num_sims} simulations)...")

        # Initialize root node
        initial_state = environment.get_state()
        self.root = MCTSNode(
            state=initial_state,
            untried_actions=self._get_possible_actions(agents, initial_state)
        )

        # Run simulations
        for sim in range(num_sims):
            # Create snapshot for this simulation
            environment.snapshot(f"mcts_sim_{sim}")

            try:
                # MCTS steps
                node = self._select(self.root)
                if not self._is_terminal(node):
                    node = self._expand(node, environment)
                reward = self._simulate(node, environment, agents)
                self._backpropagate(node, reward)

            except Exception as e:
                self.logger.error(f"MCTS simulation failed: {e}")
                reward = Decimal(-1000)
                self._backpropagate(node, reward)

            finally:
                # Revert to root state
                environment.revert(f"mcts_sim_{sim}")

            # Log progress
            if (sim + 1) % 100 == 0:
                self.logger.info(
                    f"Simulation {sim + 1}/{num_sims}: "
                    f"Best reward={self.best_reward:,.2f}"
                )

        # Extract best sequence
        best_sequence = self._extract_best_sequence()

        # Compile results
        results = self._compile_results(best_sequence)

        self.logger.info(f"MCTS complete. Best reward: {self.best_reward:,.2f}")

        return results

    def _select(self, node: MCTSNode) -> MCTSNode:
        """
        Selection phase: traverse tree using UCT

        Navigate from root to a leaf node, choosing children with
        highest UCT score at each step.
        """
        current = node

        while current.children and not current.untried_actions:
            # All actions tried, select best child by UCT
            current = max(
                current.children,
                key=lambda child: child.uct_score(self.exploration_constant)
            )

            # Check depth limit
            depth = self._get_depth(current)
            if depth >= self.max_depth:
                break

        return current

    def _expand(self, node: MCTSNode, environment: Any) -> MCTSNode:
        """
        Expansion phase: add new child for untried action

        Args:
            node: Node to expand
            environment: Environment to execute action

        Returns:
            Newly created child node
        """
        if not node.untried_actions:
            return node

        # Select random untried action
        action = random.choice(node.untried_actions)
        node.untried_actions.remove(action)

        # Execute action
        result = environment.execute_action(action)

        if result.success:
            # Create child node
            new_state = environment.get_state()
            child = MCTSNode(
                state=new_state,
                parent=node,
                action=action,
                untried_actions=self._get_possible_actions([], new_state)
            )
            node.children.append(child)
            return child
        else:
            # Action failed, try another
            if node.untried_actions:
                return self._expand(node, environment)
            return node

    def _simulate(
        self,
        node: MCTSNode,
        environment: Any,
        agents: List[Any]
    ) -> Decimal:
        """
        Simulation phase: random rollout from node

        Execute random actions until terminal state or max depth,
        return cumulative reward.

        Args:
            node: Starting node
            environment: Environment
            agents: List of agents (for action generation)

        Returns:
            Total reward from simulation
        """
        state = node.state
        total_reward = Decimal(0)

        for _ in range(self.rollout_depth):
            # Get possible actions
            possible_actions = self._get_possible_actions(agents, state)

            if not possible_actions:
                break

            # Select random action
            action = random.choice(possible_actions)

            # Execute
            result = environment.execute_action(action)

            if result.success:
                total_reward += result.profit
                state = environment.get_state()
            else:
                # Failed action, small penalty
                total_reward -= Decimal(100)
                break

        return total_reward

    def _backpropagate(self, node: MCTSNode, reward: Decimal):
        """
        Backpropagation phase: update statistics up the tree

        Args:
            node: Leaf node where simulation started
            reward: Reward from simulation
        """
        current = node

        while current is not None:
            current.visits += 1
            current.total_reward += reward
            current = current.parent

        # Track best reward
        if reward > self.best_reward:
            self.best_reward = reward
            self.best_sequence = self._get_node_sequence(node)

    def _get_possible_actions(self, agents: List[Any], state: Any) -> List[Any]:
        """
        Get list of possible actions from current state

        Args:
            agents: List of attacker agents
            state: Current environment state

        Returns:
            List of possible actions
        """
        actions = []

        # In full implementation, this would:
        # 1. Query each agent for possible actions
        # 2. Generate actions based on current state
        # 3. Filter invalid actions

        # For MVP, return simplified action set
        from ..simulation.evm_environment import Action, ActionType

        # Possible actions: swaps, borrows, liquidations
        action_templates = [
            Action(ActionType.SWAP, {'pool': 'uniswap', 'amount': 1000}),
            Action(ActionType.BORROW, {'protocol': 'aave', 'amount': 5000}),
            Action(ActionType.FLASH_LOAN, {'protocol': 'balancer', 'amount': 100000}),
        ]

        return action_templates

    def _is_terminal(self, node: MCTSNode) -> bool:
        """Check if node is terminal (no more actions possible)"""
        depth = self._get_depth(node)
        return depth >= self.max_depth or not node.untried_actions

    def _get_depth(self, node: MCTSNode) -> int:
        """Get depth of node in tree"""
        depth = 0
        current = node
        while current.parent is not None:
            depth += 1
            current = current.parent
        return depth

    def _get_node_sequence(self, node: MCTSNode) -> List[Any]:
        """Get sequence of actions from root to node"""
        sequence = []
        current = node

        while current.parent is not None:
            if current.action:
                sequence.append(current.action)
            current = current.parent

        sequence.reverse()
        return sequence

    def _extract_best_sequence(self) -> List[Any]:
        """Extract best action sequence from tree"""
        if not self.root or not self.root.children:
            return []

        # Follow path of highest average reward
        sequence = []
        current = self.root

        while current.children:
            # Select child with highest average reward
            best_child = max(
                current.children,
                key=lambda child: child.average_reward
            )

            if best_child.action:
                sequence.append(best_child.action)

            current = best_child

        return sequence

    def _compile_results(self, best_sequence: List[Any]) -> Dict[str, Any]:
        """Compile search results"""
        strategies = []

        if self.best_reward > 0:
            strategies.append({
                'type': 'mcts_discovered',
                'profit': float(self.best_reward),
                'success': True,
                'fitness': float(self.best_reward),
                'transactions': best_sequence,
                'sequence': best_sequence,
            })

        return {
            'strategies': strategies,
            'sequences': [best_sequence] if best_sequence else [],
            'metrics': {
                'num_simulations': self.num_simulations,
                'best_reward': float(self.best_reward),
                'tree_depth': self._get_max_depth(),
                'num_nodes': self._count_nodes(),
            }
        }

    def _get_max_depth(self) -> int:
        """Get maximum depth of search tree"""
        if not self.root:
            return 0

        def max_depth_recursive(node: MCTSNode) -> int:
            if not node.children:
                return 0
            return 1 + max(max_depth_recursive(child) for child in node.children)

        return max_depth_recursive(self.root)

    def _count_nodes(self) -> int:
        """Count total nodes in tree"""
        if not self.root:
            return 0

        def count_recursive(node: MCTSNode) -> int:
            return 1 + sum(count_recursive(child) for child in node.children)

        return count_recursive(self.root)

    def search_from_strategy(
        self,
        strategy: Any,
        environment: Any,
        num_simulations: int = 100
    ) -> Dict[str, Any]:
        """
        Search from a specific strategy

        Used by hybrid search to refine promising strategies found by
        evolutionary search.

        Args:
            strategy: Starting strategy
            environment: Environment
            num_simulations: Number of simulations

        Returns:
            Search results
        """
        self.logger.info(f"MCTS refinement of {strategy.name}...")

        # Execute initial strategy
        result = strategy.execute(environment)

        if not result.success:
            return {'strategies': [], 'sequences': [], 'metrics': {}}

        # Use MCTS to explore variations
        # For MVP, just return the strategy result
        return {
            'strategies': [{
                'type': strategy.category,
                'profit': float(result.profit),
                'success': True,
                'fitness': float(result.profit),
                'transactions': result.transactions,
                'sequence': []
            }],
            'sequences': [result.transactions],
            'metrics': {
                'num_simulations': num_simulations,
                'best_reward': float(result.profit)
            }
        }
