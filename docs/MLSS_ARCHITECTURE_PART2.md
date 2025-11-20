# Multi-Layer Security Stack (MLSS) Architecture - Part 2
## Layers 5-7: Learning, Rewards, and Defense

**[Continuation from Part 1]**

---

## Layer 5: Historical MEV Pattern Learner (HMPL)

**Purpose**: Learn from past exploits and MEV data to achieve superhuman pattern recognition.

### Problem

Current system (Phase 1) only knows attacks we explicitly programmed. Real attackers learn from:
- Historical hacks ($10B+ stolen since 2016)
- MEV patterns ($3B+ annual volume)
- Failed attempts (mempool data)
- Copycat attacks

### Solution: Pattern Learning Pipeline

#### 5.1 Data Sources

**Integrated Sources**:

```python
class DataSourceManager:
    """Aggregate historical exploit and MEV data"""

    def __init__(self):
        self.sources = {
            'flashbots_data': FlashbotsDataSource(),
            'rekt_database': RektNewsDatabase(),
            'mev_inspect': MEVInspectData(),
            'exploit_database': ExploitDBSource(),
            'immunefi_reports': ImmuneFiAPI(),
            'chainalysis': ChainalysisAPI(),  # If available
        }

    def get_historical_exploits(
        self,
        start_date: str,
        end_date: str,
        categories: List[str] = None
    ) -> List[ExploitRecord]:
        """
        Fetch historical exploit data

        Returns:
            List of exploits with:
            - Date, protocol, amount lost
            - Attack vector (oracle, flash loan, etc.)
            - Transaction traces
            - Root cause analysis
        """
        pass
```

**Flashbots MEV Data** (Primary Source):

```python
class FlashbotsDataSource:
    """
    Access Flashbots historical MEV data

    Note: mev-inspect-py deprecated → use Flashbots Data platform
    """

    BASE_URL = "https://data.flashbots.net"

    def fetch_mev_bundles(
        self,
        start_block: int,
        end_block: int,
        bundle_type: str = None  # sandwich, arbitrage, liquidation
    ) -> List[MEVBundle]:
        """
        Fetch MEV bundles from Flashbots Data

        2024 Patterns:
        - Sandwich attacks: $289M extracted
        - Arbitrage: $500M+
        - Liquidations: $200M+
        - Spam bots: 50%+ of L2 gas usage
        """

        # Query Flashbots Data API
        response = requests.get(
            f"{self.BASE_URL}/bundles",
            params={
                'start': start_block,
                'end': end_block,
                'type': bundle_type
            }
        )

        return [self.parse_bundle(b) for b in response.json()]

    def extract_patterns(self, bundles: List[MEVBundle]) -> List[Pattern]:
        """
        Extract attack patterns from bundles

        Pattern features:
        - Transaction sequence
        - Tokens involved
        - Protocols targeted
        - Profit mechanism
        - Success rate
        """
        patterns = []

        for bundle in bundles:
            pattern = Pattern(
                type=classify_bundle_type(bundle),
                sequence=bundle.transactions,
                tokens=[tx.token_in, tx.token_out for tx in bundle.transactions],
                protocols=[tx.protocol for tx in bundle.transactions],
                profit=bundle.profit,
                gas_cost=bundle.gas_cost,
                net_profit=bundle.profit - bundle.gas_cost
            )
            patterns.append(pattern)

        return patterns
```

**Exploit Database** (Known Hacks):

