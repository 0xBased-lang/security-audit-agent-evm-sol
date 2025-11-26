"""
Base Simulation Adapter Interface

Abstract interface that all simulation adapters must implement.
This allows seamless switching between different simulation backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging
import os


class UnsupportedChainError(Exception):
    """Raised when no adapter supports the requested chain"""
    pass


class SimulationAdapter(ABC):
    """
    Abstract base class for simulation adapters

    Each adapter provides blockchain simulation for specific chains/use cases:
    - AnvilAdapter: Foundry-supported EVM chains (fast, production-ready)
    - HardhatAdapter: Custom EVM chains with special configs
    - REVMAdapter: Direct Rust integration, maximum control
    - TenderlyAdapter: 90+ chains via commercial service
    - DirectRPCAdapter: Fallback for any chain with RPC
    """

    def __init__(self, chain: str, fork_block: Optional[int] = None):
        """
        Initialize adapter

        Args:
            chain: Chain identifier (ethereum, polygon, arbitrum, etc.)
            fork_block: Block number to fork from (None for latest)
        """
        self.chain = chain
        self.fork_block = fork_block
        self.logger = logging.getLogger(f"{__name__}.{chain}")

    @abstractmethod
    def start(self):
        """Start the simulation environment"""
        pass

    @abstractmethod
    def stop(self):
        """Stop the simulation environment"""
        pass

    @abstractmethod
    def execute_transaction(
        self,
        to: str,
        data: str,
        value: int = 0,
        from_address: Optional[str] = None,
        gas_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a transaction

        Args:
            to: Destination address
            data: Transaction data (encoded function call)
            value: ETH value to send
            from_address: Sender address
            gas_limit: Gas limit

        Returns:
            Transaction receipt
        """
        pass

    @abstractmethod
    def get_balance(self, address: str) -> int:
        """Get ETH balance of address"""
        pass

    @abstractmethod
    def get_storage_at(self, address: str, position: int) -> str:
        """Get storage slot value"""
        pass

    @abstractmethod
    def get_block_number(self) -> int:
        """Get current block number"""
        pass

    @abstractmethod
    def mine_blocks(self, num_blocks: int = 1):
        """Mine blocks"""
        pass

    @abstractmethod
    def snapshot(self) -> int:
        """Create state snapshot"""
        pass

    @abstractmethod
    def revert(self, snapshot_id: int):
        """Revert to snapshot"""
        pass

    @abstractmethod
    def set_balance(self, address: str, balance: int):
        """Set balance (cheat code)"""
        pass

    @abstractmethod
    def impersonate_account(self, address: str):
        """Impersonate account (cheat code)"""
        pass

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get adapter capabilities

        Returns:
            Dictionary of supported features
        """
        return {
            'forking': True,
            'snapshots': True,
            'cheat_codes': True,
            'fast_execution': False,
            'custom_hardforks': False,
            'multi_chain': False,
        }

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# Supported chains by adapter
ANVIL_SUPPORTED = [
    'ethereum',
    'polygon',
    'arbitrum',
    'optimism',
    'base',
    'bsc',
    'avalanche',
]

HARDHAT_SUPPORTED = [
    *ANVIL_SUPPORTED,  # All Anvil chains
    'custom_evm',  # Any EVM with config
    'moonbeam',
    'moonriver',
]

TENDERLY_SUPPORTED = [
    # 90+ chains - partial list
    *ANVIL_SUPPORTED,
    'linea',
    'scroll',
    'zksync',
    'starknet',
    'mantle',
    'celo',
    'gnosis',
    'aurora',
    'fantom',
    # ... many more
]


def select_adapter(
    chain: str,
    fork_block: Optional[int] = None,
    prefer: Optional[str] = None
) -> SimulationAdapter:
    """
    Auto-select best adapter for chain

    Selection logic:
    1. If prefer specified, use that
    2. If Anvil supports → use Anvil (fastest)
    3. If Tenderly key available and supports → use Tenderly
    4. If Hardhat custom config available → use Hardhat
    5. If RPC endpoint available → use DirectRPC
    6. Raise UnsupportedChainError

    Args:
        chain: Chain identifier
        fork_block: Block number to fork
        prefer: Preferred adapter ('anvil', 'hardhat', 'tenderly', 'revm', 'rpc')

    Returns:
        Configured SimulationAdapter

    Raises:
        UnsupportedChainError: If no adapter supports the chain
    """

    logger = logging.getLogger(__name__)

    # Manual preference
    if prefer:
        adapter_map = {
            'anvil': AnvilAdapter,
            'hardhat': HardhatAdapter,
            'revm': REVMAdapter,
            'tenderly': TenderlyAdapter,
            'rpc': DirectRPCAdapter,
        }

        if prefer not in adapter_map:
            raise ValueError(f"Unknown adapter: {prefer}")

        logger.info(f"Using preferred adapter: {prefer}")
        return adapter_map[prefer](chain, fork_block)

    # Auto-selection

    # 1. Anvil (fastest, best for standard EVM chains)
    if chain in ANVIL_SUPPORTED:
        logger.info(f"Auto-selected Anvil adapter for {chain}")
        from .anvil_adapter import AnvilAdapter
        return AnvilAdapter(chain, fork_block)

    # 2. Tenderly (if API key available)
    if chain in TENDERLY_SUPPORTED and _has_tenderly_key():
        logger.info(f"Auto-selected Tenderly adapter for {chain}")
        from .tenderly_adapter import TenderlyAdapter
        return TenderlyAdapter(chain, fork_block)

    # 3. Hardhat (if custom config available)
    if _has_hardhat_config(chain):
        logger.info(f"Auto-selected Hardhat adapter for {chain}")
        from .hardhat_adapter import HardhatAdapter
        return HardhatAdapter(chain, fork_block)

    # 4. DirectRPC (if RPC endpoint available)
    if _has_rpc_endpoint(chain):
        logger.info(f"Auto-selected DirectRPC adapter for {chain}")
        from .direct_rpc_adapter import DirectRPCAdapter
        return DirectRPCAdapter(chain, fork_block)

    # No adapter found
    raise UnsupportedChainError(
        f"No adapter available for chain: {chain}\n"
        f"Supported chains: {ANVIL_SUPPORTED}\n"
        f"Try:\n"
        f"  1. Use Tenderly (set TENDERLY_API_KEY)\n"
        f"  2. Add Hardhat config for {chain}\n"
        f"  3. Provide RPC endpoint in config\n"
        f"  4. Use a supported chain"
    )


def _has_tenderly_key() -> bool:
    """Check if Tenderly API key is configured"""
    return bool(os.environ.get('TENDERLY_API_KEY') or
                os.environ.get('TENDERLY_ACCESS_KEY'))


def _has_hardhat_config(chain: str) -> bool:
    """Check if Hardhat config exists for chain"""
    # SECURITY FIX: Validate chain name to prevent injection
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
        from src.security.validators import ChainValidator
        validated_chain = ChainValidator.validate_chain_name(chain)
    except Exception:
        # If validation fails, chain is not supported
        return False

    # Check for hardhat.config.js with chain config
    import os.path
    config_path = os.path.abspath('hardhat.config.js')

    # Ensure config file is in current directory (not traversal)
    if not config_path.startswith(os.getcwd()):
        return False

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                return validated_chain in content
        except Exception as e:
            logging.getLogger(__name__).warning(
                f"Failed to read hardhat config: {e}"
            )
            pass
    return False


def _has_rpc_endpoint(chain: str) -> bool:
    """Check if RPC endpoint is configured"""
    # SECURITY FIX: Validate chain name before using in environment variable
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
        from src.security.validators import ChainValidator
        validated_chain = ChainValidator.validate_chain_name(chain)
    except Exception:
        # If validation fails, chain is not supported
        return False

    # Check environment variables with validated chain name
    rpc_key = f"{validated_chain.upper()}_RPC_URL"
    return bool(os.environ.get(rpc_key))


__all__ = ['SimulationAdapter', 'select_adapter', 'UnsupportedChainError']
