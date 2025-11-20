"""
Direct RPC Adapter

Fallback adapter for any chain with an RPC endpoint.
No forking, but can execute against live chain or local node.
"""

import os
from typing import Optional, Dict, Any
from .base import SimulationAdapter

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False


class DirectRPCAdapter(SimulationAdapter):
    """
    Direct RPC adapter

    Features:
    - Works with ANY chain that has RPC endpoint
    - No special setup required
    - Fallback option when other adapters don't work

    Limitations:
    - No forking (executes against live chain or local node)
    - Limited cheat code support
    - Slower than local simulation

    Requirements:
    - RPC endpoint URL
    - web3.py

    Usage:
        Set environment variable: {CHAIN}_RPC_URL
        Example: ETHEREUM_RPC_URL=https://eth.llamarpc.com

        Or provide rpc_url parameter directly
    """

    def __init__(
        self,
        chain: str,
        fork_block: Optional[int] = None,
        rpc_url: Optional[str] = None
    ):
        super().__init__(chain, fork_block)

        if not WEB3_AVAILABLE:
            raise ImportError("web3.py required. Install: pip install web3")

        # Get RPC URL from env or parameter
        env_key = f"{chain.upper()}_RPC_URL"
        self.rpc_url = rpc_url or os.environ.get(env_key)

        if not self.rpc_url:
            raise ValueError(
                f"No RPC URL for {chain}. "
                f"Set {env_key} environment variable or provide rpc_url parameter"
            )

        self.w3: Optional[Web3] = None

        if fork_block:
            self.logger.warning(
                "fork_block parameter ignored by DirectRPC adapter. "
                "Adapter connects to live chain/node."
            )

    def start(self):
        """Connect to RPC endpoint"""
        self.logger.info(f"Connecting to {self.chain} via RPC...")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        if not self.w3.is_connected():
            raise RuntimeError(f"Failed to connect to {self.rpc_url}")

        block_number = self.w3.eth.block_number
        chain_id = self.w3.eth.chain_id

        self.logger.info(
            f"✓ Connected to {self.chain} "
            f"(block={block_number}, chain_id={chain_id})"
        )

    def stop(self):
        """Disconnect from RPC (no-op)"""
        self.w3 = None
        self.logger.info("Disconnected from RPC")

    def execute_transaction(
        self,
        to: str,
        data: str,
        value: int = 0,
        from_address: Optional[str] = None,
        gas_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute transaction

        Note: This sends REAL transactions to the chain!
        Be careful when using DirectRPC adapter.
        """

        if not from_address:
            # DirectRPC can't create accounts like Anvil
            raise ValueError(
                "from_address required for DirectRPC adapter. "
                "Provide account with funds."
            )

        tx = {
            'from': from_address,
            'to': to,
            'data': data,
            'value': value,
            'gas': gas_limit or 500000,
        }

        # NOTE: This sends a REAL transaction!
        # In production, you'd want dry-run mode or confirmation
        self.logger.warning(f"Sending REAL transaction to {self.chain}!")

        tx_hash = self.w3.eth.send_transaction(tx)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            'success': receipt['status'] == 1,
            'gas_used': receipt['gasUsed'],
            'transaction_hash': receipt['transactionHash'].hex(),
        }

    def get_balance(self, address: str) -> int:
        return self.w3.eth.get_balance(address)

    def get_storage_at(self, address: str, position: int) -> str:
        return self.w3.eth.get_storage_at(address, position).hex()

    def get_block_number(self) -> int:
        return self.w3.eth.block_number

    def mine_blocks(self, num_blocks: int = 1):
        """Not supported - chain mines naturally"""
        raise NotImplementedError(
            "mine_blocks not supported by DirectRPC adapter. "
            "Chain mines blocks naturally."
        )

    def snapshot(self) -> int:
        """Not supported - no state manipulation"""
        raise NotImplementedError(
            "Snapshots not supported by DirectRPC adapter. "
            "Use Anvil or Hardhat for testing."
        )

    def revert(self, snapshot_id: int):
        """Not supported"""
        raise NotImplementedError(
            "Snapshots not supported by DirectRPC adapter"
        )

    def set_balance(self, address: str, balance: int):
        """Not supported - can't manipulate live chain"""
        raise NotImplementedError(
            "Cheat codes not supported by DirectRPC adapter. "
            "Use Anvil or Hardhat for testing."
        )

    def impersonate_account(self, address: str):
        """Not supported"""
        raise NotImplementedError(
            "Cheat codes not supported by DirectRPC adapter"
        )

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            'forking': False,  # No forking, connects to live chain
            'snapshots': False,
            'cheat_codes': False,
            'fast_execution': False,  # Network latency
            'custom_hardforks': False,
            'multi_chain': True,  # Works with any chain!
        }