```python
class ExploitDBSource:
    """
    Database of known DeFi exploits

    Sources:
    - Rekt News (https://rekt.news)
    - Immunefi reports
    - Post-mortems
    - Security firm reports
    """

    EXPLOITS_2024 = [
        {
            'date': '2024-01-15',
            'protocol': 'Socket',
            'amount': 3_300_000,
            'category': 'smart_contract_bug',
            'vector': 'infinite_approval_exploit',
            'description': 'Flaw in smart contracts affected wallets with infinite approvals',
            'trace': [...],  # Transaction trace
        },
        {
            'date': '2024-01-31',
            'protocol': 'Orbit Chain',
            'amount': 81_500_000,
            'category': 'bridge_exploit',
            'vector': 'multisig_compromise',
            'description': '7/10 multisig private keys compromised',
            'trace': [...],
        },
        {
            'date': '2024-05-XX',
            'protocol': 'ALEX Bridge',
            'amount': 4_300_000,
            'category': 'bridge_exploit',
            'vector': 'private_key_compromise',
            'description': 'Suspicious withdrawals following key compromise',
            'trace': [...],
        },
        # ... more exploits
    ]

    def get_exploits_by_category(self, category: str) -> List[Exploit]:
        """Group exploits by attack vector"""
        return [
            e for e in self.EXPLOITS_2024
            if e['category'] == category
        ]

    def extract_common_patterns(self, exploits: List[Exploit]) -> List[Pattern]:
        """
        Analyze exploits to find common patterns

        Example: Oracle manipulation exploits
        Common pattern:
        1. Flash loan large amount
        2. Manipulate AMM pool (spot price oracle)
        3. Execute action at manipulated price
        4. Reverse manipulation
        5. Repay flash loan
        """
        patterns = {}

        for exploit in exploits:
            # Group by signature
            signature = self.compute_exploit_signature(exploit)

            if signature not in patterns:
                patterns[signature] = {
                    'count': 0,
                    'total_value': 0,
                    'example_traces': [],
                    'common_sequence': None
                }

            patterns[signature]['count'] += 1
            patterns[signature]['total_value'] += exploit['amount']
            patterns[signature]['example_traces'].append(exploit['trace'])

        # Extract common sequences
        for signature, data in patterns.items():
            data['common_sequence'] = self.find_common_sequence(
                data['example_traces']
            )

        return patterns
```

#### 5.2 Pattern Recognition

**Feature Extraction**:

```python
class ExploitFeatureExtractor:
    """Extract features from exploit traces for ML"""

    def extract_features(self, trace: List[Transaction]) -> np.ndarray:
        """
        Convert transaction trace to feature vector

        Features (100-dimensional vector):
        - Transaction count
        - Unique protocols touched
        - Token types involved
        - Flash loan presence (binary)
        - Oracle reads (count)
        - Price impact (max)
        - Time span (blocks)
        - Gas used (total)
        - Value flow pattern (vector)
        - Repeated actions (count)
        - ...
        """

        features = {
            'tx_count': len(trace),
            'protocols': len(set(tx.protocol for tx in trace)),
            'tokens': len(set(tx.token for tx in trace)),
            'has_flash_loan': any(tx.type == 'flash_loan' for tx in trace),
            'oracle_reads': sum(1 for tx in trace if tx.reads_oracle),
            'max_price_impact': max(tx.price_impact for tx in trace),
            'time_span': trace[-1].block - trace[0].block,
            'total_gas': sum(tx.gas_used for tx in trace),
            # ... 90+ more features
        }

        return self.vectorize(features)
```

**Pattern Matching**:

```python
class PatternMatcher:
    """Match new transactions against known patterns"""

    def __init__(self, historical_patterns: List[Pattern]):
        self.patterns = historical_patterns
        self.feature_extractor = ExploitFeatureExtractor()

        # Build similarity index
        self.pattern_vectors = [
            self.feature_extractor.extract_features(p.trace)
            for p in historical_patterns
        ]

    def match_pattern(
        self,
        current_trace: List[Transaction],
        threshold: float = 0.85
    ) -> List[Pattern]:
        """
        Find similar patterns from history

        Uses cosine similarity on feature vectors
        """

        current_vector = self.feature_extractor.extract_features(current_trace)

        similarities = [
            cosine_similarity(current_vector, pattern_vector)
            for pattern_vector in self.pattern_vectors
        ]

        matches = [
            (pattern, sim)
            for pattern, sim in zip(self.patterns, similarities)
            if sim > threshold
        ]

        return sorted(matches, key=lambda x: x[1], reverse=True)
```

