"""
Live Adversarial Testing Integration

Week 4: Integration layer for unified orchestrator.
Adds live fork testing, real attack execution, and invariant validation.

This module extends the existing unified_orchestrator.py with:
- Live mainnet fork testing
- Real transaction execution
- Protocol invariant validation
- MEV profitability analysis
- Historical exploit replay
"""

import logging
import asyncio
import os
from typing import Dict, List, Optional, Any
from dataclasses import asdict
from pathlib import Path

from .simulation.live_fork import LiveFork, LiveForkConfig, create_live_fork
from .live_attack_executor import LiveAttackExecutor, SandwichAttackParams, AttackType
from .protocol_invariants import InvariantChecker, InvariantCategory
from .mev_profitability import LiveMEVProfitabilityAnalyzer, analyze_mev_opportunities
from web3 import Web3

logger = logging.getLogger(__name__)


class LiveAdversarialTestingConfig:
    """Configuration for live adversarial testing"""
    def __init__(
        self,
        enable_live_fork: bool = True,
        enable_attack_execution: bool = True,
        enable_invariant_checking: bool = True,
        enable_mev_analysis: bool = True,

        # Fork settings
        fork_chain: str = "ethereum",
        fork_block: Optional[int] = None,
        rpc_url: Optional[str] = None,

        # Analysis depth
        max_attack_iterations: int = 10,
        test_multiple_parameters: bool = True,

        # Safety
        dry_run: bool = False,  # Simulate without execution
        snapshot_before_attacks: bool = True
    ):
        self.enable_live_fork = enable_live_fork
        self.enable_attack_execution = enable_attack_execution
        self.enable_invariant_checking = enable_invariant_checking
        self.enable_mev_analysis = enable_mev_analysis

        self.fork_chain = fork_chain
        self.fork_block = fork_block
        self.rpc_url = rpc_url or os.getenv("ETHEREUM_RPC_URL")

        self.max_attack_iterations = max_attack_iterations
        self.test_multiple_parameters = test_multiple_parameters

        self.dry_run = dry_run
        self.snapshot_before_attacks = snapshot_before_attacks


