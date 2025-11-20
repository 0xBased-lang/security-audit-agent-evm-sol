"""
EVM Simulation Environment

High-fidelity Ethereum simulation environment for adversarial testing.
Uses Foundry Anvil for mainnet forking and REVM for performance.
"""

import subprocess
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from decimal import Decimal

try:
    from web3 import Web3
    from web3.contract import Contract
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    Web3 = None
    Contract = None
    Account = None


class ActionType(Enum):
    """Types of actions available in the environment"""
    SWAP = "swap"
    BORROW = "borrow"
    REPAY = "repay"
    LIQUIDATE = "liquidate"
    FLASH_LOAN = "flash_loan"
    ADD_LIQUIDITY = "add_liquidity"
    REMOVE_LIQUIDITY = "remove_liquidity"
    MINT = "mint"
    BURN = "burn"
    TRANSFER = "transfer"


@dataclass
class EnvironmentState:
    """Current state of the simulation environment"""
    block_number: int
    timestamp: int
    balances: Dict[str, Dict[str, int]] = field(default_factory=dict)  # account -> token -> balance
    pool_reserves: Dict[str, Dict[str, int]] = field(default_factory=dict)  # pool -> token -> reserve
    borrowing_state: Dict[str, Any] = field(default_factory=dict)  # protocol -> state
    total_gas_used: int = 0
    total_value_extracted: Decimal = Decimal(0)

    def clone(self) -> 'EnvironmentState':
        """Create a deep copy of the state"""
        import copy
        return copy.deepcopy(self)


@dataclass
class Action:
    """An action to be executed in the environment"""
    action_type: ActionType
    parameters: Dict[str, Any]
    from_address: Optional[str] = None
    gas_limit: int = 500000

    def __repr__(self):
        return f"Action({self.action_type.value}, {self.parameters})"


@dataclass
class ActionResult:
    """Result of executing an action"""
    success: bool
    gas_used: int
    profit: Decimal
    state_changes: Dict[str, Any]
    error: Optional[str] = None
    transaction_hash: Optional[str] = None

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"ActionResult({status}, profit={self.profit}, gas={self.gas_used})"


