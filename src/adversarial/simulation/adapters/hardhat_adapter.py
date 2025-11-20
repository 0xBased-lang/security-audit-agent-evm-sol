"""
Hardhat Adapter

For custom EVM chains and special configurations.
Supports any EVM-compatible chain with proper hardhat config.
"""

import subprocess
import time
import os
from typing import Optional, Dict, Any
from .base import SimulationAdapter

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False


class HardhatAdapter(SimulationAdapter):
    """
    Hardhat simulation adapter

    Features:
    - Custom EVM chain support
    - Hardfork configuration
    - Good for unusual chains

    Requirements:
    - Node.js and npm
    - Hardhat installed
    - hardhat.config.js with chain config

    Example hardhat.config.js:
        module.exports = {
          networks: {
            hardhat: {
              forking: {
                url: "https://your-chain-rpc.com",
                blockNumber: 1234567
              },
              chains: {
                12345: {
                  hardforkHistory: {
                    london: 100000,
                    paris: 200000,
                  }
                }
              }
            }
          }
        };
    """

    def __init__(
        self,
        chain: str,
        fork_block: Optional[int] = None,
        port: int = 8545,
        project_dir: str = '.'
    ):
        super().__init__(chain, fork_block)

        if not WEB3_AVAILABLE:
            raise ImportError("web3.py required. Install: pip install web3")

        self.port = port
        self.project_dir = project_dir
        self.hardhat_process: Optional[subprocess.Popen] = None
        self.w3: Optional[Web3] = None

    def start(self):
        """Start Hardhat node"""
        self.logger.info(f"Starting Hardhat for {self.chain}...")

        # Check Hardhat is installed
        if not self._check_hardhat_installed():
            raise RuntimeError(
                "Hardhat not found. Install:\n"
                "  npm install --save-dev hardhat"
            )

        # Start Hardhat node
        cmd = ['npx', 'hardhat', 'node', '--port', str(self.port)]

        try:
            self.hardhat_process = subprocess.Popen(
                cmd,
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for Hardhat to start
            time.sleep(5)

            if self.hardhat_process.poll() is not None:
                raise RuntimeError("Hardhat node failed to start")

            # Connect Web3
            self.w3 = Web3(Web3.HTTPProvider(f"http://localhost:{self.port}"))

            if not self.w3.is_connected():
                raise RuntimeError("Failed to connect to Hardhat")

            self.logger.info(f"✓ Hardhat started (block={self.w3.eth.block_number})")

        except FileNotFoundError:
            raise RuntimeError(
                "npx not found. Install Node.js and npm"
            )

    def stop(self):
        """Stop Hardhat node"""
        if self.hardhat_process:
            self.hardhat_process.terminate()
            self.hardhat_process.wait(timeout=5)
            self.hardhat_process = None
            self.logger.info("Hardhat stopped")

    def _check_hardhat_installed(self) -> bool:
        """Check if Hardhat is installed"""
        return os.path.exists(
            os.path.join(self.project_dir, 'node_modules', '.bin', 'hardhat')
        )

    # Implement same interface as Anvil
    def execute_transaction(self, to, data, value=0, from_address=None, gas_limit=None):
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
        return self.w3.eth.get_balance(address)

    def get_storage_at(self, address: str, position: int) -> str:
        return self.w3.eth.get_storage_at(address, position).hex()

    def get_block_number(self) -> int:
        return self.w3.eth.block_number

    def mine_blocks(self, num_blocks: int = 1):
        for _ in range(num_blocks):
            self.w3.provider.make_request('evm_mine', [])

    def snapshot(self) -> int:
        result = self.w3.provider.make_request('evm_snapshot', [])
        return result['result']

    def revert(self, snapshot_id: int):
        self.w3.provider.make_request('evm_revert', [snapshot_id])

    def set_balance(self, address: str, balance: int):
        self.w3.provider.make_request('hardhat_setBalance', [address, hex(balance)])

    def impersonate_account(self, address: str):
        self.w3.provider.make_request('hardhat_impersonateAccount', [address])

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            'forking': True,
            'snapshots': True,
            'cheat_codes': True,
            'fast_execution': False,  # Slower than Anvil
            'custom_hardforks': True,  # Main advantage
            'multi_chain': False,
        }