class LiveAdversarialIntegration:
    """
    Integration layer for live adversarial testing

    Usage (from unified_orchestrator.py):

        # In UnifiedSecurityOrchestrator class:
        async def _run_adversarial_testing(self) -> Dict:
            integration = LiveAdversarialIntegration(
                project_path=self.project_path,
                config=self.config
            )

            return await integration.run_live_adversarial_tests()
    """

    def __init__(
        self,
        project_path: Path,
        config: Optional[LiveAdversarialTestingConfig] = None
    ):
        self.project_path = project_path
        self.config = config or LiveAdversarialTestingConfig()

        self.fork: Optional[LiveFork] = None
        self.executor: Optional[LiveAttackExecutor] = None
        self.invariant_checker: Optional[InvariantChecker] = None
        self.mev_analyzer: Optional[LiveMEVProfitabilityAnalyzer] = None

        self.results = {
            'fork_info': {},
            'attack_results': [],
            'invariant_violations': [],
            'mev_opportunities': [],
            'summary': {}
        }

    async def run_live_adversarial_tests(self) -> Dict[str, Any]:
        """
        Execute comprehensive live adversarial testing

        Returns:
            Complete results including:
            - Fork information
            - Attack execution results
            - Invariant violations
            - MEV profitability analysis
        """
        logger.info("🚀 Starting live adversarial testing...")

        try:
            # Step 1: Initialize fork
            if self.config.enable_live_fork:
                await self._initialize_fork()

            if not self.fork:
                logger.error("❌ Fork initialization failed")
                return self._create_error_result("Fork initialization failed")

            # Step 2: Identify target contracts
            target_contracts = await self._identify_target_contracts()

            if not target_contracts:
                logger.warning("⚠️  No target contracts identified")
                return self._create_empty_result()

            logger.info(f"Found {len(target_contracts)} target contracts")

            # Step 3: Execute live attacks
            if self.config.enable_attack_execution:
                await self._execute_live_attacks(target_contracts)

            # Step 4: Check protocol invariants
            if self.config.enable_invariant_checking:
                await self._check_protocol_invariants(target_contracts)

            # Step 5: Analyze MEV opportunities
            if self.config.enable_mev_analysis:
                await self._analyze_mev_opportunities(target_contracts)

            # Step 6: Generate summary
            self._generate_summary()

            return self.results

        except Exception as e:
            logger.error(f"❌ Live adversarial testing failed: {e}")
            return self._create_error_result(str(e))

        finally:
            # Cleanup: Stop fork
            if self.fork:
                self.fork.stop()

    async def _initialize_fork(self):
        """Initialize Anvil mainnet fork"""
        logger.info("🔧 Initializing mainnet fork...")

        try:
            fork_config = LiveForkConfig(
                chain=self.config.fork_chain,
                fork_block=self.config.fork_block,
                rpc_url=self.config.rpc_url,
                anvil_port=8545,
                balance=10000  # 10k ETH per test account
            )

            # Create and start fork
            self.fork = LiveFork(fork_config)

            if not self.fork.start():
                raise RuntimeError("Failed to start Anvil fork")

            # Initialize executor and analyzers
            self.executor = LiveAttackExecutor(self.fork)
            self.invariant_checker = InvariantChecker(self.fork)
            self.mev_analyzer = LiveMEVProfitabilityAnalyzer(self.fork, self.executor)

            # Store fork info
            self.results['fork_info'] = {
                'chain': self.config.fork_chain,
                'block_number': self.fork.w3.eth.block_number,
                'accounts': len(self.fork.accounts),
                'status': 'ready'
            }

            logger.info(f"✅ Fork ready at block {self.fork.w3.eth.block_number}")

        except Exception as e:
            logger.error(f"❌ Fork initialization failed: {e}")
            self.fork = None

    async def _identify_target_contracts(self) -> List[Dict[str, Any]]:
        """
        Identify contracts to test

        Scans project for deployed contracts and classifies them
        (AMM, Lending, Oracle, Governance, etc.)
        """
        logger.info("🔍 Identifying target contracts...")

        # In real implementation, this would:
        # 1. Read deployment artifacts
        # 2. Detect contract types (AMM, Lending, etc.)
        # 3. Gather contract addresses and ABIs

        # For demo, return example targets
        targets = []

        # Example: Uniswap V2 pair (if found in project)
        # targets.append({
        #     'address': '0x...',
        #     'type': 'amm',
        #     'name': 'UniswapV2Pair',
        #     'abi': [...]
        # })

        logger.info(f"Found {len(targets)} target contracts")

        return targets

    async def _execute_live_attacks(self, target_contracts: List[Dict[str, Any]]):
        """Execute real attacks on target contracts"""
        logger.info("⚔️  Executing live attacks...")

        for target in target_contracts:
            contract_type = target.get('type')
            contract_address = target.get('address')

            logger.info(f"Testing {contract_type} at {contract_address}...")

            # Take snapshot for rollback
            snapshot_id = None
            if self.config.snapshot_before_attacks:
                snapshot_id = self.fork.create_snapshot()

            try:
                if contract_type == 'amm':
                    await self._test_amm_attacks(target)
                elif contract_type == 'lending':
                    await self._test_lending_attacks(target)
                elif contract_type == 'oracle':
                    await self._test_oracle_attacks(target)
                elif contract_type == 'governance':
                    await self._test_governance_attacks(target)

            except Exception as e:
                logger.error(f"❌ Attack execution failed for {contract_address}: {e}")

            finally:
                # Restore snapshot
                if snapshot_id:
                    self.fork.restore_snapshot(snapshot_id)

    async def _test_amm_attacks(self, target: Dict[str, Any]):
        """Test AMM-specific attacks"""
        logger.info("🥪 Testing sandwich attacks...")

        # Sandwich attack parameters
        params = SandwichAttackParams(
            target_tx_hash="0x0",  # Placeholder
            target_swap_amount=50000 * 10**18,  # $50K in wei
            pool_address=Web3.to_checksum_address(target['address']),
            token_in=Web3.to_checksum_address("0x0"),  # Placeholder
            token_out=Web3.to_checksum_address("0x0"),  # Placeholder
            frontrun_amount=100000 * 10**18,  # $100K
            slippage_tolerance=0.005  # 0.5%
        )

        # Execute sandwich attack
        result = self.executor.execute_sandwich_attack(params, simulate_first=True)

        # Store result
        self.results['attack_results'].append({
            'type': 'sandwich_attack',
            'target': target['address'],
            'status': result.status.value,
            'profit_usd': result.net_profit_usd,
            'proof': result.proof_of_exploit
        })

        logger.info(f"Sandwich result: {result}")

    async def _test_lending_attacks(self, target: Dict[str, Any]):
        """Test lending protocol attacks"""
        logger.info("⚡ Testing liquidation attacks...")

        # Liquidation attack would be implemented here
        # Similar pattern to _test_amm_attacks

    async def _test_oracle_attacks(self, target: Dict[str, Any]):
        """Test oracle manipulation attacks"""
        logger.info("🎯 Testing oracle manipulation...")

        # Oracle manipulation attack would be implemented here

    async def _test_governance_attacks(self, target: Dict[str, Any]):
        """Test governance attacks"""
        logger.info("🗳️  Testing governance attacks...")

        # Governance attack (flash loan voting, etc.) would be implemented here

    async def _check_protocol_invariants(self, target_contracts: List[Dict[str, Any]]):
        """Check protocol invariants for all targets"""
        logger.info("🔍 Checking protocol invariants...")

        for target in target_contracts:
            contract_address = Web3.to_checksum_address(target['address'])
            contract_type = target.get('type')

            # Determine which invariant category to check
            category_map = {
                'amm': InvariantCategory.AMM,
                'lending': InvariantCategory.LENDING,
                'oracle': InvariantCategory.ORACLE,
                'governance': InvariantCategory.GOVERNANCE,
                'staking': InvariantCategory.STAKING
            }

            category = category_map.get(contract_type)
            if not category:
                logger.warning(f"Unknown contract type: {contract_type}")
                continue

            # Check invariants
            violations = self.invariant_checker.check_category(
                protocol_address=contract_address,
                category=category
            )

            # Store violations
            for violation in violations:
                self.results['invariant_violations'].append({
                    'contract': target['address'],
                    'contract_type': contract_type,
                    'invariant': violation.invariant_name,
                    'severity': violation.severity.value,
                    'expected': str(violation.expected),
                    'actual': str(violation.actual),
                    'deviation': violation.deviation,
                    'exploit_potential': violation.exploit_potential,
                    'mitigation': violation.mitigation
                })

            logger.info(f"Found {len(violations)} invariant violations")

    async def _analyze_mev_opportunities(self, target_contracts: List[Dict[str, Any]]):
        """Analyze MEV opportunities"""
        logger.info("💰 Analyzing MEV profitability...")

        # Prepare protocols for analysis
        protocols = []

        for target in target_contracts:
            contract_type = target.get('type')
            address = Web3.to_checksum_address(target['address'])

            if contract_type == 'amm':
                protocols.append({
                    'type': 'amm',
                    'address': address,
                    'liquidity': 1_000_000,  # Placeholder - should be queried
                    'victim_swap': 50_000
                })
            elif contract_type == 'lending':
                protocols.append({
                    'type': 'lending',
                    'address': address,
                    'positions': [
                        {
                            'size': 100_000,
                            'collateral_ratio': 0.95
                        }
                    ]
                })

        # Analyze opportunities
        opportunities = analyze_mev_opportunities(
            fork=self.fork,
            executor=self.executor,
            target_protocols=protocols
        )

        # Store opportunities
        for opp in opportunities:
            self.results['mev_opportunities'].append({
                'type': opp.opportunity_type,
                'target': opp.target_protocol,
                'profit_usd': opp.net_profit_usd,
                'roi_percent': opp.roi_percent,
                'capital_required': opp.capital_required_usd,
                'profitability': opp.profitability_status.value,
                'worth_executing': opp.is_worth_executing(),
                'optimal_parameters': opp.optimal_parameters
            })

        logger.info(f"Found {len(opportunities)} MEV opportunities")

        # Generate profitability report
        report = self.mev_analyzer.generate_profitability_report(opportunities)
        self.results['mev_profitability_report'] = report

    def _generate_summary(self):
        """Generate summary of live testing results"""
        attack_results = self.results.get('attack_results', [])
        invariant_violations = self.results.get('invariant_violations', [])
        mev_opportunities = self.results.get('mev_opportunities', [])

        successful_attacks = [a for a in attack_results if a['status'] == 'success']
        profitable_mev = [o for o in mev_opportunities if o['worth_executing']]

        critical_violations = [
            v for v in invariant_violations
            if v['severity'] == 'critical'
        ]

        self.results['summary'] = {
            'total_attacks_executed': len(attack_results),
            'successful_attacks': len(successful_attacks),
            'total_profit_demonstrated': sum(a['profit_usd'] for a in successful_attacks),

            'total_invariant_violations': len(invariant_violations),
            'critical_violations': len(critical_violations),

            'total_mev_opportunities': len(mev_opportunities),
            'profitable_opportunities': len(profitable_mev),
            'total_potential_mev_profit': sum(o['profit_usd'] for o in profitable_mev),

            'risk_assessment': self._calculate_risk_assessment()
        }

    def _calculate_risk_assessment(self) -> str:
        """Calculate overall risk assessment"""
        attack_results = self.results.get('attack_results', [])
        invariant_violations = self.results.get('invariant_violations', [])

        successful_attacks = [a for a in attack_results if a['status'] == 'success']
        critical_violations = [
            v for v in invariant_violations
            if v['severity'] == 'critical'
        ]

        if len(successful_attacks) > 0 or len(critical_violations) > 0:
            return "CRITICAL - Exploitable vulnerabilities found"
        elif len(invariant_violations) > 5:
            return "HIGH - Multiple protocol violations detected"
        elif len(invariant_violations) > 0:
            return "MEDIUM - Some invariant violations found"
        else:
            return "LOW - No exploitable issues found"

    def _create_error_result(self, error: str) -> Dict:
        """Create error result"""
        return {
            'error': error,
            'fork_info': {},
            'attack_results': [],
            'invariant_violations': [],
            'mev_opportunities': [],
            'summary': {'status': 'error', 'message': error}
        }

    def _create_empty_result(self) -> Dict:
        """Create empty result when no targets found"""
        return {
            'fork_info': self.results.get('fork_info', {}),
            'attack_results': [],
            'invariant_violations': [],
            'mev_opportunities': [],
            'summary': {
                'status': 'completed',
                'message': 'No target contracts found for testing'
            }
        }


# Integration function for unified_orchestrator.py
async def run_live_adversarial_phase(
    project_path: Path,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Function to integrate with UnifiedSecurityOrchestrator

    Usage in unified_orchestrator.py:

        from adversarial.live_integration import run_live_adversarial_phase

        # In _run_adversarial_testing method:
        async def _run_adversarial_testing(self) -> Dict:
            return await run_live_adversarial_phase(
                project_path=self.project_path,
                config=self.config
            )
    """
    live_config = LiveAdversarialTestingConfig(
        enable_live_fork=config.get('enable_live_fork', True),
        enable_attack_execution=config.get('enable_attack_execution', True),
        enable_invariant_checking=config.get('enable_invariant_checking', True),
        enable_mev_analysis=config.get('enable_mev_analysis', True),
        fork_chain=config.get('fork_chain', 'ethereum'),
        fork_block=config.get('fork_block'),
        rpc_url=config.get('rpc_url')
    )

    integration = LiveAdversarialIntegration(
        project_path=project_path,
        config=live_config
    )

    return await integration.run_live_adversarial_tests()
