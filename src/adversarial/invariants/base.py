"""
Base Invariant Classes

Defines the structure for protocol invariants.
"""

from typing import Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum


class InvariantSeverity(Enum):
    """Severity levels for invariant violations"""
    CRITICAL = "CRITICAL"  # Invariant violation = exploit
    HIGH = "HIGH"          # Likely leads to loss of funds
    MEDIUM = "MEDIUM"      # Could lead to issues under certain conditions
    LOW = "LOW"            # Edge case or informational


@dataclass
class InvariantViolation:
    """Represents a violation of an invariant"""
    invariant_name: str
    severity: InvariantSeverity
    description: str
    state_before: Any
    state_after: Any
    violating_action: Optional[Any] = None

    def __repr__(self):
        return (
            f"InvariantViolation({self.invariant_name}, "
            f"severity={self.severity.value})"
        )


class Invariant:
    """
    Protocol Invariant

    An invariant is a property that must always be true for a protocol
    to operate securely. Violations indicate potential exploits.

    Example:
        constant_product = Invariant(
            name="Constant Product",
            check_function=lambda state: (
                state.pool.reserve0 * state.pool.reserve1 >= state.pool.k
            ),
            severity=InvariantSeverity.CRITICAL,
            description="x * y >= k must hold for AMM"
        )

        # Check invariant
        if not constant_product.check(current_state):
            print("Invariant violated!")
    """

    def __init__(
        self,
        name: str,
        check_function: Callable[[Any], bool],
        severity: InvariantSeverity,
        description: str = "",
        category: str = "generic"
    ):
        """
        Initialize invariant

        Args:
            name: Invariant name
            check_function: Function that returns True if invariant holds
            severity: Severity level if violated
            description: Human-readable description
            category: Category (amm, lending, oracle, etc.)
        """
        self.name = name
        self.check_function = check_function
        self.severity = severity
        self.description = description
        self.category = category

    def check(self, state: Any) -> bool:
        """
        Check if invariant holds

        Args:
            state: Current environment state

        Returns:
            True if invariant holds, False if violated
        """
        try:
            return self.check_function(state)
        except Exception as e:
            # If check fails, treat as violation
            print(f"Invariant check failed: {self.name} - {e}")
            return False

    def create_violation(
        self,
        state_before: Any,
        state_after: Any,
        action: Optional[Any] = None
    ) -> InvariantViolation:
        """
        Create a violation record

        Args:
            state_before: State before violation
            state_after: State after violation
            action: Action that caused violation

        Returns:
            InvariantViolation instance
        """
        return InvariantViolation(
            invariant_name=self.name,
            severity=self.severity,
            description=self.description,
            state_before=state_before,
            state_after=state_after,
            violating_action=action
        )

    def __repr__(self):
        return f"Invariant({self.name}, severity={self.severity.value})"


class InvariantChecker:
    """
    Manages and checks multiple invariants

    Example:
        checker = InvariantChecker()
        checker.add_invariants(AMM_INVARIANTS)
        checker.add_invariants(LENDING_INVARIANTS)

        violations = checker.check_all(current_state)
        if violations:
            print(f"Found {len(violations)} violations!")
    """

    def __init__(self):
        self.invariants: list[Invariant] = []

    def add_invariant(self, invariant: Invariant):
        """Add an invariant to check"""
        self.invariants.append(invariant)

    def add_invariants(self, invariants: list[Invariant]):
        """Add multiple invariants"""
        self.invariants.extend(invariants)

    def check_all(self, state: Any) -> list[Invariant]:
        """
        Check all invariants

        Args:
            state: Current environment state

        Returns:
            List of violated invariants
        """
        violations = []

        for invariant in self.invariants:
            if not invariant.check(state):
                violations.append(invariant)

        return violations

    def check_by_category(self, state: Any, category: str) -> list[Invariant]:
        """
        Check invariants in a specific category

        Args:
            state: Current environment state
            category: Category to check

        Returns:
            List of violated invariants in category
        """
        violations = []

        for invariant in self.invariants:
            if invariant.category == category and not invariant.check(state):
                violations.append(invariant)

        return violations

    def get_critical_violations(self, state: Any) -> list[Invariant]:
        """Get only critical invariant violations"""
        violations = self.check_all(state)
        return [
            inv for inv in violations
            if inv.severity == InvariantSeverity.CRITICAL
        ]

    def __len__(self):
        return len(self.invariants)

    def __repr__(self):
        return f"InvariantChecker({len(self.invariants)} invariants)"