#### 5.3 Transfer Learning

Use learned patterns to guide search:

```python
class TransferLearner:
    """Use historical patterns to bootstrap new attacks"""

    def __init__(self, pattern_db: PatternDatabase):
        self.pattern_db = pattern_db

    def generate_attack_from_pattern(
        self,
        historical_pattern: Pattern,
        current_protocol: Protocol
    ) -> StrategyTemplate:
        """
        Adapt historical exploit to current protocol

        Example:
        Historical: Euler oracle manipulation
        Current: New lending protocol
        → Generate similar attack for new protocol
        """

        # Extract attack structure
        attack_structure = self.decompose_pattern(historical_pattern)

        # Map to current protocol
        adapted_strategy = StrategyTemplate(
            name=f"adapted_{historical_pattern.name}",
            category=historical_pattern.category,
            parameters=self.map_parameters(
                historical_pattern.parameters,
                current_protocol
            ),
            sequence=self.adapt_sequence(
                historical_pattern.sequence,
                current_protocol
            )
        )

        return adapted_strategy

    def decompose_pattern(self, pattern: Pattern) -> Dict:
        """
        Break exploit into abstract components

        Returns:
            {
                'setup': [flash_loan, swap],
                'exploit': [borrow, liquidate],
                'cleanup': [swap, repay],
                'key_insight': 'manipulated_oracle_used_for_collateral'
            }
        """
        pass
```

### HMPL Intelligence Levels

**Level 1: Pattern Recognition**
- Identify known exploit signatures
- Alert on similar transaction sequences

**Level 2: Pattern Adaptation**
- Adapt historical exploits to new protocols
- Transfer attack structure

**Level 3: Pattern Combination**
- Combine multiple historical patterns
- Discover novel composability attacks

**Level 4: Pattern Generalization**
- Extract abstract attack principles
- Generate entirely new attack classes

---

## Layer 6: Hierarchical Reward Engine (HRE)

**Purpose**: Reward partial progress and novelty, not just final exploit success.

### Problem

Phase 1 reward: Binary (exploit success or failure).

**Issues**:
- No credit for partial progress
- No incentive for exploration
- Novel but failed strategies discarded

### Solution: Multi-Level Rewards

#### 6.1 Reward Hierarchy

```python
class HierarchicalRewardEngine:
    """Three-tier reward system"""

    def __init__(self):
        self.micro_rewards = MicroRewardCalculator()
        self.macro_rewards = MacroRewardCalculator()
        self.meta_rewards = MetaRewardCalculator()

    def calculate_total_reward(
        self,
        strategy: StrategyTemplate,
        result: StrategyResult
    ) -> float:
        """
        Total reward = weighted sum of all levels

        Weights:
        - Micro: 0.2
        - Macro: 0.6
        - Meta: 0.2
        """

        micro = self.micro_rewards.calculate(strategy, result)
        macro = self.macro_rewards.calculate(strategy, result)
        meta = self.meta_rewards.calculate(strategy, result)

        return 0.2 * micro + 0.6 * macro + 0.2 * meta
```

#### 6.2 Micro-Rewards

Reward partial achievements:

