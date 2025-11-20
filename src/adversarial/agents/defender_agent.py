"""
Defender Agent

Agent that analyzes attacks and generates defensive recommendations.
"""

from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent


class DefenderAgent(BaseAgent):
    """
    Defender Agent

    Analyzes successful attacks and generates recommendations for
    preventing them.

    The defender agent:
    - Observes attack patterns
    - Identifies vulnerabilities exploited
    - Generates mitigation strategies
    - Prioritizes fixes by severity

    Example:
        defender = DefenderAgent(
            environment=env,
            protocol_config={'name': 'MyDeFi', 'type': 'amm'}
        )

        # Analyze attacks
        recommendations = defender.generate_recommendations(vulnerabilities)

        # Get prioritized fixes
        critical_fixes = defender.get_critical_fixes()
    """

    def __init__(
        self,
        environment: Optional[Any] = None,
        protocol_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize defender agent

        Args:
            environment: Simulation environment
            protocol_config: Protocol-specific configuration
        """
        super().__init__(
            agent_id='defender',
            agent_type='defender',
            environment=environment
        )

        self.protocol_config = protocol_config or {}
        self.observed_attacks: List[Dict[str, Any]] = []
        self.vulnerability_database: Dict[str, Any] = {}

    def perceive(self, state: Any) -> Dict[str, Any]:
        """
        Observe the environment for attack patterns

        Args:
            state: Current environment state

        Returns:
            Observations about potential vulnerabilities
        """
        observations = {
            'state': state,
            'potential_vulnerabilities': [],
            'attack_patterns_detected': []
        }

        # Analyze state for vulnerabilities
        observations['potential_vulnerabilities'] = self._detect_vulnerabilities(state)

        return observations

    def decide(self, observations: Dict[str, Any]) -> Any:
        """
        Decide on defensive actions

        Args:
            observations: Observations from perceive()

        Returns:
            Defensive action (recommendation, alert, etc.)
        """
        vulnerabilities = observations.get('potential_vulnerabilities', [])

        if vulnerabilities:
            return {
                'action': 'generate_recommendations',
                'vulnerabilities': vulnerabilities
            }

        return None

    def act(self, action: Any) -> Any:
        """
        Execute defensive action

        Args:
            action: Action to execute

        Returns:
            Result of the action
        """
        if action is None:
            return None

        if action['action'] == 'generate_recommendations':
            return self.generate_recommendations(action['vulnerabilities'])

        return None

    def generate_recommendations(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate defensive recommendations based on vulnerabilities

        Args:
            vulnerabilities: List of vulnerabilities found

        Returns:
            List of recommendations
        """
        recommendations = []

        for vuln in vulnerabilities:
            vuln_type = vuln.get('type', 'unknown')

            # Generate recommendations based on vulnerability type
            if vuln_type == 'sandwich':
                recommendations.extend(self._recommend_sandwich_defenses())
            elif vuln_type == 'oracle_manipulation':
                recommendations.extend(self._recommend_oracle_defenses())
            elif vuln_type == 'flash_loan_attack':
                recommendations.extend(self._recommend_flash_loan_defenses())
            elif 'invariant' in vuln:
                recommendations.extend(
                    self._recommend_invariant_fixes(vuln['invariant'])
                )

        # Remove duplicates
        recommendations = list(set(recommendations))

        # Sort by priority (critical first)
        recommendations = self._prioritize_recommendations(recommendations)

        return recommendations

    def _detect_vulnerabilities(self, state: Any) -> List[Dict[str, Any]]:
        """Detect potential vulnerabilities from state"""
        vulnerabilities = []

        # Check for common vulnerability patterns
        # Placeholder for MVP
        return vulnerabilities

    def _recommend_sandwich_defenses(self) -> List[str]:
        """Recommendations for sandwich attack prevention"""
        return [
            "Implement minimum liquidity requirements for price feeds",
            "Add slippage protection with max price impact checks (e.g., 5% per swap)",
            "Use private mempools (Flashbots Protect) for user transactions",
            "Implement MEV-aware order routing",
            "Add time delays between large swaps",
            "Use Chainlink price feeds instead of spot prices for critical operations"
        ]

    def _recommend_oracle_defenses(self) -> List[str]:
        """Recommendations for oracle manipulation prevention"""
        return [
            "Replace spot price oracles with TWAP (Time-Weighted Average Price)",
            "Implement multi-oracle architecture (Chainlink + Uniswap TWAP)",
            "Add circuit breakers for extreme price movements (>10% per block)",
            "Enforce minimum liquidity requirements for AMM-based oracles",
            "Implement flash loan protections (check block.number between operations)",
            "Use Chainlink Data Streams for low-latency, manipulation-resistant prices",
            "Add price deviation checks across multiple sources",
            "Implement oracle update delays to prevent single-block manipulation"
        ]

    def _recommend_flash_loan_defenses(self) -> List[str]:
        """Recommendations for flash loan attack prevention"""
        return [
            "Implement reentrancy guards on all external functions",
            "Add same-block borrow restrictions (store block.number on borrow)",
            "Use checks-effects-interactions pattern",
            "Implement flash loan detection (check balance changes in same tx)",
            "Add minimum time locks for sensitive operations",
            "Validate state consistency before and after flash loan callbacks",
            "Implement withdrawal delays for new deposits",
            "Use TWAP oracles instead of spot prices"
        ]

    def _recommend_invariant_fixes(self, invariant: Dict[str, Any]) -> List[str]:
        """Recommendations for fixing invariant violations"""
        name = invariant.get('name', '')

        if 'constant product' in name.lower():
            return [
                "Add overflow/underflow checks in swap calculations",
                "Implement k-value validation after every swap",
                "Add minimum reserve requirements",
                "Validate reserve ratios before and after operations"
            ]
        elif 'collateral' in name.lower():
            return [
                "Implement health factor checks before all borrows",
                "Add automated liquidation triggers",
                "Use multiple oracles for collateral valuation",
                "Implement collateral factor safety margins (e.g., 80% max LTV)"
            ]
        else:
            return [
                f"Review and fix invariant: {name}",
                "Add comprehensive invariant testing",
                "Implement assertion checks in production code"
            ]

    def _prioritize_recommendations(
        self,
        recommendations: List[str]
    ) -> List[str]:
        """
        Prioritize recommendations by importance

        Args:
            recommendations: List of recommendations

        Returns:
            Sorted list (most important first)
        """
        # Keywords that indicate critical fixes
        critical_keywords = [
            'reentrancy',
            'invariant',
            'critical',
            'overflow',
            'flash loan protection'
        ]

        high_keywords = [
            'oracle',
            'twap',
            'circuit breaker',
            'multi-oracle'
        ]

        def priority_score(rec: str) -> int:
            rec_lower = rec.lower()
            if any(keyword in rec_lower for keyword in critical_keywords):
                return 3
            elif any(keyword in rec_lower for keyword in high_keywords):
                return 2
            else:
                return 1

        return sorted(recommendations, key=priority_score, reverse=True)

    def analyze_attack_pattern(self, attack_result: Any):
        """
        Analyze an attack to understand the pattern

        Args:
            attack_result: Result from an attack
        """
        if not attack_result.success:
            return

        # Extract attack pattern
        pattern = {
            'type': attack_result.metadata.get('strategy'),
            'profit': float(attack_result.profit),
            'transactions': len(attack_result.transactions),
            'invariant_violated': attack_result.invariant_violated
        }

        self.observed_attacks.append(pattern)

        # Update vulnerability database
        attack_type = pattern['type']
        if attack_type not in self.vulnerability_database:
            self.vulnerability_database[attack_type] = {
                'count': 0,
                'total_profit': 0,
                'avg_profit': 0
            }

        self.vulnerability_database[attack_type]['count'] += 1
        self.vulnerability_database[attack_type]['total_profit'] += pattern['profit']
        self.vulnerability_database[attack_type]['avg_profit'] = (
            self.vulnerability_database[attack_type]['total_profit'] /
            self.vulnerability_database[attack_type]['count']
        )

    def get_critical_fixes(self) -> List[str]:
        """
        Get most critical fixes based on observed attacks

        Returns:
            List of critical fixes to implement
        """
        if not self.vulnerability_database:
            return []

        # Sort vulnerabilities by total profit extracted
        sorted_vulns = sorted(
            self.vulnerability_database.items(),
            key=lambda x: x[1]['total_profit'],
            reverse=True
        )

        critical_fixes = []

        for vuln_type, data in sorted_vulns:
            if vuln_type == 'sandwich':
                critical_fixes.extend(self._recommend_sandwich_defenses()[:3])
            elif vuln_type == 'oracle_manipulation':
                critical_fixes.extend(self._recommend_oracle_defenses()[:3])
            elif vuln_type == 'flash_loan_attack':
                critical_fixes.extend(self._recommend_flash_loan_defenses()[:3])

        return list(set(critical_fixes))

    def generate_security_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive security report

        Returns:
            Security report with vulnerabilities and recommendations
        """
        return {
            'total_attacks_observed': len(self.observed_attacks),
            'vulnerability_summary': self.vulnerability_database,
            'critical_fixes': self.get_critical_fixes(),
            'all_recommendations': self.generate_recommendations(
                [{'type': k} for k in self.vulnerability_database.keys()]
            )
        }
