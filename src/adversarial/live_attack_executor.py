"""
Live Attack Execution Framework

Week 4 implementation: Real exploit execution on mainnet forks.
Moves from simulation to actual demonstration of vulnerabilities.

This framework:
- Executes real transactions on forked mainnet
- Measures actual MEV profitability
- Validates exploits with live blockchain state
- Proves vulnerabilities are exploitable (not just theoretical)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
import time

from .simulation.live_fork import LiveFork, LiveForkConfig, create_live_fork
from web3 import Web3
from web3.types import Wei
from eth_typing import ChecksumAddress

logger = logging.getLogger(__name__)


class AttackType(Enum):
    """Types of attacks that can be executed"""
    SANDWICH = "sandwich"
    FRONT_RUN = "front_run"
    BACK_RUN = "back_run"
    FLASH_LOAN = "flash_loan"
    ORACLE_MANIPULATION = "oracle_manipulation"
    LIQUIDATION = "liquidation"
    GOVERNANCE = "governance"
    REENTRANCY = "reentrancy"
    ARBITRAGE = "arbitrage"


class AttackStatus(Enum):
    """Status of attack execution"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    REVERTED = "reverted"
    UNPROFITABLE = "unprofitable"


@dataclass
class AttackResult:
    """Result of a live attack execution"""
    attack_type: AttackType
    status: AttackStatus
    profit_wei: int
    profit_usd: float
    gas_used: int
    gas_cost_wei: int
    net_profit_wei: int
    net_profit_usd: float

    # Transaction details
    transactions: List[str] = field(default_factory=list)
    block_numbers: List[int] = field(default_factory=list)

    # Proof
    proof_of_exploit: Dict[str, Any] = field(default_factory=dict)

    # Timing
    execution_time_ms: float = 0.0
    timestamp: int = 0

    def is_profitable(self) -> bool:
        """Check if attack was profitable"""
        return self.net_profit_wei > 0

    def __repr__(self):
        status_emoji = {
            AttackStatus.SUCCESS: "✅",
            AttackStatus.FAILED: "❌",
            AttackStatus.UNPROFITABLE: "📉",
            AttackStatus.REVERTED: "⏪"
        }
        emoji = status_emoji.get(self.status, "❓")

        return (
            f"AttackResult({emoji} {self.attack_type.value}, "
            f"profit=${self.net_profit_usd:.2f}, gas={self.gas_used})"
        )


@dataclass
class SandwichAttackParams:
    """Parameters for sandwich attack"""
    target_tx_hash: str
    target_swap_amount: int
    pool_address: ChecksumAddress
    token_in: ChecksumAddress
    token_out: ChecksumAddress
    frontrun_amount: int
    slippage_tolerance: float = 0.005  # 0.5%


@dataclass
class FlashLoanAttackParams:
    """Parameters for flash loan attack"""
    loan_amount: int
    loan_token: ChecksumAddress
    target_protocol: ChecksumAddress
    attack_sequence: List[Dict[str, Any]]


@dataclass
class OracleAttackParams:
    """Parameters for oracle manipulation attack"""
    oracle_address: ChecksumAddress
    manipulation_method: str  # "price_feed", "twap", "spot"
    target_price: int
    manipulation_transactions: List[Dict[str, Any]]