```python
class MicroRewardCalculator:
    """Reward incremental progress"""

    MICRO_REWARDS = {
        'price_moved_1_percent': 10,
        'price_moved_5_percent': 50,
        'price_moved_10_percent': 100,

        'collateral_ratio_worsened': 20,
        'health_factor_decreased': 30,

        'pool_imbalanced': 15,
        'liquidity_drained_partially': 25,

        'liquidation_price_approached': 40,
        'became_liquidatable': 80,

        'slippage_induced': 10,
        'frontrun_detected': 20,

        'invariant_stressed': 50,  # Close to violation
        'invariant_temporarily_violated': 100,

        'gas_cost_optimized': 5,
        'mev_bundle_created': 15,
    }

    def calculate(
        self,
        strategy: StrategyTemplate,
        result: StrategyResult
    ) -> float:
        """Sum of all micro achievements"""

        total_micro = 0

        # Check each micro achievement
        for achievement, reward in self.MICRO_REWARDS.items():
            if self.check_achievement(result, achievement):
                total_micro += reward

        return total_micro
```

#### 6.3 Macro-Rewards

Reward exploit completion:

```python
class MacroRewardCalculator:
    """Reward successful exploits"""

    def calculate(
        self,
        strategy: StrategyTemplate,
        result: StrategyResult
    ) -> float:
        """
        Macro reward = profit - costs

        Normalized to [0, 1000] for consistency
        """

        if not result.success:
            return 0

        profit_usd = float(result.profit)

        # Normalize using logarithmic scale
        # $100 → 100
        # $1,000 → 200
        # $10,000 → 300
        # $100,000 → 400
        # $1,000,000 → 500

        if profit_usd <= 0:
            return 0

        normalized = 100 * math.log10(profit_usd)

        return min(normalized, 1000)  # Cap at 1000
```

#### 6.4 Meta-Rewards

Reward creativity and novelty:

```python
class MetaRewardCalculator:
    """Reward novel and creative strategies"""

    def __init__(self):
        self.known_strategies = set()

    def calculate(
        self,
        strategy: StrategyTemplate,
        result: StrategyResult
    ) -> float:
        """Reward novelty and creativity"""

        total_meta = 0

        # Novelty bonus
        novelty = self.calculate_novelty(strategy)
        total_meta += novelty * 100

        # Complexity bonus (more steps = more interesting)
        complexity = len(strategy.transactions) / 10.0
        total_meta += complexity * 20

        # Cross-protocol bonus
        protocols = set(tx.protocol for tx in strategy.transactions)
        if len(protocols) > 3:
            total_meta += 50  # Multi-protocol attack

        # Unique invariant violation bonus
        if result.invariant_violated:
            invariant_name = result.invariant_violated['name']
            if invariant_name not in self.violated_invariants_seen:
                total_meta += 100  # First time violating this invariant
                self.violated_invariants_seen.add(invariant_name)

        # Efficiency bonus (profit / gas ratio)
        if result.success:
            efficiency = result.profit / max(result.gas_used, 1)
            total_meta += math.log10(efficiency + 1) * 10

        return total_meta

    def calculate_novelty(self, strategy: StrategyTemplate) -> float:
        """
        Novelty score [0, 1]

        Based on:
        - Distance from known strategies
        - Unique transaction sequences
        - Novel parameter combinations
        """

        # Compute strategy signature
        signature = self.compute_signature(strategy)

        if signature in self.known_strategies:
            return 0.0  # Already seen

        # Find most similar known strategy
        similarities = [
            self.similarity(signature, known)
            for known in self.known_strategies
        ]

        if not similarities:
            return 1.0  # First strategy ever

        max_similarity = max(similarities)
        novelty = 1.0 - max_similarity

        # Archive this strategy
        self.known_strategies.add(signature)

        return novelty
```

### Reward Shaping Effects

**Without HRE** (Phase 1):
- Agents only learn from successes
- Exploration discouraged
- Novel strategies ignored

**With HRE** (Phase 2):
- Credit for partial progress
- Exploration encouraged
- Novel strategies valued
- Faster learning convergence

---

## Layer 7: Adaptive Defense Agent (ADA)

**Purpose**: Automatically generate and test defensive patches.

### Current State (Phase 1)

✅ Defender agent:
- Generates recommendations (text)
- Analyzes attack patterns
- Prioritizes fixes

❌ Missing:
- Actual patch generation
- Patch testing
- Governance awareness

