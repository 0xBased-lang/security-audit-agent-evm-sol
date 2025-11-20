"""
REVM Adapter (Phase 2+)

Direct Rust EVM integration for maximum control and performance.

Status: Stub implementation - to be completed in Phase 2
"""

from typing import Optional, Dict, Any
from .base import SimulationAdapter


class REVMAdapter(SimulationAdapter):
    """
    REVM (Rust EVM) adapter

    Phase 2+ Feature

    Will provide:
    - Direct Rust integration
    - Maximum performance (60% faster than ethers-rs)
    - Full control over execution
    - Custom precompiles and opcodes

    Requirements (future):
    - Rust toolchain
    - REVM crate
    - PyO3 bindings

    Example usage (future):
        adapter = REVMAdapter('ethereum', fork_block=18500000)
        adapter.start()

        # Direct EVM execution
        result = adapter.execute_bytecode(bytecode, calldata)
    """

    def __init__(self, chain: str, fork_block: Optional[int] = None):
        super().__init__(chain, fork_block)

        raise NotImplementedError(
            "REVM adapter is a Phase 2+ feature.\n"
            "\n"
            "Planned capabilities:\n"
            "- Direct Rust EVM execution (60% faster)\n"
            "- Custom opcode support\n"
            "- Full EVM control\n"
            "\n"
            "For now, use:\n"
            "- AnvilAdapter (fastest, standard EVM chains)\n"
            "- HardhatAdapter (custom EVM chains)\n"
            "- DirectRPCAdapter (any chain with RPC)\n"
            "\n"
            "See docs/MLSS_ARCHITECTURE_PART1.md for roadmap"
        )

    def start(self):
        raise NotImplementedError("Phase 2+ feature")

    def stop(self):
        pass

    def execute_transaction(self, to, data, value=0, from_address=None, gas_limit=None):
        raise NotImplementedError("Phase 2+ feature")

    def get_balance(self, address):
        raise NotImplementedError("Phase 2+ feature")

    def get_storage_at(self, address, position):
        raise NotImplementedError("Phase 2+ feature")

    def get_block_number(self):
        raise NotImplementedError("Phase 2+ feature")

    def mine_blocks(self, num_blocks=1):
        raise NotImplementedError("Phase 2+ feature")

    def snapshot(self):
        raise NotImplementedError("Phase 2+ feature")

    def revert(self, snapshot_id):
        raise NotImplementedError("Phase 2+ feature")

    def set_balance(self, address, balance):
        raise NotImplementedError("Phase 2+ feature")

    def impersonate_account(self, address):
        raise NotImplementedError("Phase 2+ feature")
