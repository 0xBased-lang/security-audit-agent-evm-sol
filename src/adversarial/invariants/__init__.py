"""
Protocol Invariant Definitions

Invariants are properties that must always hold true for a protocol
to be considered secure. Violations indicate potential exploits.
"""

from .base import Invariant, InvariantViolation
from .amm_invariants import AMM_INVARIANTS
from .lending_invariants import LENDING_INVARIANTS
from .oracle_invariants import ORACLE_INVARIANTS

__all__ = [
    'Invariant',
    'InvariantViolation',
    'AMM_INVARIANTS',
    'LENDING_INVARIANTS',
    'ORACLE_INVARIANTS',
]