### Enhanced ADA (Phase 2)

#### 7.1 Automated Patch Generation

```python
class AdaptiveDefenseAgent:
    """Automated security patch generation and testing"""

    def __init__(self, environment):
        self.environment = environment
        self.patch_generator = PatchGenerator()
        self.patch_tester = PatchTester()

    def generate_patch_for_vulnerability(
        self,
        vulnerability: Vulnerability
    ) -> List[Patch]:
        """
        Generate defensive patches

        Vulnerability types → Patch types:
        - Oracle manipulation → Add TWAP, multi-oracle
        - Flash loan attack → Add reentrancy guard, same-block check
        - Sandwich attack → Add MEV protection, slippage limits
        """

        vuln_type = vulnerability.type

        if vuln_type == 'oracle_manipulation':
            return self.patch_generator.generate_oracle_fixes(vulnerability)
        elif vuln_type == 'flash_loan_attack':
            return self.patch_generator.generate_flash_loan_fixes(vulnerability)
        elif vuln_type == 'sandwich':
            return self.patch_generator.generate_mev_fixes(vulnerability)
        else:
            # Generic fixes
            return self.patch_generator.generate_generic_fixes(vulnerability)
```

**Patch Generator**:

```python
class PatchGenerator:
    """Generate code patches for vulnerabilities"""

    def generate_oracle_fixes(
        self,
        vulnerability: Vulnerability
    ) -> List[Patch]:
        """
        Oracle manipulation fixes:

        1. Replace spot price with TWAP
        2. Add multi-oracle checks
        3. Add price deviation limits
        4. Add minimum liquidity requirements
        """

        patches = []

        # Patch 1: Add TWAP oracle
        patches.append(Patch(
            name="Implement TWAP Oracle",
            code_changes=[
                CodeChange(
                    file="Oracle.sol",
                    function="getPrice",
                    old_code="""
                        function getPrice() public view returns (uint256) {
                            return pool.spotPrice();
                        }
                    """,
                    new_code="""
                        function getPrice() public view returns (uint256) {
                            // Use TWAP instead of spot price
                            return twapOracle.consult(token, TWAP_PERIOD);
                        }
                    """,
                    description="Replace spot price with TWAP to prevent manipulation"
                )
            ],
            tests=[
                "test_twap_not_manipulable_single_tx",
                "test_twap_requires_multiple_blocks"
            ],
            deployment_changes=[
                "Deploy UniswapV3TWAPOracle",
                "Update Oracle contract"
            ]
        ))

        # Patch 2: Add multi-oracle validation
        patches.append(Patch(
            name="Add Multi-Oracle Validation",
            code_changes=[
                CodeChange(
                    file="Oracle.sol",
                    function="getPrice",
                    old_code="""
                        function getPrice() public view returns (uint256) {
                            return singleOracle.getPrice();
                        }
                    """,
                    new_code="""
                        function getPrice() public view returns (uint256) {
                            uint256 chainlinkPrice = chainlinkOracle.latestAnswer();
                            uint256 uniswapPrice = twapOracle.consult(token, PERIOD);

                            // Prices must agree within 5%
                            uint256 deviation = abs(chainlinkPrice - uniswapPrice);
                            require(
                                deviation < chainlinkPrice * 5 / 100,
                                "Oracle price deviation too high"
                            );

                            return chainlinkPrice;
                        }
                    """,
                    description="Require multiple oracles to agree"
                )
            ],
            tests=[
                "test_multi_oracle_agreement",
                "test_reverts_on_price_deviation"
            ]
        ))

        # Patch 3: Add circuit breaker
        patches.append(Patch(
            name="Add Price Circuit Breaker",
            code_changes=[
                CodeChange(
                    file="Oracle.sol",
                    function="getPrice",
                    new_code="""
                        uint256 public lastPrice;
                        uint256 public constant MAX_PRICE_CHANGE = 10; // 10% per update

                        function getPrice() public view returns (uint256) {
                            uint256 currentPrice = oracle.getPrice();

                            if (lastPrice > 0) {
                                uint256 change = abs(currentPrice - lastPrice);
                                uint256 changePercent = (change * 100) / lastPrice;

                                require(
                                    changePercent <= MAX_PRICE_CHANGE,
                                    "Price change exceeds circuit breaker"
                                );
                            }

                            return currentPrice;
                        }
                    """,
                    description="Limit price changes to prevent manipulation"
                )
            ]
        ))

        return patches
```

