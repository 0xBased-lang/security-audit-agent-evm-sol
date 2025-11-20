"""
Anvil Adapter (Foundry)

Default adapter using Foundry's Anvil for fast EVM simulation.
Best performance for standard EVM chains.
"""

import subprocess
import time
from typing import Optional, Dict, Any
from .base import SimulationAdapter

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False


class AnvilAdapter(SimulationAdapter):
    """
    Anvil (Foundry) simulation adapter

    Features:
    - Very fast execution
    - Mainnet forking
    - Full cheat code support
    - Best for standard EVM chains

    Supported chains:
    - Ethereum, Polygon, Arbitrum, Optimism, Base, BSC, Avalanche

    Requirements:
    - Foundry installed
    - web3.py
    """

    # Default RPC URLs for forking
    DEFAULT_RPC_URLS = {
        'ethereum': 'https://eth-mainnet.g.alchemy.com/v2/demo',
        'polygon': 'https://polygon-rpc.com',
        'arbitrum': 'https://arb1.arbitrum.io/rpc',
        'optimism': 'https://mainnet.optimism.io',
        'base': 'https://mainnet.base.org',
        'bsc': 'https://bsc-dataseed.binance.org',
        'avalanche': 'https://api.avax.network/ext/bc/C/rpc',
    }

    def __init__(
        self,
        chain: str,
        fork_block: Optional[int] = None,
        port: int = 8545,
        fork_url: Optional[str] = None
    ):
        super().__init__(chain, fork_block)

        if not WEB3_AVAILABLE:
            raise ImportError("web3.py required. Install: pip install web3")

        self.port = port
        self.fork_url = fork_url or self.DEFAULT_RPC_URLS.get(chain)

        if not self.fork_url:
            raise ValueError(
                f"No default RPC URL for {chain}. "
                f"Provide fork_url or set {chain.upper()}_RPC_URL env var"
            )

        self.anvil_process: Optional[subprocess.Popen] = None
        self.w3: Optional[Web3] = None

    def start(self):
        """Start Anvil process"""
        self.logger.info(f"Starting Anvil for {self.chain}...")

        cmd = [
            'anvil',
            '--port', str(self.port),
            '--accounts', '10',
            '--balance', '10000',
            '--fork-url', self.fork_url,
        ]

        if self.fork_block:
            cmd.extend(['--fork-block-number', str(self.fork_block)])

        try:
            self.anvil_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for Anvil to start
            time.sleep(2)

            if self.anvil_process.poll() is not None:
                raise RuntimeError("Anvil failed to start")

            # Connect Web3
            self.w3 = Web3(Web3.HTTPProvider(f"http://localhost:{self.port}"))

            if not self.w3.is_connected():
                raise RuntimeError("Failed to connect to Anvil")

            self.logger.info(f"✓ Anvil started (block={self.w3.eth.block_number})")

        except FileNotFoundError:
            raise RuntimeError(
                "Anvil not found. Install Foundry:\n"
                "  curl -L https://foundry.paradigm.xyz | bash && foundryup"
            )

    def stop(self):
        """Stop Anvil process"""
        if self.anvil_process:
            self.anvil_process.terminate()
            self.anvil_process.wait(timeout=5)
            self.anvil_process = None
            self.logger.info("Anvil stopped")

    def execute_transaction(
        self,
        to: str,
        data: str,
        value: int = 0,
        from_address: Optional[str] = None,
        gas_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute transaction"""

        if not from_address:
            from_address = self.w3.eth.accounts[0]

        tx = {
            'from': from_address,
            'to': to,
            'data': data,
            'value': value,
            'gas': gas_limit or 500000,
        }

        tx_hash = self.w3.eth.send_transaction(tx)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            'success': receipt['status'] == 1,
            'gas_used': receipt['gasUsed'],
            'transaction_hash': receipt['transactionHash'].hex(),
        }

    def get_balance(self, address: str) -> int:
        """Get ETH balance"""
        return self.w3.eth.get_balance(address)

    def get_storage_at(self, address: str, position: int) -> str:
        """Get storage slot"""
        return self.w3.eth.get_storage_at(address, position).hex()

    def get_block_number(self) -> int:
        """Get current block number"""
        return self.w3.eth.block_number

    def mine_blocks(self, num_blocks: int = 1):
        """Mine blocks"""
        for _ in range(num_blocks):
            self.w3.provider.make_request('evm_mine', [])

    def snapshot(self) -> int:
        """Create snapshot"""
        result = self.w3.provider.make_request('evm_snapshot', [])
        return result['result']

    def revert(self, snapshot_id: int):
        """Revert to snapshot"""
        self.w3.provider.make_request('evm_revert', [snapshot_id])

    def set_balance(self, address: str, balance: int):
        """Set balance (cheat code)"""
        self.w3.provider.make_request('anvil_setBalance', [address, hex(balance)])

    def impersonate_account(self, address: str):
        """Impersonate account"""
        self.w3.provider.make_request('anvil_impersonateAccount', [address])

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            'forking': True,
            'snapshots': True,
            'cheat_codes': True,
            'fast_execution': True,  # Anvil is very fast
            'custom_hardforks': False,
            'multi_chain': False,
        }
