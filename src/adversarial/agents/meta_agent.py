"""
Meta-Agent

AI orchestrator using Claude for high-level strategy and synthesis.
"""

from typing import Any, Dict, List, Optional
import logging
from .base_agent import BaseAgent


class MetaAgent(BaseAgent):
    """
    Meta-Agent (AI Orchestrator)

    Uses Claude AI for:
    - High-level attack strategy coordination
    - Novel exploit pattern discovery
    - Cross-referencing known vulnerabilities
    - Generating natural language explanations
    - Synthesizing recommendations

    The meta-agent sits above attacker and defender agents, providing
    intelligent orchestration and insights that go beyond rule-based systems.

    Example:
        meta_agent = MetaAgent(
            model='claude-sonnet-4',
            attacker_agents=attackers,
            defender_agent=defender
        )

        # Analyze results
        analysis = meta_agent.analyze_and_recommend(vulnerabilities)

        # Get strategic insights
        insights = meta_agent.generate_insights()
    """

    def __init__(
        self,
        model: str = 'claude-sonnet-4',
        attacker_agents: Optional[List[Any]] = None,
        defender_agent: Optional[Any] = None
    ):
        """
        Initialize meta-agent

        Args:
            model: Claude model to use
            attacker_agents: List of attacker agents
            defender_agent: Defender agent
        """
        super().__init__(
            agent_id='meta_agent',
            agent_type='meta',
            environment=None
        )

        self.model = model
        self.attacker_agents = attacker_agents or []
        self.defender_agent = defender_agent

        # AI orchestration state
        self.claude_client = None  # Would initialize Anthropic client
        self.analysis_history: List[Dict[str, Any]] = []

        self.logger.warning(
            "Meta-agent AI orchestration requires ANTHROPIC_API_KEY. "
            "Current implementation provides basic interface."
        )

    def perceive(self, state: Any) -> Dict[str, Any]:
        """
        Perceive high-level patterns and relationships

        Args:
            state: Current environment state

        Returns:
            High-level observations
        """
        observations = {
            'attacker_performance': self._analyze_attacker_performance(),
            'defender_insights': self._get_defender_insights(),
            'novel_patterns': self._detect_novel_patterns(),
            'cross_protocol_risks': self._identify_cross_protocol_risks()
        }

        return observations

    def decide(self, observations: Dict[str, Any]) -> Any:
        """
        Make strategic decisions

        Args:
            observations: High-level observations

        Returns:
            Strategic action
        """
        # Decide on next research direction
        if observations['novel_patterns']:
            return {
                'action': 'investigate_pattern',
                'pattern': observations['novel_patterns'][0]
            }

        return None

    def act(self, action: Any) -> Any:
        """
        Execute meta-level action

        Args:
            action: Meta-action to execute

        Returns:
            Result of the action
        """
        if action is None:
            return None

        # Placeholder: would use Claude API here
        return None

    def analyze_and_recommend(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze vulnerabilities and generate recommendations using AI

        Args:
            vulnerabilities: List of vulnerabilities found

        Returns:
            Analysis with AI-generated insights and recommendations
        """
        if not vulnerabilities:
            return {
                'analysis': 'No vulnerabilities found.',
                'recommendations': [],
                'insights': []
            }

        # In full implementation, this would use Claude API
        # For MVP, provide rule-based analysis

        analysis = {
            'summary': self._generate_summary(vulnerabilities),
            'severity_assessment': self._assess_severity(vulnerabilities),
            'attack_vectors': self._identify_attack_vectors(vulnerabilities),
            'recommendations': self._generate_ai_recommendations(vulnerabilities),
            'insights': self._generate_insights(vulnerabilities),
            'estimated_risk': self._estimate_risk(vulnerabilities)
        }

        self.analysis_history.append(analysis)

        return analysis

    def _analyze_attacker_performance(self) -> Dict[str, Any]:
        """Analyze performance of attacker agents"""
        if not self.attacker_agents:
            return {}

        performance = {
            'total_agents': len(self.attacker_agents),
            'successful_attacks': 0,
            'total_profit': 0.0,
            'best_strategy': None
        }

        for agent in self.attacker_agents:
            metrics = agent.get_metrics()
            performance['successful_attacks'] += metrics.get('actions_taken', 0)
            performance['total_profit'] += metrics.get('total_profit', 0.0)

        return performance

    def _get_defender_insights(self) -> Dict[str, Any]:
        """Get insights from defender agent"""
        if not self.defender_agent:
            return {}

        return {
            'critical_fixes': self.defender_agent.get_critical_fixes(),
            'vulnerability_count': len(self.defender_agent.vulnerability_database)
        }

    def _detect_novel_patterns(self) -> List[Dict[str, Any]]:
        """Detect novel attack patterns"""
        # Placeholder: AI would identify unusual patterns
        return []

    def _identify_cross_protocol_risks(self) -> List[Dict[str, Any]]:
        """Identify risks across multiple protocols"""
        # Placeholder: AI would analyze composability risks
        return []

    def _generate_summary(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """Generate natural language summary"""
        num_vulns = len(vulnerabilities)
        total_profit = sum(v.get('profit', 0) for v in vulnerabilities)

        critical = sum(1 for v in vulnerabilities if v.get('severity') == 'CRITICAL')
        high = sum(1 for v in vulnerabilities if v.get('severity') == 'HIGH')

        summary = (
            f"Discovered {num_vulns} vulnerabilities with potential profit "
            f"of ${total_profit:,.2f}. "
            f"Severity breakdown: {critical} critical, {high} high priority."
        )

        return summary

    def _assess_severity(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """Assess overall severity"""
        if any(v.get('severity') == 'CRITICAL' for v in vulnerabilities):
            return "CRITICAL - Immediate action required"
        elif any(v.get('severity') == 'HIGH' for v in vulnerabilities):
            return "HIGH - Address before deployment"
        else:
            return "MEDIUM - Recommended to fix"

    def _identify_attack_vectors(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify attack vectors"""
        vectors = set()

        for vuln in vulnerabilities:
            vuln_type = vuln.get('type', 'unknown')
            vectors.add(vuln_type)

        return list(vectors)

    def _generate_ai_recommendations(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate AI-powered recommendations"""
        # In full implementation, this would use Claude API
        # For MVP, provide structured recommendations

        recommendations = []

        vuln_types = set(v.get('type') for v in vulnerabilities)

        if 'sandwich' in vuln_types:
            recommendations.append(
                "Priority 1: Implement MEV protection using Flashbots Protect "
                "or private mempools to prevent sandwich attacks"
            )

        if 'oracle_manipulation' in vuln_types:
            recommendations.append(
                "Priority 1: Replace spot price oracles with TWAP and implement "
                "multi-oracle architecture (Chainlink + Uniswap TWAP)"
            )

        if 'flash_loan' in vuln_types:
            recommendations.append(
                "Priority 1: Add reentrancy guards and implement same-block "
                "borrow restrictions to prevent flash loan exploits"
            )

        # Add general recommendations
        recommendations.extend([
            "Conduct professional security audit before mainnet deployment",
            "Implement circuit breakers for extreme market conditions",
            "Add comprehensive monitoring and alerting for suspicious activity",
            "Consider bug bounty program for responsible disclosure"
        ])

        return recommendations

    def _generate_insights(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate strategic insights"""
        insights = []

        # Pattern analysis
        if len(vulnerabilities) > 5:
            insights.append(
                "Multiple vulnerability types detected suggests systematic issues "
                "in protocol design. Consider comprehensive security review."
            )

        # Profit analysis
        max_profit = max((v.get('profit', 0) for v in vulnerabilities), default=0)
        if max_profit > 100000:
            insights.append(
                f"Maximum exploit profit of ${max_profit:,.2f} indicates high-value "
                "target. Expect sophisticated attackers if vulnerabilities not fixed."
            )

        # Invariant analysis
        invariant_violations = [v for v in vulnerabilities if v.get('invariant')]
        if invariant_violations:
            insights.append(
                f"{len(invariant_violations)} invariant violations detected. "
                "These represent fundamental protocol assumptions being broken."
            )

        return insights

    def _estimate_risk(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate risk levels"""
        total_profit = sum(v.get('profit', 0) for v in vulnerabilities)

        return {
            'financial_risk': f"${total_profit:,.2f}",
            'likelihood': 'HIGH' if len(vulnerabilities) > 3 else 'MEDIUM',
            'impact': 'CRITICAL' if total_profit > 100000 else 'HIGH',
            'recommended_action': (
                'DO NOT DEPLOY' if total_profit > 100000
                else 'FIX BEFORE DEPLOYMENT'
            )
        }

    def generate_insights(self) -> List[str]:
        """Generate strategic insights from all analyses"""
        if not self.analysis_history:
            return ["No analysis history available"]

        insights = [
            f"Analyzed {len(self.analysis_history)} test scenarios",
            f"Coordinated {len(self.attacker_agents)} attacker agents",
        ]

        return insights

    def __repr__(self):
        return (
            f"MetaAgent(model={self.model}, "
            f"attackers={len(self.attacker_agents)}, "
            f"defender={'✓' if self.defender_agent else '✗'})"
        )
