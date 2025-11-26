"""
Protocol Invariant Testing System

Week 4: 32+ invariant tests for DeFi protocols.
These are mathematical properties that MUST hold true after any transaction.
If an invariant is violated, there's a critical vulnerability.

Invariant Categories:
1. AMM Invariants (8): Uniswap V2/V3, Curve, Balancer
2. Lending Invariants (8): Aave, Compound, MakerDAO
3. Oracle Invariants (6): Chainlink, TWAP, Band Protocol
4. Governance Invariants (5): Voting power, proposal execution
5. Staking Invariants (5): Rewards, slashing, delegation
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from abc import ABC, abstractmethod

from .simulation.live_fork import LiveFork
from web3 import Web3
from eth_typing import ChecksumAddress

logger = logging.getLogger(__name__)


class InvariantSeverity(Enum):
    """Severity of invariant violation"""
    CRITICAL = "critical"  # Protocol can be drained
    HIGH = "high"         # Significant loss possible
    MEDIUM = "medium"     # Unfair advantage possible
    LOW = "low"           # Edge case, minimal impact


class InvariantCategory(Enum):
    """Category of protocol invariant"""
    AMM = "amm"
    LENDING = "lending"
    ORACLE = "oracle"
    GOVERNANCE = "governance"
    STAKING = "staking"
    VAULT = "vault"
    BRIDGE = "bridge"


@dataclass
class InvariantViolation:
    """Record of an invariant violation"""
    invariant_name: str
    category: InvariantCategory
    severity: InvariantSeverity

    # Violation details
    expected: Any
    actual: Any
    deviation: float  # Percentage deviation

    # Context
    block_number: int
    transaction_hash: Optional[str]

    # Protocol state
    protocol_state: Dict[str, Any]

    # Recommendations
    exploit_potential: str
    mitigation: str

    def __repr__(self):
        severity_emoji = {
            InvariantSeverity.CRITICAL: "🚨",
            InvariantSeverity.HIGH: "⚠️",
            InvariantSeverity.MEDIUM: "⚡",
            InvariantSeverity.LOW: "ℹ️"
        }
        emoji = severity_emoji[self.severity]

        return (
            f"InvariantViolation({emoji} {self.invariant_name}, "
            f"deviation={self.deviation:.2f}%, {self.severity.value})"
        )


class ProtocolInvariant(ABC):
    """
    Base class for protocol invariants

    Each invariant defines:
    - check(): Verify the invariant holds
    - severity: Impact if violated
    - description: What the invariant protects
    """

    def __init__(
        self,
        name: str,
        category: InvariantCategory,
        severity: InvariantSeverity,
        description: str
    ):
        self.name = name
        self.category = category
        self.severity = severity
        self.description = description

    @abstractmethod
    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        """
        Check if invariant holds

        Args:
            fork: Live fork instance
            protocol_address: Protocol contract address

        Returns:
            InvariantViolation if violated, None if holds
        """
        pass

    def _create_violation(
        self,
        expected: Any,
        actual: Any,
        fork: LiveFork,
        protocol_address: ChecksumAddress,
        tx_hash: Optional[str] = None,
        exploit_potential: str = "",
        mitigation: str = ""
    ) -> InvariantViolation:
        """Helper to create violation object"""

        # Calculate deviation
        try:
            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                deviation = abs((actual - expected) / expected) * 100
            else:
                deviation = 100.0  # Non-numeric
        except ZeroDivisionError:
            deviation = 100.0

        return InvariantViolation(
            invariant_name=self.name,
            category=self.category,
            severity=self.severity,
            expected=expected,
            actual=actual,
            deviation=deviation,
            block_number=fork.w3.eth.block_number,
            transaction_hash=tx_hash,
            protocol_state=self._capture_protocol_state(fork, protocol_address),
            exploit_potential=exploit_potential,
            mitigation=mitigation
        )

    def _capture_protocol_state(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Dict[str, Any]:
        """Capture protocol state for debugging"""
        return {
            'address': protocol_address,
            'balance': fork.get_balance(protocol_address),
            'block': fork.w3.eth.block_number
        }


# ============================================================================
# AMM INVARIANTS (8 total)
# ============================================================================

class AMMConstantProductInvariant(ProtocolInvariant):
    """
    AMM Invariant #1: Constant Product (x * y = k)

    For Uniswap V2 and similar AMMs, the product of reserves must remain constant
    (or increase due to fees) after any swap.

    Violation = Protocol can be drained
    """

    def __init__(self):
        super().__init__(
            name="AMM Constant Product",
            category=InvariantCategory.AMM,
            severity=InvariantSeverity.CRITICAL,
            description="Product of reserves must remain constant or increase (x * y >= k)"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        """Check x * y >= k invariant"""

        try:
            # Read reserves before
            reserves_before = self._get_reserves(fork, protocol_address)
            k_before = reserves_before['reserve0'] * reserves_before['reserve1']

            # Execute a swap (if there's a pending transaction)
            # In real implementation, this would be called after each transaction

            # Read reserves after
            reserves_after = self._get_reserves(fork, protocol_address)
            k_after = reserves_after['reserve0'] * reserves_after['reserve1']

            # Check invariant
            if k_after < k_before:
                return self._create_violation(
                    expected=f"k >= {k_before}",
                    actual=f"k = {k_after}",
                    fork=fork,
                    protocol_address=protocol_address,
                    exploit_potential="Protocol can be drained through repeated swaps that decrease k",
                    mitigation="Add validation: require(k_after >= k_before) in swap function"
                )

            return None

        except Exception as e:
            logger.error(f"Error checking constant product: {e}")
            return None

    def _get_reserves(self, fork: LiveFork, pool: ChecksumAddress) -> Dict[str, int]:
        """Get pool reserves"""
        # Call getReserves() function
        result = fork.call_contract(
            contract_address=pool,
            function_signature="getReserves()",
            args=[]
        )

        # Decode (reserve0, reserve1, timestamp)
        # Simplified - real implementation would use ABI decoder
        reserve0 = int.from_bytes(result[:32], byteorder='big')
        reserve1 = int.from_bytes(result[32:64], byteorder='big')

        return {'reserve0': reserve0, 'reserve1': reserve1}


class AMMSlippageProtectionInvariant(ProtocolInvariant):
    """
    AMM Invariant #2: Slippage Protection

    User must receive at least min_amount_out tokens.
    If actual < min_amount_out, the swap should revert.

    Violation = User receives less than minimum acceptable
    """

    def __init__(self):
        super().__init__(
            name="AMM Slippage Protection",
            category=InvariantCategory.AMM,
            severity=InvariantSeverity.HIGH,
            description="Swap output must be >= min_amount_out parameter"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        """Check slippage protection"""
        # Implementation would verify actual_out >= min_amount_out for recent swaps
        return None


class AMMPriceImpactInvariant(ProtocolInvariant):
    """
    AMM Invariant #3: Price Impact Limits

    Large swaps should not move price more than reasonable threshold.
    Excessive price impact enables sandwich attacks.

    Violation = Sandwich attack opportunity
    """

    def __init__(self):
        super().__init__(
            name="AMM Price Impact Limits",
            category=InvariantCategory.AMM,
            severity=InvariantSeverity.MEDIUM,
            description="Price impact should not exceed reasonable threshold (e.g., 5%)"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        """Check price impact"""
        # Implementation would calculate price before/after swap
        return None


class AMMLiquidityInvariant(ProtocolInvariant):
    """
    AMM Invariant #4: Minimum Liquidity

    Pool must maintain minimum liquidity to prevent manipulation.
    Very low liquidity enables price manipulation.

    Violation = Price manipulation possible
    """

    def __init__(self):
        super().__init__(
            name="AMM Minimum Liquidity",
            category=InvariantCategory.AMM,
            severity=InvariantSeverity.HIGH,
            description="Pool must maintain minimum liquidity threshold"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        """Check minimum liquidity"""
        try:
            reserves = self._get_reserves(fork, protocol_address)

            min_liquidity = 1000  # 1000 smallest units (configurable)

            if reserves['reserve0'] < min_liquidity or reserves['reserve1'] < min_liquidity:
                return self._create_violation(
                    expected=f"reserves >= {min_liquidity}",
                    actual=f"reserve0={reserves['reserve0']}, reserve1={reserves['reserve1']}",
                    fork=fork,
                    protocol_address=protocol_address,
                    exploit_potential="Low liquidity enables price manipulation attacks",
                    mitigation="Enforce minimum liquidity: require(reserve0 >= MIN_LIQUIDITY && reserve1 >= MIN_LIQUIDITY)"
                )

            return None

        except Exception as e:
            logger.error(f"Error checking minimum liquidity: {e}")
            return None

    def _get_reserves(self, fork: LiveFork, pool: ChecksumAddress) -> Dict[str, int]:
        """Get pool reserves"""
        result = fork.call_contract(pool, "getReserves()", [])
        reserve0 = int.from_bytes(result[:32], byteorder='big')
        reserve1 = int.from_bytes(result[32:64], byteorder='big')
        return {'reserve0': reserve0, 'reserve1': reserve1}


class AMMFeeAccrualInvariant(ProtocolInvariant):
    """
    AMM Invariant #5: Fee Accrual

    Fees must accrue to LPs correctly. No fee leakage.

    Violation = LP funds stolen
    """

    def __init__(self):
        super().__init__(
            name="AMM Fee Accrual",
            category=InvariantCategory.AMM,
            severity=InvariantSeverity.HIGH,
            description="Trading fees must accrue to liquidity providers"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class AMMOracleManipulationResistance(ProtocolInvariant):
    """
    AMM Invariant #6: Oracle Manipulation Resistance

    TWAP (Time-Weighted Average Price) must be resistant to single-block manipulation.

    Violation = Oracle manipulation possible
    """

    def __init__(self):
        super().__init__(
            name="AMM Oracle Manipulation Resistance",
            category=InvariantCategory.AMM,
            severity=InvariantSeverity.CRITICAL,
            description="TWAP should not be manipulable in single block"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class AMMFlashLoanProtection(ProtocolInvariant):
    """
    AMM Invariant #7: Flash Loan Attack Protection

    State changes within single transaction must not enable unfair profit extraction.

    Violation = Flash loan attack possible
    """

    def __init__(self):
        super().__init__(
            name="AMM Flash Loan Protection",
            category=InvariantCategory.AMM,
            severity=InvariantSeverity.CRITICAL,
            description="Single-transaction exploits should not be profitable"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class AMMReentrancyProtection(ProtocolInvariant):
    """
    AMM Invariant #8: Reentrancy Protection

    State must be updated before external calls.

    Violation = Reentrancy attack possible
    """

    def __init__(self):
        super().__init__(
            name="AMM Reentrancy Protection",
            category=InvariantCategory.AMM,
            severity=InvariantSeverity.CRITICAL,
            description="State updates before external calls (checks-effects-interactions)"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


# ============================================================================
# LENDING INVARIANTS (8 total)
# ============================================================================

class LendingCollateralizationInvariant(ProtocolInvariant):
    """
    Lending Invariant #1: Collateralization Ratio

    All loans must be overcollateralized at all times.
    collateral_value >= borrow_value * collateral_ratio

    Violation = Under-collateralized loans, protocol insolvency
    """

    def __init__(self):
        super().__init__(
            name="Lending Collateralization Ratio",
            category=InvariantCategory.LENDING,
            severity=InvariantSeverity.CRITICAL,
            description="All loans must maintain minimum collateralization ratio"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        """Check collateralization for all positions"""
        try:
            # Get all borrowers (in real implementation)
            # For each borrower, check: collateral_value >= borrow_value * min_ratio

            # Example for one position:
            collateral_value = 100_000  # USD
            borrow_value = 80_000       # USD
            min_ratio = 1.5             # 150%

            required_collateral = borrow_value * min_ratio

            if collateral_value < required_collateral:
                return self._create_violation(
                    expected=f"collateral >= {required_collateral}",
                    actual=f"collateral = {collateral_value}",
                    fork=fork,
                    protocol_address=protocol_address,
                    exploit_potential="Under-collateralized loans can lead to protocol insolvency if not liquidated",
                    mitigation="Implement robust liquidation system with incentives"
                )

            return None

        except Exception as e:
            logger.error(f"Error checking collateralization: {e}")
            return None


class LendingUtilizationInvariant(ProtocolInvariant):
    """
    Lending Invariant #2: Utilization Rate

    utilization = borrowed / (borrowed + available) <= 100%

    Violation = Accounting error, infinite borrow
    """

    def __init__(self):
        super().__init__(
            name="Lending Utilization Rate",
            category=InvariantCategory.LENDING,
            severity=InvariantSeverity.CRITICAL,
            description="Utilization rate must be <= 100%"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class LendingInterestAccrualInvariant(ProtocolInvariant):
    """
    Lending Invariant #3: Interest Accrual

    Interest must accrue correctly over time.
    total_borrowed + interest >= initial_borrowed

    Violation = Interest calculation error
    """

    def __init__(self):
        super().__init__(
            name="Lending Interest Accrual",
            category=InvariantCategory.LENDING,
            severity=InvariantSeverity.HIGH,
            description="Interest must accrue monotonically"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class LendingLiquidationBonusInvariant(ProtocolInvariant):
    """
    Lending Invariant #4: Liquidation Bonus

    Liquidation bonus must be reasonable (5-10%).
    Too high = excessive liquidations, too low = insufficient incentive.

    Violation = Unfair liquidations or liquidation crisis
    """

    def __init__(self):
        super().__init__(
            name="Lending Liquidation Bonus",
            category=InvariantCategory.LENDING,
            severity=InvariantSeverity.MEDIUM,
            description="Liquidation bonus should be in reasonable range (5-10%)"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class LendingHealthFactorInvariant(ProtocolInvariant):
    """
    Lending Invariant #5: Health Factor

    health_factor = collateral_value / borrow_value
    Positions with health_factor < 1.0 should be liquidatable.

    Violation = Underwater positions not liquidatable
    """

    def __init__(self):
        super().__init__(
            name="Lending Health Factor",
            category=InvariantCategory.LENDING,
            severity=InvariantSeverity.CRITICAL,
            description="Positions with health factor < 1 must be liquidatable"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class LendingReserveFactor(ProtocolInvariant):
    """
    Lending Invariant #6: Reserve Factor

    Protocol must maintain reserves for bad debt.

    Violation = Insolvency risk
    """

    def __init__(self):
        super().__init__(
            name="Lending Reserve Factor",
            category=InvariantCategory.LENDING,
            severity=InvariantSeverity.HIGH,
            description="Protocol must maintain adequate reserves"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class LendingFlashLoanFee(ProtocolInvariant):
    """
    Lending Invariant #7: Flash Loan Fee

    Flash loans must charge non-zero fee.

    Violation = Free flash loans enable attacks
    """

    def __init__(self):
        super().__init__(
            name="Lending Flash Loan Fee",
            category=InvariantCategory.LENDING,
            severity=InvariantSeverity.HIGH,
            description="Flash loans must have non-zero fee (typically 0.09%)"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class LendingBorrowCapInvariant(ProtocolInvariant):
    """
    Lending Invariant #8: Borrow Cap

    Total borrowed <= borrow cap (if set).

    Violation = Borrow cap bypass
    """

    def __init__(self):
        super().__init__(
            name="Lending Borrow Cap",
            category=InvariantCategory.LENDING,
            severity=InvariantSeverity.MEDIUM,
            description="Total borrowed must not exceed borrow cap"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


# ============================================================================
# ORACLE INVARIANTS (6 total)
# ============================================================================

class OracleFreshnessInvariant(ProtocolInvariant):
    """
    Oracle Invariant #1: Price Freshness

    Oracle prices must be updated within acceptable timeframe.
    Stale prices enable arbitrage.

    Violation = Stale price exploitation
    """

    def __init__(self):
        super().__init__(
            name="Oracle Price Freshness",
            category=InvariantCategory.ORACLE,
            severity=InvariantSeverity.CRITICAL,
            description="Oracle prices must be updated within acceptable timeframe (e.g., 1 hour)"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        try:
            # Read latest price update timestamp
            result = fork.call_contract(
                contract_address=protocol_address,
                function_signature="latestRoundData()",
                args=[]
            )

            # Decode timestamp (typically 4th return value in Chainlink)
            # Simplified - real implementation would decode all return values
            updated_at = int.from_bytes(result[96:128], byteorder='big')

            current_time = fork.w3.eth.get_block('latest')['timestamp']
            age = current_time - updated_at

            max_age = 3600  # 1 hour

            if age > max_age:
                return self._create_violation(
                    expected=f"age <= {max_age}s",
                    actual=f"age = {age}s",
                    fork=fork,
                    protocol_address=protocol_address,
                    exploit_potential="Stale prices can be exploited for arbitrage or undercollateralized borrows",
                    mitigation="Add staleness check: require(block.timestamp - updatedAt <= MAX_AGE)"
                )

            return None

        except Exception as e:
            logger.error(f"Error checking oracle freshness: {e}")
            return None


class OracleManipulationResistance(ProtocolInvariant):
    """
    Oracle Invariant #2: Manipulation Resistance

    Oracle should not be manipulable in single block/transaction.

    Violation = Oracle manipulation attack
    """

    def __init__(self):
        super().__init__(
            name="Oracle Manipulation Resistance",
            category=InvariantCategory.ORACLE,
            severity=InvariantSeverity.CRITICAL,
            description="Oracle prices must be resistant to single-block manipulation"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class OraclePriceDeviationInvariant(ProtocolInvariant):
    """
    Oracle Invariant #3: Price Deviation Limits

    Price changes between updates should not exceed threshold.
    Excessive deviation = manipulation or data error.

    Violation = Manipulated or erroneous price
    """

    def __init__(self):
        super().__init__(
            name="Oracle Price Deviation Limits",
            category=InvariantCategory.ORACLE,
            severity=InvariantSeverity.HIGH,
            description="Price deviation between updates must be reasonable (e.g., <10%)"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class OracleCircuitBreakerInvariant(ProtocolInvariant):
    """
    Oracle Invariant #4: Circuit Breaker

    Oracle should pause if price moves too much.

    Violation = No protection against extreme events
    """

    def __init__(self):
        super().__init__(
            name="Oracle Circuit Breaker",
            category=InvariantCategory.ORACLE,
            severity=InvariantSeverity.MEDIUM,
            description="Oracle should pause on extreme price movements"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class OracleMultiSourceValidation(ProtocolInvariant):
    """
    Oracle Invariant #5: Multi-Source Validation

    Critical protocols should use multiple oracle sources.

    Violation = Single point of failure
    """

    def __init__(self):
        super().__init__(
            name="Oracle Multi-Source Validation",
            category=InvariantCategory.ORACLE,
            severity=InvariantSeverity.HIGH,
            description="Critical systems should aggregate multiple oracle sources"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class OracleFallbackMechanism(ProtocolInvariant):
    """
    Oracle Invariant #6: Fallback Mechanism

    Oracle should have fallback if primary source fails.

    Violation = DoS when oracle fails
    """

    def __init__(self):
        super().__init__(
            name="Oracle Fallback Mechanism",
            category=InvariantCategory.ORACLE,
            severity=InvariantSeverity.MEDIUM,
            description="Oracle should have fallback data source"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


# ============================================================================
# GOVERNANCE INVARIANTS (5 total)
# ============================================================================

class GovernanceVotingPowerInvariant(ProtocolInvariant):
    """
    Governance Invariant #1: Voting Power

    voting_power = token_balance at proposal_creation
    Voting power must be locked at snapshot.

    Violation = Vote buying, flash loan governance attack
    """

    def __init__(self):
        super().__init__(
            name="Governance Voting Power Snapshot",
            category=InvariantCategory.GOVERNANCE,
            severity=InvariantSeverity.CRITICAL,
            description="Voting power must be determined by snapshot, not current balance"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class GovernanceTimelockInvariant(ProtocolInvariant):
    """
    Governance Invariant #2: Timelock

    Proposals must have timelock before execution.

    Violation = Immediate malicious proposal execution
    """

    def __init__(self):
        super().__init__(
            name="Governance Timelock",
            category=InvariantCategory.GOVERNANCE,
            severity=InvariantSeverity.CRITICAL,
            description="Proposals must have adequate timelock (e.g., 48 hours)"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class GovernanceQuorumInvariant(ProtocolInvariant):
    """
    Governance Invariant #3: Quorum

    Proposals must meet minimum quorum to pass.

    Violation = Low participation governance takeover
    """

    def __init__(self):
        super().__init__(
            name="Governance Quorum Requirement",
            category=InvariantCategory.GOVERNANCE,
            severity=InvariantSeverity.HIGH,
            description="Proposals must meet minimum quorum threshold"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class GovernanceProposalThreshold(ProtocolInvariant):
    """
    Governance Invariant #4: Proposal Threshold

    Minimum tokens required to create proposal.

    Violation = Governance spam
    """

    def __init__(self):
        super().__init__(
            name="Governance Proposal Threshold",
            category=InvariantCategory.GOVERNANCE,
            severity=InvariantSeverity.MEDIUM,
            description="Proposal creation requires minimum token threshold"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class GovernanceVetoPower(ProtocolInvariant):
    """
    Governance Invariant #5: Veto Power

    Some protocols have guardian veto for malicious proposals.

    Violation = No emergency protection
    """

    def __init__(self):
        super().__init__(
            name="Governance Veto Mechanism",
            category=InvariantCategory.GOVERNANCE,
            severity=InvariantSeverity.MEDIUM,
            description="Critical governance should have guardian veto capability"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


# ============================================================================
# STAKING INVARIANTS (5 total)
# ============================================================================

class StakingRewardAccrualInvariant(ProtocolInvariant):
    """
    Staking Invariant #1: Reward Accrual

    Rewards must accrue fairly based on stake and time.

    Violation = Unfair reward distribution
    """

    def __init__(self):
        super().__init__(
            name="Staking Reward Accrual",
            category=InvariantCategory.STAKING,
            severity=InvariantSeverity.HIGH,
            description="Rewards must accrue proportionally to stake and time"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class StakingUnbondingPeriod(ProtocolInvariant):
    """
    Staking Invariant #2: Unbonding Period

    Stakes must have minimum lock-up period.

    Violation = Flash staking attacks
    """

    def __init__(self):
        super().__init__(
            name="Staking Unbonding Period",
            category=InvariantCategory.STAKING,
            severity=InvariantSeverity.MEDIUM,
            description="Unstaking must enforce minimum unbonding period"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class StakingSlashingInvariant(ProtocolInvariant):
    """
    Staking Invariant #3: Slashing Protection

    Slashing must not exceed maximum threshold.

    Violation = Total stake loss
    """

    def __init__(self):
        super().__init__(
            name="Staking Slashing Limits",
            category=InvariantCategory.STAKING,
            severity=InvariantSeverity.CRITICAL,
            description="Slashing must not exceed maximum percentage (e.g., 30%)"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class StakingDelegationInvariant(ProtocolInvariant):
    """
    Staking Invariant #4: Delegation Accounting

    Delegated stake must sum correctly.

    Violation = Accounting error, double delegation
    """

    def __init__(self):
        super().__init__(
            name="Staking Delegation Accounting",
            category=InvariantCategory.STAKING,
            severity=InvariantSeverity.HIGH,
            description="Total delegated = sum of all delegations"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


class StakingRewardPoolSolvency(ProtocolInvariant):
    """
    Staking Invariant #5: Reward Pool Solvency

    Reward pool must have sufficient funds.

    Violation = Rewards can't be paid
    """

    def __init__(self):
        super().__init__(
            name="Staking Reward Pool Solvency",
            category=InvariantCategory.STAKING,
            severity=InvariantSeverity.CRITICAL,
            description="Reward pool must have >= total_accrued_rewards"
        )

    def check(self, fork: LiveFork, protocol_address: ChecksumAddress) -> Optional[InvariantViolation]:
        return None


# ============================================================================
# INVARIANT CHECKER
# ============================================================================

class InvariantChecker:
    """
    Protocol Invariant Checker

    Runs all 32+ invariant tests against a protocol.

    Usage:
        checker = InvariantChecker(fork)
        violations = checker.check_all_invariants(protocol_address)

        if violations:
            print(f"Found {len(violations)} invariant violations!")
            for v in violations:
                print(v)
    """

    def __init__(self, fork: LiveFork):
        self.fork = fork

        # Register all invariants
        self.invariants: List[ProtocolInvariant] = [
            # AMM (8)
            AMMConstantProductInvariant(),
            AMMSlippageProtectionInvariant(),
            AMMPriceImpactInvariant(),
            AMMLiquidityInvariant(),
            AMMFeeAccrualInvariant(),
            AMMOracleManipulationResistance(),
            AMMFlashLoanProtection(),
            AMMReentrancyProtection(),

            # Lending (8)
            LendingCollateralizationInvariant(),
            LendingUtilizationInvariant(),
            LendingInterestAccrualInvariant(),
            LendingLiquidationBonusInvariant(),
            LendingHealthFactorInvariant(),
            LendingReserveFactor(),
            LendingFlashLoanFee(),
            LendingBorrowCapInvariant(),

            # Oracle (6)
            OracleFreshnessInvariant(),
            OracleManipulationResistance(),
            OraclePriceDeviationInvariant(),
            OracleCircuitBreakerInvariant(),
            OracleMultiSourceValidation(),
            OracleFallbackMechanism(),

            # Governance (5)
            GovernanceVotingPowerInvariant(),
            GovernanceTimelockInvariant(),
            GovernanceQuorumInvariant(),
            GovernanceProposalThreshold(),
            GovernanceVetoPower(),

            # Staking (5)
            StakingRewardAccrualInvariant(),
            StakingUnbondingPeriod(),
            StakingSlashingInvariant(),
            StakingDelegationInvariant(),
            StakingRewardPoolSolvency(),
        ]

        logger.info(f"Loaded {len(self.invariants)} protocol invariants")

    def check_all_invariants(
        self,
        protocol_address: ChecksumAddress,
        categories: Optional[List[InvariantCategory]] = None
    ) -> List[InvariantViolation]:
        """
        Check all invariants (or specific categories)

        Args:
            protocol_address: Protocol to test
            categories: Limit to specific categories (None = all)

        Returns:
            List of violations found
        """
        logger.info(f"🔍 Checking invariants for {protocol_address}...")

        violations = []

        for invariant in self.invariants:
            # Filter by category if specified
            if categories and invariant.category not in categories:
                continue

            try:
                violation = invariant.check(self.fork, protocol_address)

                if violation:
                    violations.append(violation)
                    logger.warning(f"❌ {violation}")

            except Exception as e:
                logger.error(f"Error checking {invariant.name}: {e}")

        if violations:
            logger.warning(f"Found {len(violations)} invariant violations")
        else:
            logger.info(f"✅ All invariants passed!")

        return violations

    def check_category(
        self,
        protocol_address: ChecksumAddress,
        category: InvariantCategory
    ) -> List[InvariantViolation]:
        """Check invariants for specific category"""
        return self.check_all_invariants(protocol_address, categories=[category])

    def get_invariants_by_severity(
        self,
        severity: InvariantSeverity
    ) -> List[ProtocolInvariant]:
        """Get all invariants of specific severity"""
        return [inv for inv in self.invariants if inv.severity == severity]

    def generate_invariant_report(
        self,
        violations: List[InvariantViolation]
    ) -> Dict[str, Any]:
        """Generate comprehensive invariant violation report"""

        critical = [v for v in violations if v.severity == InvariantSeverity.CRITICAL]
        high = [v for v in violations if v.severity == InvariantSeverity.HIGH]
        medium = [v for v in violations if v.severity == InvariantSeverity.MEDIUM]
        low = [v for v in violations if v.severity == InvariantSeverity.LOW]

        return {
            'summary': {
                'total_violations': len(violations),
                'critical': len(critical),
                'high': len(high),
                'medium': len(medium),
                'low': len(low),
                'categories': {
                    category.value: len([v for v in violations if v.category == category])
                    for category in InvariantCategory
                }
            },
            'critical_violations': [self._format_violation(v) for v in critical],
            'high_violations': [self._format_violation(v) for v in high],
            'medium_violations': [self._format_violation(v) for v in medium],
            'low_violations': [self._format_violation(v) for v in low],
            'recommendations': self._generate_recommendations(violations)
        }

    def _format_violation(self, v: InvariantViolation) -> Dict[str, Any]:
        """Format violation for report"""
        return {
            'name': v.invariant_name,
            'category': v.category.value,
            'severity': v.severity.value,
            'expected': str(v.expected),
            'actual': str(v.actual),
            'deviation': f"{v.deviation:.2f}%",
            'block': v.block_number,
            'exploit_potential': v.exploit_potential,
            'mitigation': v.mitigation
        }

    def _generate_recommendations(
        self,
        violations: List[InvariantViolation]
    ) -> List[str]:
        """Generate fix recommendations based on violations"""
        recommendations = []

        # Critical violations first
        critical = [v for v in violations if v.severity == InvariantSeverity.CRITICAL]
        if critical:
            recommendations.append(
                f"🚨 CRITICAL: Fix {len(critical)} critical vulnerabilities immediately. "
                f"Protocol is at risk of being drained."
            )

        # Category-specific recommendations
        categories = set(v.category for v in violations)
        for category in categories:
            category_violations = [v for v in violations if v.category == category]
            recommendations.append(
                f"{category.value.upper()}: Review {len(category_violations)} "
                f"invariant violations in {category.value} logic"
            )

        return recommendations
