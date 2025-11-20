"""
Attack Strategy Templates

Parameterized attack patterns for adversarial testing.
"""

from .base import StrategyTemplate, StrategyResult
from .sandwich import SandwichAttack
from .oracle_manipulation import OracleManipulation
from .flash_loan import FlashLoanAttack

__all__ = [
    'StrategyTemplate',
    'StrategyResult',
    'SandwichAttack',
    'OracleManipulation',
    'FlashLoanAttack',
]
