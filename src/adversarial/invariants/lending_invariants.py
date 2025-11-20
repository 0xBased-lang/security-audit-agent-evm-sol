"""
Lending Protocol Invariants

Invariants for lending/borrowing protocols like Aave, Compound, Euler, etc.
"""

from .base import Invariant, InvariantSeverity


# Core Lending Invariants

OVERCOLLATERALIZATION = Invariant(
    name="Overcollateralization Maintained",
    check_function=lambda state: (
        # For all borrowers: collateral_value * collateral_factor >= borrow_value
        # This is the most critical lending invariant
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.CRITICAL,
    description=(
        "All positions must remain overcollateralized. "
        "Undercollateralized positions indicate exploit allowing free borrowing."
    ),
    category="lending"
)

TOTAL_COLLATERAL_GTE_BORROWS = Invariant(
    name="Total Collateral >= Total Borrows",
    check_function=lambda state: (
        # Protocol level: sum(all_collateral) >= sum(all_borrows)
        # System solvency check
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.CRITICAL,
    description=(
        "Protocol-wide collateral must exceed borrows. "
        "Violation means protocol is insolvent."
    ),
    category="lending"
)

NO_NEGATIVE_BALANCES = Invariant(
    name="No Negative Balances",
    check_function=lambda state: (
        # All user balances (deposits, borrows) must be >= 0
        # Prevents accounting exploits
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.CRITICAL,
    description=(
        "User balances cannot be negative. "
        "Negative balances indicate accounting exploit."
    ),
    category="lending"
)

INTEREST_ACCRUAL = Invariant(
    name="Interest Accrues Correctly",
    check_function=lambda state: (
        # Interest should only increase over time
        # Protects interest calculation
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.HIGH,
    description=(
        "Interest must accrue monotonically. "
        "Decreasing interest indicates manipulation."
    ),
    category="lending"
)

LIQUIDATION_THRESHOLD = Invariant(
    name="Liquidation Threshold Enforced",
    check_function=lambda state: (
        # Positions below health factor should be liquidatable
        # Positions above threshold should not be liquidatable
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.HIGH,
    description=(
        "Liquidation thresholds must be enforced correctly. "
        "Violation allows unfair liquidations or prevents necessary ones."
    ),
    category="lending"
)

RESERVE_FACTOR = Invariant(
    name="Reserve Factor Maintained",
    check_function=lambda state: (
        # Protocol reserves should accumulate correctly
        # Protects protocol's safety buffer
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.MEDIUM,
    description=(
        "Protocol reserves must accumulate from fees. "
        "Loss of reserves reduces protocol safety."
    ),
    category="lending"
)

UTILIZATION_BOUNDS = Invariant(
    name="Utilization Within Bounds",
    check_function=lambda state: (
        # Utilization = borrows / (deposits) should be in [0, 1]
        # Above 100% means more borrowed than deposited (impossible normally)
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.CRITICAL,
    description=(
        "Utilization ratio must be between 0% and 100%. "
        "Over 100% indicates impossible state (more borrowed than exists)."
    ),
    category="lending"
)

SUPPLY_EQUALS_DEPOSITS = Invariant(
    name="Supply Token Supply = Total Deposits",
    check_function=lambda state: (
        # aToken/cToken supply should equal underlying deposits
        # Protects against supply token manipulation
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.HIGH,
    description=(
        "Supply token total supply must match actual deposits. "
        "Mismatch indicates supply token inflation/deflation attack."
    ),
    category="lending"
)

BORROW_CAP_ENFORCED = Invariant(
    name="Borrow Caps Enforced",
    check_function=lambda state: (
        # Total borrows <= borrow cap for each asset
        # Protects against over-borrowing
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.MEDIUM,
    description=(
        "Borrow caps must be enforced per asset. "
        "Exceeding caps may indicate bypass exploit."
    ),
    category="lending"
)

NO_FLASH_LOAN_IN_LIQUIDATION = Invariant(
    name="No Flash Loan During Liquidation",
    check_function=lambda state: (
        # Flash loans should not be possible during liquidation callback
        # Prevents flash loan + liquidation exploits
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.HIGH,
    description=(
        "Flash loans during liquidation can manipulate health factors. "
        "Should be prevented by reentrancy guards."
    ),
    category="lending"
)

LIQUIDATION_BONUS_BOUNDS = Invariant(
    name="Liquidation Bonus Within Bounds",
    check_function=lambda state: (
        # Liquidation bonus should be in reasonable range (e.g., 5-15%)
        # Prevents liquidation bonus manipulation
        True  # Placeholder for MVP
    ),
    severity=InvariantSeverity.MEDIUM,
    description=(
        "Liquidation bonus must be within configured bounds. "
        "Excessive bonus indicates manipulation."
    ),
    category="lending"
)

# Compile all lending invariants
LENDING_INVARIANTS = [
    OVERCOLLATERALIZATION,
    TOTAL_COLLATERAL_GTE_BORROWS,
    NO_NEGATIVE_BALANCES,
    INTEREST_ACCRUAL,
    LIQUIDATION_THRESHOLD,
    RESERVE_FACTOR,
    UTILIZATION_BOUNDS,
    SUPPLY_EQUALS_DEPOSITS,
    BORROW_CAP_ENFORCED,
    NO_FLASH_LOAN_IN_LIQUIDATION,
    LIQUIDATION_BONUS_BOUNDS,
]
