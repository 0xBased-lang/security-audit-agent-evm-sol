"""
Sandwich Attack Strategy

Classic MEV sandwich: front-run victim tx, victim executes, back-run to profit.

This is one of the most common MEV strategies, accounting for $289.76M in
losses in 2024 alone.
"""

from typing import List, Any
from decimal import Decimal
from .base import StrategyTemplate
from ..simulation.evm_environment import Action, ActionType


class SandwichAttack(StrategyTemplate):
    """
    Sandwich Attack Strategy

    Process:
    1. Detect victim transaction in mempool (large swap on DEX)
    2. Front-run: Execute same-direction swap before victim
    3. Victim transaction executes (at worse price due to front-run)
    4. Back-run: Reverse the swap to capture profit

    Parameters:
    - pool: Target DEX pool address
    - token_in: Input token
    - token_out: Output token
    - front_run_amount: Amount to front-run with (evolved)
    - gas_price_multiplier: Gas price increase for front-run (evolved)
    - min_victim_size: Minimum victim tx size to target (evolved)
    - max_price_impact: Maximum acceptable price impact (evolved)

    Example:
        Victim wants to swap 100 ETH -> USDC on Uniswap
        1. Attacker front-runs: 50 ETH -> USDC (price moves up)
        2. Victim executes: 100 ETH -> USDC (at worse price)
        3. Attacker back-runs: USDC -> ETH (price moves down, profit captured)

    Typical profit: 0.1% - 5% of victim transaction size
    """

    def __init__(
        self,
        pool: str = None,
        token_in: str = 'WETH',
        token_out: str = 'USDC',
        front_run_amount: float = 10.0,
        gas_price_multiplier: float = 1.5,
        min_victim_size: float = 5.0,
        max_price_impact: float = 0.05
    ):
        super().__init__(
            name='sandwich',
            category='mev',
            parameters={
                'pool': pool,
                'token_in': token_in,
                'token_out': token_out,
                'front_run_amount': front_run_amount,
                'gas_price_multiplier': gas_price_multiplier,
                'min_victim_size': min_victim_size,
                'max_price_impact': max_price_impact,
            },
            description=(
                "Sandwich attack: front-run + victim tx + back-run. "
                "Exploits price impact of large swaps on AMMs."
            ),
            tags=['mev', 'amm', 'sandwich', 'high-frequency']
        )

    def generate_transactions(self, env_state: Any) -> List[Action]:
        """
        Generate sandwich attack transaction sequence

        Returns:
            [front_run_swap, back_run_swap]

        Note: In full implementation, victim tx would be detected from mempool
        """
        pool = self.parameters['pool']
        token_in = self.parameters['token_in']
        token_out = self.parameters['token_out']
        amount = self.parameters['front_run_amount']

        # Transaction 1: Front-run (same direction as victim)
        front_run = Action(
            action_type=ActionType.SWAP,
            parameters={
                'pool': pool,
                'token_in': token_in,
                'token_out': token_out,
                'amount_in': amount,
                'min_amount_out': 0,  # No slippage protection (MEV bot)
                'gas_price_multiplier': self.parameters['gas_price_multiplier']
            }
        )

        # Transaction 2: Back-run (reverse direction)
        # Amount calculated based on front-run result
        back_run = Action(
            action_type=ActionType.SWAP,
            parameters={
                'pool': pool,
                'token_in': token_out,
                'token_out': token_in,
                'amount_in': 'calculated_from_front_run',  # Dynamic
                'min_amount_out': 0,
                'gas_price_multiplier': 1.0  # Normal gas for back-run
            }
        )

        return [front_run, back_run]

    def check_preconditions(self, env_state: Any) -> bool:
        """
        Check if sandwich attack is viable

        Conditions:
        - Pool must have sufficient liquidity
        - Victim transaction must be large enough
        - Price impact must be within acceptable range
        - Gas costs must not exceed potential profit
        """
        pool = self.parameters['pool']

        if not pool:
            return False

        # Check pool liquidity (simplified)
        if pool in env_state.pool_reserves:
            reserves = env_state.pool_reserves[pool]
            min_liquidity = self.parameters['front_run_amount'] * 100
            if reserves.get(self.parameters['token_in'], 0) < min_liquidity:
                return False

        # In full implementation:
        # - Check mempool for victim transactions
        # - Calculate expected price impact
        # - Verify gas costs are acceptable
        # - Check for MEV competition

        return True

    def check_victim_transaction(self, victim_tx: Dict[str, Any]) -> bool:
        """
        Check if victim transaction is profitable to sandwich

        Args:
            victim_tx: Victim transaction data

        Returns:
            True if victim tx is good target
        """
        min_size = self.parameters['min_victim_size']
        victim_amount = victim_tx.get('amount', 0)

        if victim_amount < min_size:
            return False

        # Check if same pool and tokens
        if victim_tx.get('pool') != self.parameters['pool']:
            return False

        # Calculate expected profit
        expected_profit = self._estimate_sandwich_profit(victim_amount)
        estimated_gas_cost = self._estimate_gas_cost()

        return expected_profit > estimated_gas_cost * 2  # 2x gas cost threshold

    def calculate_profit(self, initial_state: Any, final_state: Any) -> Decimal:
        """
        Calculate profit from sandwich attack

        Profit = (final_balance - initial_balance) - gas_costs
        """
        token_in = self.parameters['token_in']

        # Get balance change for the input token
        initial_balance = initial_state.balances.get(
            initial_state.block_number,  # Placeholder account
            {}
        ).get(token_in, 0)

        final_balance = final_state.balances.get(
            final_state.block_number,
            {}
        ).get(token_in, 0)

        balance_change = Decimal(final_balance - initial_balance) / Decimal(10**18)

        # Subtract gas costs
        gas_cost_eth = Decimal(final_state.total_gas_used) * Decimal(50) / Decimal(10**9)
        eth_price = Decimal(2000)  # Simplified

        profit_usd = (balance_change * eth_price) - (gas_cost_eth * eth_price)

        return profit_usd

    def _estimate_sandwich_profit(self, victim_amount: float) -> Decimal:
        """
        Estimate sandwich profit for a victim transaction

        Simplified calculation:
        - Profit is roughly proportional to price impact^2
        - Price impact = victim_amount / liquidity
        """
        front_run_amount = self.parameters['front_run_amount']
        price_impact = self.parameters.get('max_price_impact', 0.05)

        # Simplified profit model
        # Real implementation would use constant product formula
        estimated_profit_pct = price_impact * 0.5  # 50% of price impact
        estimated_profit = victim_amount * estimated_profit_pct

        return Decimal(estimated_profit)

    def _estimate_gas_cost(self) -> Decimal:
        """Estimate gas cost for sandwich attack"""
        gas_per_swap = 150000  # ~150k gas per Uniswap swap
        gas_price = 50  # 50 gwei
        eth_price = 2000

        total_gas = gas_per_swap * 2  # front-run + back-run
        gas_cost_eth = Decimal(total_gas * gas_price) / Decimal(10**9)
        gas_cost_usd = gas_cost_eth * Decimal(eth_price)

        return gas_cost_usd

    def get_optimal_parameters(self, victim_amount: float, pool_liquidity: float) -> Dict[str, Any]:
        """
        Calculate optimal parameters for a given victim transaction

        Args:
            victim_amount: Size of victim transaction
            pool_liquidity: Current pool liquidity

        Returns:
            Optimal strategy parameters
        """
        # Optimal front-run amount is typically 30-50% of victim amount
        optimal_front_run = victim_amount * 0.4

        # Adjust based on liquidity
        if optimal_front_run > pool_liquidity * 0.1:
            optimal_front_run = pool_liquidity * 0.1

        # Gas price multiplier based on competition
        gas_multiplier = 1.5  # Default, would be dynamic based on mempool

        return {
            **self.parameters,
            'front_run_amount': optimal_front_run,
            'gas_price_multiplier': gas_multiplier
        }
