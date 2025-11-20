"""
Multi-Chain Simulation Adapters

Provides support for ANY blockchain through pluggable adapters.

Supported:
- Anvil (Foundry) - Default, best performance
- Hardhat - Custom EVM chains
- REVM - Direct Rust integration
- Tenderly - 90+ chains (commercial)
- DirectRPC - Any chain with RPC endpoint (fallback)

Usage:
    adapter = select_adapter(chain='ethereum')
    env = EVMEnvironment(adapter=adapter)
"""

from .base import SimulationAdapter, select_adapter
from .anvil_adapter import AnvilAdapter
from .hardhat_adapter import HardhatAdapter
from .revm_adapter import REVMAdapter
from .tenderly_adapter import TenderlyAdapter
from .direct_rpc_adapter import DirectRPCAdapter

__all__ = [
    'SimulationAdapter',
    'select_adapter',
    'AnvilAdapter',
    'HardhatAdapter',
    'REVMAdapter',
    'TenderlyAdapter',
    'DirectRPCAdapter',
]