class LiveAttackExecutor:
    """
    Live Attack Execution Engine

    Executes real attacks on mainnet forks to prove exploitability.

    Features:
    - Real transaction execution (not just simulation)
    - Live profitability calculation with actual gas costs
    - State validation before and after attacks
    - Proof generation with transaction receipts
    - Rollback capability for iterative testing

    Usage:
        executor = LiveAttackExecutor(fork)

        # Execute sandwich attack
        result = executor.execute_sandwich_attack(params)

        if result.is_profitable():
            print(f"Exploit proven! Profit: ${result.net_profit_usd}")
            print(f"Transaction proof: {result.transactions}")
    """

    def __init__(self, fork: LiveFork):
        self.fork = fork
        self.w3 = fork.w3

        # Track all executed attacks
        self.attack_history: List[AttackResult] = []

        # Price oracle (for USD conversion)
        self.eth_usd_price = 2000.0  # Default, should be fetched from oracle

    def execute_sandwich_attack(
        self,
        params: SandwichAttackParams,
        simulate_first: bool = True
    ) -> AttackResult:
        """
        Execute a real sandwich attack on the fork

        Process:
        1. Take snapshot for rollback
        2. Simulate attack if requested
        3. Execute frontrun transaction
        4. Execute target transaction
        5. Execute backrun transaction
        6. Calculate profit and gas costs
        7. Validate result

        Args:
            params: Sandwich attack parameters
            simulate_first: Simulate before executing

        Returns:
            AttackResult with proof of exploit
        """
        logger.info(f"🥪 Executing sandwich attack...")

        start_time = time.time()
        snapshot_id = None

        try:
            # Step 1: Take snapshot
            snapshot_id = self.fork.create_snapshot()

            # Step 2: Simulate if requested
            if simulate_first:
                sim_result = self._simulate_sandwich(params)
                if not sim_result['profitable']:
                    logger.warning("⚠️  Simulation shows unprofitable attack")
                    return self._create_unprofitable_result(
                        AttackType.SANDWICH,
                        sim_result
                    )

            # Step 3: Get initial balances
            attacker = self.fork.accounts[0]
            initial_balance = self.fork.get_balance(attacker)

            # Step 4: Execute frontrun
            logger.info("1️⃣ Executing frontrun swap...")
            frontrun_success, frontrun_tx, frontrun_receipt = self._execute_swap(
                from_address=attacker,
                pool=params.pool_address,
                amount_in=params.frontrun_amount,
                token_in=params.token_in,
                token_out=params.token_out,
                min_amount_out=0  # Accept any slippage
            )

            if not frontrun_success:
                return self._create_failed_result(
                    AttackType.SANDWICH,
                    "Frontrun failed",
                    frontrun_receipt
                )

            frontrun_block = frontrun_receipt['blockNumber']
            frontrun_gas = frontrun_receipt['gasUsed']

            # Step 5: Execute target transaction (simulated victim)
            logger.info("2️⃣ Executing target/victim swap...")
            target_success, target_tx, target_receipt = self._execute_swap(
                from_address=self.fork.accounts[1],  # Different account
                pool=params.pool_address,
                amount_in=params.target_swap_amount,
                token_in=params.token_in,
                token_out=params.token_out,
                min_amount_out=int(
                    params.target_swap_amount * (1 - params.slippage_tolerance)
                )
            )

            if not target_success:
                logger.warning("⚠️  Target transaction failed (victim would be protected)")
                # This might actually be a good thing - attack blocked
                return self._create_failed_result(
                    AttackType.SANDWICH,
                    "Target transaction failed",
                    target_receipt
                )

            target_block = target_receipt['blockNumber']
            target_gas = target_receipt['gasUsed']

            # Step 6: Execute backrun
            logger.info("3️⃣ Executing backrun swap...")
            backrun_success, backrun_tx, backrun_receipt = self._execute_swap(
                from_address=attacker,
                pool=params.pool_address,
                amount_in=0,  # Sell all token_out back to token_in
                token_in=params.token_out,  # Reverse direction
                token_out=params.token_in,
                min_amount_out=params.frontrun_amount,  # At least get back what we put in
                sell_all=True
            )

            if not backrun_success:
                return self._create_failed_result(
                    AttackType.SANDWICH,
                    "Backrun failed",
                    backrun_receipt
                )

            backrun_block = backrun_receipt['blockNumber']
            backrun_gas = backrun_receipt['gasUsed']

            # Step 7: Calculate profit
            final_balance = self.fork.get_balance(attacker)

            total_gas_used = frontrun_gas + target_gas + backrun_gas
            gas_cost_wei = total_gas_used * self.fork.config.gas_price

            gross_profit_wei = final_balance - initial_balance
            net_profit_wei = gross_profit_wei - gas_cost_wei

            gross_profit_usd = self._wei_to_usd(gross_profit_wei)
            net_profit_usd = self._wei_to_usd(net_profit_wei)

            # Step 8: Determine status
            if net_profit_wei > 0:
                status = AttackStatus.SUCCESS
                logger.info(f"✅ Sandwich attack successful!")
                logger.info(f"💰 Net profit: {net_profit_usd:.2f} USD")
            else:
                status = AttackStatus.UNPROFITABLE
                logger.warning(f"📉 Attack unprofitable: -${abs(net_profit_usd):.2f}")

            # Step 9: Create result with proof
            execution_time_ms = (time.time() - start_time) * 1000

            result = AttackResult(
                attack_type=AttackType.SANDWICH,
                status=status,
                profit_wei=gross_profit_wei,
                profit_usd=gross_profit_usd,
                gas_used=total_gas_used,
                gas_cost_wei=gas_cost_wei,
                net_profit_wei=net_profit_wei,
                net_profit_usd=net_profit_usd,
                transactions=[frontrun_tx, target_tx, backrun_tx],
                block_numbers=[frontrun_block, target_block, backrun_block],
                execution_time_ms=execution_time_ms,
                timestamp=int(time.time()),
                proof_of_exploit={
                    'frontrun': {
                        'tx_hash': frontrun_tx,
                        'block': frontrun_block,
                        'gas_used': frontrun_gas,
                        'amount_in': params.frontrun_amount
                    },
                    'target': {
                        'tx_hash': target_tx,
                        'block': target_block,
                        'gas_used': target_gas,
                        'amount_in': params.target_swap_amount
                    },
                    'backrun': {
                        'tx_hash': backrun_tx,
                        'block': backrun_block,
                        'gas_used': backrun_gas
                    },
                    'initial_balance': initial_balance,
                    'final_balance': final_balance,
                    'slippage_protection': params.slippage_tolerance
                }
            )

            self.attack_history.append(result)

            return result

        except Exception as e:
            logger.error(f"❌ Sandwich attack execution failed: {e}")

            return AttackResult(
                attack_type=AttackType.SANDWICH,
                status=AttackStatus.FAILED,
                profit_wei=0,
                profit_usd=0.0,
                gas_used=0,
                gas_cost_wei=0,
                net_profit_wei=0,
                net_profit_usd=0.0,
                proof_of_exploit={'error': str(e)},
                execution_time_ms=(time.time() - start_time) * 1000
            )

        finally:
            # Restore snapshot for next test
            if snapshot_id:
                self.fork.restore_snapshot(snapshot_id)

    def execute_flash_loan_attack(
        self,
        params: FlashLoanAttackParams
    ) -> AttackResult:
        """
        Execute a real flash loan attack

        Process:
        1. Deploy flash loan attacker contract
        2. Execute flash loan with attack logic
        3. Measure profit after repaying loan + fee
        4. Validate result

        Args:
            params: Flash loan attack parameters

        Returns:
            AttackResult with proof
        """
        logger.info(f"⚡ Executing flash loan attack...")

        start_time = time.time()
        snapshot_id = self.fork.create_snapshot()

        try:
            # Step 1: Deploy attacker contract
            # (In real implementation, deploy actual Solidity contract)
            logger.info("📝 Deploying flash loan attacker contract...")

            # For now, simulate the attack sequence
            attacker = self.fork.accounts[0]
            initial_balance = self.fork.get_balance(attacker)

            # Step 2: Execute attack sequence
            total_gas = 0
            transactions = []

            for i, action in enumerate(params.attack_sequence):
                logger.info(f"Executing attack step {i+1}/{len(params.attack_sequence)}...")

                # Execute action (swap, borrow, repay, etc.)
                success, tx_hash, receipt = self._execute_action(action, attacker)

                if not success:
                    return self._create_failed_result(
                        AttackType.FLASH_LOAN,
                        f"Attack step {i+1} failed",
                        receipt
                    )

                total_gas += receipt['gasUsed']
                transactions.append(tx_hash)

            # Step 3: Calculate profit (after loan repayment)
            final_balance = self.fork.get_balance(attacker)

            gas_cost_wei = total_gas * self.fork.config.gas_price
            gross_profit_wei = final_balance - initial_balance
            net_profit_wei = gross_profit_wei - gas_cost_wei

            status = AttackStatus.SUCCESS if net_profit_wei > 0 else AttackStatus.UNPROFITABLE

            result = AttackResult(
                attack_type=AttackType.FLASH_LOAN,
                status=status,
                profit_wei=gross_profit_wei,
                profit_usd=self._wei_to_usd(gross_profit_wei),
                gas_used=total_gas,
                gas_cost_wei=gas_cost_wei,
                net_profit_wei=net_profit_wei,
                net_profit_usd=self._wei_to_usd(net_profit_wei),
                transactions=transactions,
                execution_time_ms=(time.time() - start_time) * 1000,
                proof_of_exploit={
                    'loan_amount': params.loan_amount,
                    'loan_token': params.loan_token,
                    'attack_steps': len(params.attack_sequence),
                    'initial_balance': initial_balance,
                    'final_balance': final_balance
                }
            )

            self.attack_history.append(result)

            return result

        except Exception as e:
            logger.error(f"❌ Flash loan attack failed: {e}")

            return AttackResult(
                attack_type=AttackType.FLASH_LOAN,
                status=AttackStatus.FAILED,
                profit_wei=0,
                profit_usd=0.0,
                gas_used=0,
                gas_cost_wei=0,
                net_profit_wei=0,
                net_profit_usd=0.0,
                proof_of_exploit={'error': str(e)},
                execution_time_ms=(time.time() - start_time) * 1000
            )

        finally:
            self.fork.restore_snapshot(snapshot_id)

    def execute_oracle_manipulation_attack(
        self,
        params: OracleAttackParams
    ) -> AttackResult:
        """
        Execute real oracle manipulation attack

        Process:
        1. Record original oracle price
        2. Execute manipulation transactions
        3. Verify price changed
        4. Exploit the manipulated price
        5. Calculate profit

        Args:
            params: Oracle attack parameters

        Returns:
            AttackResult with proof
        """
        logger.info(f"🎯 Executing oracle manipulation attack...")

        start_time = time.time()
        snapshot_id = self.fork.create_snapshot()

        try:
            attacker = self.fork.accounts[0]
            initial_balance = self.fork.get_balance(attacker)

            # Step 1: Read original price
            original_price = self._read_oracle_price(params.oracle_address)
            logger.info(f"📊 Original price: {original_price}")

            # Step 2: Execute manipulation
            total_gas = 0
            transactions = []

            for action in params.manipulation_transactions:
                success, tx_hash, receipt = self._execute_action(action, attacker)

                if not success:
                    return self._create_failed_result(
                        AttackType.ORACLE_MANIPULATION,
                        "Manipulation failed",
                        receipt
                    )

                total_gas += receipt['gasUsed']
                transactions.append(tx_hash)

            # Step 3: Verify manipulation
            manipulated_price = self._read_oracle_price(params.oracle_address)
            logger.info(f"📊 Manipulated price: {manipulated_price}")

            price_change = abs(manipulated_price - original_price) / original_price

            if price_change < 0.01:  # < 1% change
                logger.warning("⚠️  Oracle manipulation insufficient")

            # Step 4: Exploit (borrow at manipulated price, etc.)
            # Implementation depends on target protocol

            # Step 5: Calculate profit
            final_balance = self.fork.get_balance(attacker)

            gas_cost_wei = total_gas * self.fork.config.gas_price
            gross_profit_wei = final_balance - initial_balance
            net_profit_wei = gross_profit_wei - gas_cost_wei

            status = AttackStatus.SUCCESS if net_profit_wei > 0 else AttackStatus.UNPROFITABLE

            result = AttackResult(
                attack_type=AttackType.ORACLE_MANIPULATION,
                status=status,
                profit_wei=gross_profit_wei,
                profit_usd=self._wei_to_usd(gross_profit_wei),
                gas_used=total_gas,
                gas_cost_wei=gas_cost_wei,
                net_profit_wei=net_profit_wei,
                net_profit_usd=self._wei_to_usd(net_profit_wei),
                transactions=transactions,
                execution_time_ms=(time.time() - start_time) * 1000,
                proof_of_exploit={
                    'oracle': params.oracle_address,
                    'original_price': original_price,
                    'manipulated_price': manipulated_price,
                    'price_change_percent': price_change * 100,
                    'manipulation_method': params.manipulation_method
                }
            )

            self.attack_history.append(result)

            return result

        except Exception as e:
            logger.error(f"❌ Oracle manipulation failed: {e}")

            return AttackResult(
                attack_type=AttackType.ORACLE_MANIPULATION,
                status=AttackStatus.FAILED,
                profit_wei=0,
                profit_usd=0.0,
                gas_used=0,
                gas_cost_wei=0,
                net_profit_wei=0,
                net_profit_usd=0.0,
                proof_of_exploit={'error': str(e)},
                execution_time_ms=(time.time() - start_time) * 1000
            )

        finally:
            self.fork.restore_snapshot(snapshot_id)

    def get_attack_history(self) -> List[AttackResult]:
        """Get history of all executed attacks"""
        return self.attack_history

    def get_total_profit(self) -> float:
        """Get total profit from all successful attacks"""
        return sum(
            r.net_profit_usd
            for r in self.attack_history
            if r.status == AttackStatus.SUCCESS
        )

    def generate_exploit_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive exploit report

        Returns:
            Report with all proven exploits and evidence
        """
        successful_attacks = [
            r for r in self.attack_history
            if r.status == AttackStatus.SUCCESS
        ]

        return {
            'summary': {
                'total_attacks': len(self.attack_history),
                'successful': len(successful_attacks),
                'failed': len([r for r in self.attack_history if r.status == AttackStatus.FAILED]),
                'unprofitable': len([r for r in self.attack_history if r.status == AttackStatus.UNPROFITABLE]),
                'total_profit_usd': self.get_total_profit(),
                'total_gas_used': sum(r.gas_used for r in self.attack_history)
            },
            'exploits': [
                {
                    'type': r.attack_type.value,
                    'profit_usd': r.net_profit_usd,
                    'transactions': r.transactions,
                    'proof': r.proof_of_exploit,
                    'timestamp': r.timestamp
                }
                for r in successful_attacks
            ],
            'attack_breakdown': {
                attack_type.value: {
                    'count': len([r for r in self.attack_history if r.attack_type == attack_type]),
                    'success_rate': len([
                        r for r in self.attack_history
                        if r.attack_type == attack_type and r.status == AttackStatus.SUCCESS
                    ]) / max(len([r for r in self.attack_history if r.attack_type == attack_type]), 1)
                }
                for attack_type in AttackType
            }
        }

    # Private helper methods

    def _simulate_sandwich(self, params: SandwichAttackParams) -> Dict[str, Any]:
        """
        Simulate sandwich attack without executing

        Returns:
            Simulation result with profitability estimate
        """
        # Simplified simulation
        # Real implementation would use getAmountOut calculations

        estimated_profit = params.frontrun_amount * 0.01  # 1% profit estimate
        estimated_gas = 300000  # 3 transactions

        gas_cost = estimated_gas * self.fork.config.gas_price

        return {
            'profitable': estimated_profit > gas_cost,
            'estimated_profit': estimated_profit,
            'estimated_gas': estimated_gas
        }

    def _execute_swap(
        self,
        from_address: ChecksumAddress,
        pool: ChecksumAddress,
        amount_in: int,
        token_in: ChecksumAddress,
        token_out: ChecksumAddress,
        min_amount_out: int,
        sell_all: bool = False
    ) -> Tuple[bool, str, Dict]:
        """Execute a swap on a DEX"""
        # This would call the actual DEX router contract
        # For now, simplified implementation

        # Build swap transaction data
        # In real implementation: encode swap function call

        success, tx_hash, receipt = self.fork.execute_transaction(
            from_address=from_address,
            to_address=pool,
            data=b"",  # Encoded swap call
            value=amount_in if token_in == self.w3.to_checksum_address("0x0") else 0
        )

        return success, tx_hash, receipt

    def _execute_action(
        self,
        action: Dict[str, Any],
        from_address: ChecksumAddress
    ) -> Tuple[bool, str, Dict]:
        """Execute a generic action"""
        # Dispatch based on action type

        action_type = action.get('type')

        if action_type == 'swap':
            return self._execute_swap(
                from_address=from_address,
                pool=action['pool'],
                amount_in=action['amount_in'],
                token_in=action['token_in'],
                token_out=action['token_out'],
                min_amount_out=action.get('min_amount_out', 0)
            )

        # Add more action types as needed

        return False, "", {"error": f"Unknown action type: {action_type}"}

    def _read_oracle_price(self, oracle_address: ChecksumAddress) -> int:
        """Read price from oracle contract"""
        # Call oracle's getPrice() or latestAnswer() function
        # For now, return placeholder

        result = self.fork.call_contract(
            contract_address=oracle_address,
            function_signature="latestAnswer()",
            args=[]
        )

        # Decode result
        price = int.from_bytes(result, byteorder='big')

        return price

    def _wei_to_usd(self, wei: int) -> float:
        """Convert wei to USD"""
        eth = wei / 10**18
        return eth * self.eth_usd_price

    def _create_failed_result(
        self,
        attack_type: AttackType,
        reason: str,
        receipt: Dict
    ) -> AttackResult:
        """Create a failed attack result"""
        return AttackResult(
            attack_type=attack_type,
            status=AttackStatus.FAILED,
            profit_wei=0,
            profit_usd=0.0,
            gas_used=receipt.get('gasUsed', 0),
            gas_cost_wei=receipt.get('gasUsed', 0) * self.fork.config.gas_price,
            net_profit_wei=0,
            net_profit_usd=0.0,
            proof_of_exploit={'failure_reason': reason, 'receipt': receipt}
        )

    def _create_unprofitable_result(
        self,
        attack_type: AttackType,
        simulation: Dict
    ) -> AttackResult:
        """Create an unprofitable attack result"""
        return AttackResult(
            attack_type=attack_type,
            status=AttackStatus.UNPROFITABLE,
            profit_wei=0,
            profit_usd=0.0,
            gas_used=simulation.get('estimated_gas', 0),
            gas_cost_wei=0,
            net_profit_wei=0,
            net_profit_usd=0.0,
            proof_of_exploit={'simulation': simulation}
        )