class EVMEnvironment:
    """
    EVM Simulation Environment

    Provides a high-fidelity simulation environment for testing adversarial
    strategies against DeFi protocols.

    Features:
    - Mainnet forking at specific blocks
    - High-level DeFi actions (swap, borrow, flash loan, etc.)
    - State tracking and snapshots
    - Invariant checking
    - Gas and profit calculation

    Example:
        env = EVMEnvironment(
            project_path='./contracts',
            fork_block=18500000
        )
        env.start()

        # Execute a swap
        result = env.execute_action(Action(
            action_type=ActionType.SWAP,
            parameters={
                'pool': '0x...',
                'token_in': 'USDC',
                'token_out': 'ETH',
                'amount_in': 1000000
            }
        ))
    """

    def __init__(
        self,
        project_path: str,
        fork_block: Optional[int] = None,
        fork_url: str = "https://eth-mainnet.g.alchemy.com/v2/demo",
        port: int = 8545,
        chain_id: int = 1
    ):
        """
        Initialize EVM environment

        Args:
            project_path: Path to the project contracts
            fork_block: Block number to fork from (None for latest)
            fork_url: RPC URL for forking (default: Alchemy demo)
            port: Port for Anvil instance
            chain_id: Chain ID for the network
        """
        if not WEB3_AVAILABLE:
            raise ImportError(
                "web3.py is required for EVM simulation. "
                "Install with: pip install web3"
            )

        self.project_path = project_path
        self.fork_block = fork_block
        self.fork_url = fork_url
        self.port = port
        self.chain_id = chain_id

        self.logger = logging.getLogger(__name__)

        # Anvil process
        self.anvil_process: Optional[subprocess.Popen] = None
        self.w3: Optional[Web3] = None

        # Accounts
        self.accounts: List[str] = []
        self.attacker_account: Optional[str] = None

        # State
        self.current_state: Optional[EnvironmentState] = None
        self.state_history: List[EnvironmentState] = []
        self.snapshots: Dict[str, int] = {}  # name -> snapshot_id

        # Contracts
        self.contracts: Dict[str, Contract] = {}
        self.protocol_addresses: Dict[str, str] = {}

        # Invariants
        self.invariants: List[Any] = []

        # Configuration
        self.gas_price = Web3.to_wei(50, 'gwei') if Web3 else 50000000000
        self.eth_price_usd = Decimal(2000)  # Default ETH price for profit calculation

    def start(self):
        """Start the simulation environment"""
        self.logger.info("Starting EVM simulation environment...")

        # Start Anvil
        self._start_anvil()

        # Connect to Anvil
        self._connect_web3()

        # Setup accounts
        self._setup_accounts()

        # Load protocol addresses
        self._load_protocol_addresses()

        # Initialize state
        self._initialize_state()

        self.logger.info(f"✓ EVM environment ready at block {self.current_state.block_number}")

    def stop(self):
        """Stop the simulation environment"""
        if self.anvil_process:
            self.logger.info("Stopping Anvil...")
            self.anvil_process.terminate()
            self.anvil_process.wait(timeout=5)
            self.anvil_process = None

    def _start_anvil(self):
        """Start Foundry Anvil for mainnet forking"""
        self.logger.info("Starting Anvil mainnet fork...")

        cmd = [
            'anvil',
            '--port', str(self.port),
            '--chain-id', str(self.chain_id),
            '--accounts', '10',
            '--balance', '10000'
        ]

        if self.fork_url:
            cmd.extend(['--fork-url', self.fork_url])

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
            time.sleep(3)

            if self.anvil_process.poll() is not None:
                stderr = self.anvil_process.stderr.read() if self.anvil_process.stderr else ""
                raise RuntimeError(f"Anvil failed to start: {stderr}")

            self.logger.info("✓ Anvil started")

        except FileNotFoundError:
            raise RuntimeError(
                "Anvil not found. Install Foundry: "
                "curl -L https://foundry.paradigm.xyz | bash && foundryup"
            )

    def _connect_web3(self):
        """Connect to Anvil via Web3"""
        rpc_url = f"http://localhost:{self.port}"
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        # Verify connection
        if not self.w3.is_connected():
            raise RuntimeError(f"Failed to connect to Anvil at {rpc_url}")

        self.logger.info(f"✓ Connected to Anvil (chain_id={self.w3.eth.chain_id})")

    def _setup_accounts(self):
        """Setup test accounts"""
        # Get Anvil's default accounts
        self.accounts = self.w3.eth.accounts[:10]

        # First account is the attacker
        self.attacker_account = self.accounts[0]

        self.logger.info(f"✓ Setup {len(self.accounts)} accounts")
        self.logger.info(f"  Attacker: {self.attacker_account}")

    def _load_protocol_addresses(self):
        """Load DeFi protocol addresses"""
        # Common mainnet protocol addresses
        self.protocol_addresses = {
            # Uniswap V2
            'uniswap_v2_factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
            'uniswap_v2_router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',

            # Uniswap V3
            'uniswap_v3_factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
            'uniswap_v3_router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',

            # Aave V3
            'aave_v3_pool': '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2',
            'aave_v3_oracle': '0x54586bE62E3c3580375aE3723C145253060Ca0C2',

            # Compound V3
            'compound_v3_usdc': '0xc3d688B66703497DAA19211EEdff47f25384cdc3',

            # Curve
            'curve_tricrypto': '0xD51a44d3FaE010294C616388b506AcdA1bfAAE46',

            # Balancer
            'balancer_vault': '0xBA12222222228d8Ba445958a75a0704d566BF2C8',

            # Common tokens
            'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
            'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
        }

        self.logger.info(f"✓ Loaded {len(self.protocol_addresses)} protocol addresses")

    def _initialize_state(self):
        """Initialize environment state"""
        current_block = self.w3.eth.block_number
        current_timestamp = self.w3.eth.get_block('latest')['timestamp']

        self.current_state = EnvironmentState(
            block_number=current_block,
            timestamp=current_timestamp
        )

        # Load initial balances
        for account in self.accounts:
            self.current_state.balances[account] = {
                'ETH': self.w3.eth.get_balance(account)
            }

    def execute_action(self, action: Action) -> ActionResult:
        """
        Execute an action in the environment

        Args:
            action: The action to execute

        Returns:
            ActionResult with success status, gas used, and profit
        """
        from_address = action.from_address or self.attacker_account
        initial_balance = self._get_eth_balance(from_address)

        try:
            if action.action_type == ActionType.SWAP:
                result = self._execute_swap(action, from_address)
            elif action.action_type == ActionType.FLASH_LOAN:
                result = self._execute_flash_loan(action, from_address)
            elif action.action_type == ActionType.BORROW:
                result = self._execute_borrow(action, from_address)
            elif action.action_type == ActionType.LIQUIDATE:
                result = self._execute_liquidate(action, from_address)
            else:
                raise ValueError(f"Unsupported action type: {action.action_type}")

            # Calculate profit
            final_balance = self._get_eth_balance(from_address)
            gas_cost_eth = Decimal(result.gas_used) * Decimal(self.gas_price) / Decimal(10**18)
            profit_eth = Decimal(final_balance - initial_balance) / Decimal(10**18)
            profit_usd = (profit_eth - gas_cost_eth) * self.eth_price_usd

            result.profit = profit_usd

            # Update state
            self.current_state.total_gas_used += result.gas_used
            self.current_state.total_value_extracted += profit_usd

            # Check invariants
            violations = self._check_invariants()
            if violations:
                result.state_changes['invariant_violations'] = violations

            return result

        except Exception as e:
            self.logger.error(f"Action execution failed: {e}")
            return ActionResult(
                success=False,
                gas_used=0,
                profit=Decimal(0),
                state_changes={},
                error=str(e)
            )

    def _execute_swap(self, action: Action, from_address: str) -> ActionResult:
        """Execute a swap on a DEX"""
        params = action.parameters

        # For now, simulate a successful swap
        # In full implementation, this would interact with actual Uniswap contracts

        self.logger.debug(f"Executing swap: {params}")

        return ActionResult(
            success=True,
            gas_used=150000,
            profit=Decimal(0),
            state_changes={
                'action': 'swap',
                'pool': params.get('pool'),
                'token_in': params.get('token_in'),
                'token_out': params.get('token_out'),
                'amount_in': params.get('amount_in'),
            }
        )

    def _execute_flash_loan(self, action: Action, from_address: str) -> ActionResult:
        """Execute a flash loan"""
        params = action.parameters

        self.logger.debug(f"Executing flash loan: {params}")

        return ActionResult(
            success=True,
            gas_used=300000,
            profit=Decimal(0),
            state_changes={
                'action': 'flash_loan',
                'protocol': params.get('protocol'),
                'token': params.get('token'),
                'amount': params.get('amount'),
            }
        )

    def _execute_borrow(self, action: Action, from_address: str) -> ActionResult:
        """Execute a borrow from a lending protocol"""
        params = action.parameters

        self.logger.debug(f"Executing borrow: {params}")

        return ActionResult(
            success=True,
            gas_used=200000,
            profit=Decimal(0),
            state_changes={
                'action': 'borrow',
                'protocol': params.get('protocol'),
                'asset': params.get('asset'),
                'amount': params.get('amount'),
            }
        )

    def _execute_liquidate(self, action: Action, from_address: str) -> ActionResult:
        """Execute a liquidation"""
        params = action.parameters

        self.logger.debug(f"Executing liquidation: {params}")

        return ActionResult(
            success=True,
            gas_used=250000,
            profit=Decimal(0),
            state_changes={
                'action': 'liquidate',
                'protocol': params.get('protocol'),
                'borrower': params.get('borrower'),
                'collateral': params.get('collateral'),
            }
        )

    def _get_eth_balance(self, address: str) -> int:
        """Get ETH balance of an address"""
        return self.w3.eth.get_balance(address)

    def _check_invariants(self) -> List[Dict[str, Any]]:
        """Check all registered invariants"""
        violations = []

        for invariant in self.invariants:
            try:
                if not invariant.check(self.current_state):
                    violations.append({
                        'name': invariant.name,
                        'severity': invariant.severity,
                        'description': invariant.description
                    })
            except Exception as e:
                self.logger.error(f"Invariant check failed: {invariant.name} - {e}")

        return violations

    def add_invariant(self, invariant: Any):
        """Add an invariant to check"""
        self.invariants.append(invariant)
        self.logger.info(f"Added invariant: {invariant.name}")

    def snapshot(self, name: str = "default") -> int:
        """Create a snapshot of current state"""
        snapshot_id = self.w3.provider.make_request('evm_snapshot', [])['result']
        self.snapshots[name] = snapshot_id
        self.logger.debug(f"Created snapshot '{name}': {snapshot_id}")
        return snapshot_id

    def revert(self, name: str = "default"):
        """Revert to a snapshot"""
        if name not in self.snapshots:
            raise ValueError(f"Snapshot '{name}' not found")

        snapshot_id = self.snapshots[name]
        self.w3.provider.make_request('evm_revert', [snapshot_id])
        self.logger.debug(f"Reverted to snapshot '{name}': {snapshot_id}")

        # Re-initialize state
        self._initialize_state()

    def mine_blocks(self, num_blocks: int = 1):
        """Mine blocks"""
        for _ in range(num_blocks):
            self.w3.provider.make_request('evm_mine', [])
        self.current_state.block_number += num_blocks

    def set_timestamp(self, timestamp: int):
        """Set block timestamp"""
        self.w3.provider.make_request('evm_setNextBlockTimestamp', [timestamp])
        self.current_state.timestamp = timestamp

    def impersonate_account(self, address: str):
        """Impersonate an account (useful for testing)"""
        self.w3.provider.make_request('anvil_impersonateAccount', [address])

    def stop_impersonating(self, address: str):
        """Stop impersonating an account"""
        self.w3.provider.make_request('anvil_stopImpersonatingAccount', [address])

    def get_state(self) -> EnvironmentState:
        """Get current environment state"""
        return self.current_state.clone()

    def get_metrics(self) -> Dict[str, Any]:
        """Get environment metrics"""
        return {
            'total_gas_used': self.current_state.total_gas_used,
            'total_value_extracted': float(self.current_state.total_value_extracted),
            'block_number': self.current_state.block_number,
            'timestamp': self.current_state.timestamp,
            'num_actions': len(self.state_history),
        }

    def reset(self):
        """Reset environment to initial state"""
        self.stop()
        self.start()

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
