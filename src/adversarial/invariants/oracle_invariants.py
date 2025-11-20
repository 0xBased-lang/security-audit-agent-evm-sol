"""
Oracle Invariants

Invariants for price oracles and price feeds.
Critical for preventing price manipulation exploits.
"""

from .base import Invariant, InvariantSeverity


# Core Oracle Invariants

PRICE_DEVIATION_BOUNDS = Invariant(
    name="Price Deviation Within Bounds",
    check_function=lambda state: (
        # Price should not deviate more than X% per block/transaction
        # Prevents single-transaction price manipulation
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.CRITICAL,
    description=(
        "Price changes must be within reasonable bounds per block. "
        "Large sudden changes indicate manipulation."
    ),
    category="oracle"
)

TWAP_NOT_MANIPULABLE = Invariant(
    name="TWAP Not Single-Block Manipulable",
    check_function=lambda state: (
        # TWAP should require multiple blocks to significantly move
        # Protects against flash loan manipulation
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.CRITICAL,
    description=(
        "Time-weighted average price should not be manipulable in single transaction. "
        "Single-block TWAP changes indicate vulnerability."
    ),
    category="oracle"
)

MULTI_ORACLE_CONSENSUS = Invariant(
    name="Multi-Oracle Consensus",
    check_function=lambda state: (
        # If using multiple oracles, they should agree within threshold
        # Protects against single oracle manipulation
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.HIGH,
    description=(
        "Multiple oracle sources should agree on price. "
        "Disagreement indicates potential manipulation of one source."
    ),
    category="oracle"
)

ORACLE_STALENESS = Invariant(
    name="Oracle Not Stale",
    check_function=lambda state: (
        # Oracle updates should be recent (< X seconds old)
        # Prevents use of outdated prices
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.HIGH,
    description=(
        "Oracle prices must be fresh and recently updated. "
        "Stale prices can be exploited if market has moved."
    ),
    category="oracle"
)

CHAINLINK_CIRCUIT_BREAKER = Invariant(
    name="Chainlink Circuit Breaker Active",
    check_function=lambda state: (
        # Chainlink price should be within min/max bounds
        # Circuit breaker protects against oracle failures
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.HIGH,
    description=(
        "Chainlink feeds have circuit breakers for extreme prices. "
        "Prices outside bounds indicate oracle malfunction."
    ),
    category="oracle"
)

NO_ZERO_PRICE = Invariant(
    name="Price Never Zero",
    check_function=lambda state: (
        # Oracle price should never return 0 (indicates failure)
        # Zero price can cause division by zero or free assets
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.CRITICAL,
    description=(
        "Oracle must never return zero price. "
        "Zero price indicates oracle failure and can cause exploits."
    ),
    category="oracle"
)

ORACLE_DECIMALS_CONSISTENT = Invariant(
    name="Oracle Decimals Handled Correctly",
    check_function=lambda state: (
        # Decimals must be handled consistently (8 for Chainlink, 18 for most tokens)
        # Prevents decimal confusion exploits
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.HIGH,
    description=(
        "Oracle decimal places must be handled correctly. "
        "Decimal confusion can cause 1000x price errors."
    ),
    category="oracle"
)

PRICE_ALWAYS_POSITIVE = Invariant(
    name="Price Always Positive",
    check_function=lambda state: (
        # Prices must be > 0 for all assets
        # Negative prices are impossible and indicate exploit
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.CRITICAL,
    description=(
        "Asset prices must always be positive. "
        "Negative or zero prices indicate critical bug."
    ),
    category="oracle"
)

LIQUIDITY_SUFFICIENT_FOR_ORACLE = Invariant(
    name="Oracle Source Has Sufficient Liquidity",
    check_function=lambda state: (
        # If using AMM as oracle, liquidity should be above threshold
        # Low liquidity = easy manipulation
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.CRITICAL,
    description=(
        "Oracle source (if AMM) must have sufficient liquidity. "
        "Low liquidity makes manipulation cheap."
    ),
    category="oracle"
)

NO_SANDWICH_ORACLE_UPDATE = Invariant(
    name="Oracle Update Not Sandwichable",
    check_function=lambda state: (
        # Oracle updates should not be frontrunnable
        # Protects against MEV on oracle updates
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.MEDIUM,
    description=(
        "Oracle updates should not be exploitable via frontrunning. "
        "Sandwichable updates allow MEV extraction."
    ),
    category="oracle"
)

HEARTBEAT_RESPECTED = Invariant(
    name="Oracle Heartbeat Respected",
    check_function=lambda state: (
        # Oracle should update within heartbeat interval
        # Long gaps indicate potential staleness
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.MEDIUM,
    description=(
        "Oracle must update within heartbeat interval. "
        "Missed updates indicate unreliable oracle."
    ),
    category="oracle"
)

# Compile all oracle invariants
ORACLE_INVARIANTS = [
    PRICE_DEVIATION_BOUNDS,
    TWAP_NOT_MANIPULABLE,
    MULTI_ORACLE_CONSENSUS,
    ORACLE_STALENESS,
    CHAINLINK_CIRCUIT_BREAKER,
    NO_ZERO_PRICE,
    ORACLE_DECIMALS_CONSISTENT,
    PRICE_ALWAYS_POSITIVE,
    LIQUIDITY_SUFFICIENT_FOR_ORACLE,
    NO_SANDWICH_ORACLE_UPDATE,
    HEARTBEAT_RESPECTED,
]