#### 7.2 Patch Testing

Test patches against the same adversarial agents:

```python
class PatchTester:
    """Test defensive patches"""

    def test_patch(
        self,
        patch: Patch,
        vulnerability: Vulnerability,
        attacker_agents: List[AttackerAgent]
    ) -> PatchTestResult:
        """
        Test patch effectiveness:

        1. Apply patch to protocol
        2. Re-run adversarial agents
        3. Verify vulnerability is fixed
        4. Check no new vulnerabilities introduced
        """

        # Create patched environment
        patched_env = self.apply_patch_to_environment(patch)

        # Run attackers against patched version
        results = []
        for agent in attacker_agents:
            agent.environment = patched_env
            result = agent.execute_strategy()
            results.append(result)

        # Analyze results
        vulnerability_fixed = not any(
            r.success and r.violates_invariant
            for r in results
        )

        # Check for regressions
        new_vulnerabilities = self.detect_new_vulnerabilities(
            results,
            patched_env
        )

        return PatchTestResult(
            patch=patch,
            vulnerability_fixed=vulnerability_fixed,
            successful_attacks_before=vulnerability.successful_attacks,
            successful_attacks_after=sum(1 for r in results if r.success),
            new_vulnerabilities=new_vulnerabilities,
            recommendation=(
                "APPLY" if vulnerability_fixed and not new_vulnerabilities
                else "REJECT"
            )
        )
```

#### 7.3 Governance-Aware Recommendations

```python
class GovernanceAwareDefender:
    """Generate recommendations considering governance"""

    def generate_recommendation(
        self,
        vulnerability: Vulnerability,
        patch: Patch,
        protocol: Protocol
    ) -> Recommendation:
        """
        Consider governance constraints:

        - Timelock delays
        - Voting requirements
        - Deployment complexity
        - User impact
        - Gas costs
        """

        # Assess urgency
        urgency = self.assess_urgency(vulnerability)

        # Check governance requirements
        gov_requirements = protocol.governance.get_requirements_for_change(
            patch.contract_changes
        )

        # Estimate timeline
        if urgency == "CRITICAL":
            timeline = "EMERGENCY (0-24 hours)"
            process = "Emergency multisig execution"
        elif gov_requirements.requires_vote:
            voting_period = gov_requirements.voting_period_days
            timelock = gov_requirements.timelock_days
            timeline = f"Standard governance ({voting_period + timelock} days)"
            process = "Proposal → Vote → Timelock → Execution"
        else:
            timeline = f"Admin execution ({gov_requirements.timelock_days} days)"
            process = "Admin → Timelock → Execution"

        return Recommendation(
            vulnerability=vulnerability,
            patch=patch,
            urgency=urgency,
            timeline=timeline,
            governance_process=process,
            user_impact=self.estimate_user_impact(patch),
            estimated_cost=self.estimate_deployment_cost(patch),
            priority_score=self.calculate_priority(
                urgency,
                gov_requirements,
                vulnerability
            )
        )
```

---

## [Continued in Part 3...]

**Next**: Layers 8-10 + Integration
- Layer 8: Real-World Attack Feasibility Filter
- Layer 9: Multi-Chain Context Awareness
- Layer 10: Continuous Autonomous Risk Engine
- System Integration & Usage

See `MLSS_ARCHITECTURE_PART3.md`
