"""
Flash Loan Attack Strategy

Generalized flash loan exploit pattern for discovering composability bugs.

Flash loans enable attackers to borrow massive capital (millions of dollars)
without collateral, execute complex attack sequences, and repay within a
single transaction. This enables economic exploits that would otherwise
require significant capital.
"""

from typing import List, Any, Dict
from decimal import Decimal
from .base import StrategyTemplate
from ..simulation.evm_environment import Action, ActionType


class FlashLoanAttack(StrategyTemplate):
    """
    Flash Loan Attack Strategy

    Generic flash loan attack template that can be composed with other
    strategies to discover complex exploit sequences.

    Attack Pattern:
    1. Flash loan token(s) from lending protocol
    2. Execute exploit sequence with borrowed capital
    3. Repay flash loan + fee
    4. Keep profit

    The exploit sequence (step 2) can include:
    - Multiple swaps across DEXes (arbitrage)
    - Oracle manipulation
    - Liquidations
    - Governance attacks
    - Reentrancy
    - Protocol-specific logic bugs

    Parameters:
    - flash_loan_protocol: Protocol to borrow from (Aave, Balancer, Uniswap V3)
    - flash_loan_tokens: List of tokens to borrow
    - flash_loan_amounts: Amounts to borrow for each token
    - exploit_sequence: List of actions to execute (evolved by search)
    - max_gas_price: Maximum gas price willing to pay
    - min_profit_threshold: Minimum profit to consider success

    Famous Examples:
    - bZx (2020): $954k via flash loan + oracle manipulation
    - Harvest Finance (2020): $34M via flash loan + AMM manipulation
    - Cream Finance (2021): $130M via flash loan + reentrancy
    - Euler Finance (2023): $197M via flash loan + donation attack

    Typical profit: Highly variable (0% to 1000%+ of flash loan)
    Risk: High complexity, must repay in single transaction
    """

    def __init__(
        self,
        flash_loan_protocol: str = 'balancer',  # Balancer has 0 fees
        flash_loan_tokens: List[str] = None,
        flash_loan_amounts: List[float] = None,
        exploit_sequence_type: str = 'arbitrage',  # or 'oracle', 'liquidation'
        target_protocols: List[str] = None,
        max_gas_price: float = 200,  # gwei
        min_profit_threshold: float = 1000  # $1000 minimum
    ):
        if flash_loan_tokens is None:
            flash_loan_tokens = ['USDC']
        if flash_loan_amounts is None:
            flash_loan_amounts = [1000000]  # 1M USDC
        if target_protocols is None:
            target_protocols = []

        super().__init__(
            name='flash_loan_attack',
            category='flash_loan',
            parameters={
                'flash_loan_protocol': flash_loan_protocol,
                'flash_loan_tokens': flash_loan_tokens,
                'flash_loan_amounts': flash_loan_amounts,
                'exploit_sequence_type': exploit_sequence_type,
                'target_protocols': target_protocols,
                'max_gas_price': max_gas_price,
                'min_profit_threshold': min_profit_threshold,
            },
            description=(
                "Flash loan attack: borrow massive capital -> execute exploit "
                "sequence -> repay loan -> profit"
            ),
            tags=['flash_loan', 'composability', 'complex', 'high_capital']
        )

        # Exploit sequences will be generated dynamically
        self.exploit_sequence = []

    def generate_transactions(self, env_state: Any) -> List[Action]:
        """
        Generate flash loan attack transaction sequence

        Returns:
            [flash_loan_start, ...exploit_sequence..., flash_loan_repay]
        """
        params = self.parameters
        transactions = []

        # Step 1: Initiate flash loan(s)
        for token, amount in zip(params['flash_loan_tokens'], params['flash_loan_amounts']):
            flash_loan = Action(
                action_type=ActionType.FLASH_LOAN,
                parameters={
                    'protocol': params['flash_loan_protocol'],
                    'token': token,
                    'amount': amount,
                    'callback': 'execute_exploit_sequence'
                }
            )
            transactions.append(flash_loan)

        # Step 2: Generate exploit sequence based on type
        exploit_txs = self._generate_exploit_sequence(env_state)
        transactions.extend(exploit_txs)

        # Step 3: Repay flash loan(s)
        for token, amount in zip(params['flash_loan_tokens'], params['flash_loan_amounts']):
            fee = self._calculate_flash_loan_fee(params['flash_loan_protocol'], amount)
            repay = Action(
                action_type=ActionType.REPAY,
                parameters={
                    'protocol': params['flash_loan_protocol'],
                    'token': token,
                    'amount': amount + fee
                }
            )
            transactions.append(repay)

        return transactions

    def _generate_exploit_sequence(self, env_state: Any) -> List[Action]:
        """
        Generate the exploit sequence executed during flash loan

        This is where the actual exploit logic goes. Different sequence types:
        - arbitrage: Multi-DEX arbitrage
        - oracle: Oracle manipulation
        - liquidation: Liquidation cascades
        - governance: Governance attack
        - custom: Evolved by search algorithm
        """
        exploit_type = self.parameters['exploit_sequence_type']

        if exploit_type == 'arbitrage':
            return self._generate_arbitrage_sequence(env_state)
        elif exploit_type == 'oracle':
            return self._generate_oracle_manipulation_sequence(env_state)
        elif exploit_type == 'liquidation':
            return self._generate_liquidation_sequence(env_state)
        elif exploit_type == 'custom':
            return self._generate_custom_sequence(env_state)
        else:
            # Default: simple swap sequence
            return self._generate_simple_swap_sequence(env_state)

    def _generate_arbitrage_sequence(self, env_state: Any) -> List[Action]:
        """
        Generate arbitrage exploit sequence

        Pattern: Swap across multiple DEXes to exploit price differences
        Example: USDC -> ETH (Uniswap) -> USDC (Sushiswap) = profit
        """
        sequence = []

        token_in = self.parameters['flash_loan_tokens'][0]
        amount = self.parameters['flash_loan_amounts'][0]

        # Arbitrage path (simplified 3-hop)
        # In full implementation, this would be found by path-finding algorithm

        # Swap 1: USDC -> WETH on Uniswap
        sequence.append(Action(
            action_type=ActionType.SWAP,
            parameters={
                'pool': 'uniswap_v2_usdc_weth',
                'token_in': token_in,
                'token_out': 'WETH',
                'amount_in': amount,
                'min_amount_out': 0
            }
        ))

        # Swap 2: WETH -> DAI on Sushiswap
        sequence.append(Action(
            action_type=ActionType.SWAP,
            parameters={
                'pool': 'sushiswap_weth_dai',
                'token_in': 'WETH',
                'token_out': 'DAI',
                'amount_in': 'from_previous',
                'min_amount_out': 0
            }
        ))

        # Swap 3: DAI -> USDC on Curve
        sequence.append(Action(
            action_type=ActionType.SWAP,
            parameters={
                'pool': 'curve_3pool',
                'token_in': 'DAI',
                'token_out': token_in,
                'amount_in': 'from_previous',
                'min_amount_out': amount  # Must be profitable
            }
        ))

        return sequence

    def _generate_oracle_manipulation_sequence(self, env_state: Any) -> List[Action]:
        """
        Generate oracle manipulation sequence

        Pattern: Manipulate AMM price -> exploit protocol -> reverse
        """
        sequence = []

        token = self.parameters['flash_loan_tokens'][0]
        amount = self.parameters['flash_loan_amounts'][0]

        # Manipulate price by large swap
        sequence.append(Action(
            action_type=ActionType.SWAP,
            parameters={
                'pool': 'target_amm_pool',
                'token_in': token,
                'token_out': 'WETH',
                'amount_in': amount * 0.8,  # Use 80% for manipulation
                'min_amount_out': 0
            }
        ))

        # Exploit the manipulated price
        sequence.append(Action(
            action_type=ActionType.BORROW,
            parameters={
                'protocol': 'vulnerable_lending_protocol',
                'collateral': 'WETH',
                'collateral_amount': 'from_previous',
                'borrow_asset': 'USDC',
                'borrow_amount': 'max'  # Over-borrow with inflated collateral
            }
        ))

        # Reverse price manipulation
        sequence.append(Action(
            action_type=ActionType.SWAP,
            parameters={
                'pool': 'target_amm_pool',
                'token_in': 'WETH',
                'token_out': token,
                'amount_in': 'remaining_balance',
                'min_amount_out': 0
            }
        ))

        return sequence

    def _generate_liquidation_sequence(self, env_state: Any) -> List[Action]:
        """
        Generate liquidation exploit sequence

        Pattern: Use flash loan to trigger liquidation cascade
        """
        sequence = []

        # Liquidate underwater positions
        sequence.append(Action(
            action_type=ActionType.LIQUIDATE,
            parameters={
                'protocol': 'compound_v3',
                'borrower': 'target_borrower',
                'collateral': 'WETH',
                'debt': 'USDC',
                'liquidation_amount': 'max'
            }
        ))

        return sequence

    def _generate_custom_sequence(self, env_state: Any) -> List[Action]:
        """
        Generate custom exploit sequence

        This is evolved by the search algorithm to discover novel exploits
        """
        # Placeholder: in full implementation, this would be evolved
        return []

    def _generate_simple_swap_sequence(self, env_state: Any) -> List[Action]:
        """Generate simple swap sequence for testing"""
        token = self.parameters['flash_loan_tokens'][0]
        amount = self.parameters['flash_loan_amounts'][0]

        return [Action(
            action_type=ActionType.SWAP,
            parameters={
                'pool': 'uniswap_v2',
                'token_in': token,
                'token_out': 'WETH',
                'amount_in': amount,
                'min_amount_out': 0
            }
        )]

    def check_preconditions(self, env_state: Any) -> bool:
        """
        Check if flash loan attack is viable

        Conditions:
        - Flash loan must be available with sufficient liquidity
        - Exploit sequence must be profitable
        - Gas costs must be acceptable
        - All target protocols must be accessible
        """
        params = self.parameters

        # Check flash loan availability
        for token, amount in zip(params['flash_loan_tokens'], params['flash_loan_amounts']):
            if not self._is_flash_loan_available(token, amount, env_state):
                return False

        # Estimate profitability
        estimated_profit = self._estimate_profit(env_state)
        min_threshold = params['min_profit_threshold']

        if estimated_profit < min_threshold:
            return False

        return True

    def _is_flash_loan_available(self, token: str, amount: float, env_state: Any) -> bool:
        """Check if flash loan is available"""
        protocol = self.parameters['flash_loan_protocol']

        # In full implementation, query actual protocol liquidity
        # For now, assume available if amount is reasonable
        max_flash_loan = {
            'balancer': 100_000_000,  # 100M (Balancer vault has deep liquidity)
            'aave_v3': 50_000_000,     # 50M
            'uniswap_v3': 20_000_000,  # 20M
        }

        return amount <= max_flash_loan.get(protocol, 1_000_000)

    def _calculate_flash_loan_fee(self, protocol: str, amount: float) -> float:
        """Calculate flash loan fee"""
        fees = {
            'balancer': 0.0,      # Balancer: 0%
            'aave_v3': 0.0009,    # Aave: 0.09%
            'uniswap_v3': 0.0,    # Uniswap V3: 0% (paid in swap fees)
        }

        fee_rate = fees.get(protocol, 0.001)  # Default 0.1%
        return amount * fee_rate

    def _estimate_profit(self, env_state: Any) -> Decimal:
        """
        Estimate profit from flash loan attack

        Highly dependent on exploit type and market conditions
        """
        exploit_type = self.parameters['exploit_sequence_type']
        flash_loan_amount = sum(self.parameters['flash_loan_amounts'])

        # Rough estimates by exploit type
        profit_multipliers = {
            'arbitrage': 0.002,      # 0.2% typical arbitrage profit
            'oracle': 0.10,          # 10% oracle manipulation profit
            'liquidation': 0.05,     # 5% liquidation bonus
            'custom': 0.01,          # 1% for unknown exploits
        }

        multiplier = profit_multipliers.get(exploit_type, 0.01)
        estimated_profit = flash_loan_amount * multiplier

        # Subtract costs
        flash_loan_fee = sum(
            self._calculate_flash_loan_fee(
                self.parameters['flash_loan_protocol'],
                amount
            )
            for amount in self.parameters['flash_loan_amounts']
        )

        gas_cost = self._estimate_gas_cost()

        net_profit = estimated_profit - flash_loan_fee - gas_cost

        return Decimal(max(0, net_profit))

    def _estimate_gas_cost(self) -> float:
        """Estimate total gas cost"""
        # Flash loan attacks are gas-intensive
        # Typical: 500k - 2M gas
        estimated_gas = 1_000_000  # 1M gas
        gas_price_gwei = self.parameters['max_gas_price']
        eth_price = 2000

        gas_cost_eth = estimated_gas * gas_price_gwei / 10**9
        gas_cost_usd = gas_cost_eth * eth_price

        return gas_cost_usd

    def calculate_profit(self, initial_state: Any, final_state: Any) -> Decimal:
        """
        Calculate actual profit from flash loan attack

        Profit = (final balance - initial balance) - all costs
        """
        # Get token balance changes
        token = self.parameters['flash_loan_tokens'][0]

        # Simplified: use state's total value extracted
        profit = Decimal(
            final_state.total_value_extracted -
            initial_state.total_value_extracted
        )

        return profit

    def find_profitable_paths(self, env_state: Any, max_hops: int = 5) -> List[List[str]]:
        """
        Find profitable arbitrage paths

        Args:
            env_state: Current environment state
            max_hops: Maximum number of swaps in path

        Returns:
            List of token paths that may be profitable
        """
        # In full implementation, this would use graph search
        # to find arbitrage cycles across all DEXes

        # Example paths
        profitable_paths = [
            ['USDC', 'WETH', 'DAI', 'USDC'],
            ['USDC', 'WETH', 'WBTC', 'USDC'],
            ['DAI', 'USDC', 'USDT', 'DAI'],
        ]

        return profitable_paths
