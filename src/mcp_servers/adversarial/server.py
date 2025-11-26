#!/usr/bin/env python3
"""
Adversarial MCP Server

Simulates economic exploits and attack vectors:
- Sandwich attacks (MEV)
- Flash loan attacks
- Oracle manipulation
- Governance attacks
- Liquidation sniping
- Cross-protocol arbitrage

Calculates attack profitability and provides mitigation strategies.
"""

import json
from typing import Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent

# Initialize MCP server
app = Server("adversarial-mcp")


# ============ Attack Simulation Templates ============

ATTACK_TEMPLATES = {
    "sandwich": {
        "name": "Sandwich Attack",
        "description": "Frontrun victim transaction with large buy, then backrun with sell",
        "attack_sequence": [
            "Monitor mempool for large swap transactions",
            "Frontrun: Buy target token to increase price",
            "Victim transaction executes at inflated price",
            "Backrun: Sell target token at profit"
        ],
        "requirements": {
            "frontrun_capital": "Variable (10-100 ETH typical)",
            "gas_cost": "~$50-200 depending on network congestion",
            "mev_bundle": "Required for guaranteed execution order"
        },
        "profitability_factors": [
            "Victim transaction size",
            "Pool liquidity depth",
            "Slippage protection (if any)",
            "Gas prices (Gwei)",
            "Token price volatility"
        ]
    },
    "flash_loan": {
        "name": "Flash Loan Attack",
        "description": "Borrow large capital, manipulate protocol, profit, repay in single transaction",
        "attack_sequence": [
            "Flash loan large amount from Aave/Balancer/dYdX",
            "Execute attack (price manipulation, liquidation, arbitrage)",
            "Profit from attack",
            "Repay flash loan + fee (0.05-0.09%)",
            "Keep profit"
        ],
        "requirements": {
            "capital_needed": "$0 (flash loan)",
            "flash_loan_fee": "0.05-0.09% of borrowed amount",
            "gas_cost": "~$100-500 for complex transactions",
            "attack_contract": "Required (custom smart contract)"
        },
        "profitability_factors": [
            "Available flash loan liquidity",
            "Target protocol vulnerability severity",
            "Flash loan fee percentage",
            "Gas costs",
            "Competition from other MEV searchers"
        ]
    },
    "oracle_manipulation": {
        "name": "Oracle Price Manipulation",
        "description": "Manipulate price oracle to trigger favorable liquidations or trades",
        "attack_sequence": [
            "Identify protocol using manipulable oracle (e.g., Uniswap V2 spot price)",
            "Flash loan to drain/pump target pool",
            "Price oracle reports manipulated price",
            "Trigger liquidations or trades at false price",
            "Profit from mispriced positions",
            "Repay flash loan"
        ],
        "requirements": {
            "capital_needed": "$0-500K (flash loan or own capital)",
            "target_oracle": "Single-source or manipulable oracle",
            "attack_window": "Same block or before TWAP update",
            "gas_cost": "~$200-1000 for multi-step attack"
        },
        "profitability_factors": [
            "Oracle manipulation cost",
            "Liquidation bonus percentage",
            "Total value at risk in protocol",
            "Oracle update frequency (TWAP window)",
            "Number of manipulable positions"
        ]
    },
    "governance_attack": {
        "name": "Governance Flash Loan Attack",
        "description": "Flash loan governance tokens to pass malicious proposal",
        "attack_sequence": [
            "Identify governance token available on lending protocols",
            "Flash loan large amount of governance tokens",
            "Vote on malicious proposal (or create and vote)",
            "Proposal passes due to flash-loaned voting power",
            "Repay flash loan in same transaction",
            "Wait for timelock and execute proposal"
        ],
        "requirements": {
            "governance_tokens_available": "Must be borrowable on Aave/Compound",
            "voting_mechanism": "Vulnerable to same-block voting",
            "timelock_duration": "Proposal execution delay (exploit window)",
            "attack_profit": "Depends on treasury/protocol value"
        },
        "profitability_factors": [
            "Treasury size accessible via governance",
            "Flash loan fee for governance tokens",
            "Voting power required for quorum",
            "Timelock duration (risk of detection)",
            "Community monitoring (social layer defense)"
        ]
    },
    "liquidation_sniping": {
        "name": "MEV Liquidation Sniping",
        "description": "Frontrun liquidations to claim liquidation bonus",
        "attack_sequence": [
            "Monitor lending protocols for underwater positions",
            "Detect oracle price update that enables liquidation",
            "Frontrun other liquidators with higher gas price",
            "Execute liquidation and claim bonus (5-10%)",
            "Compete with other MEV bots"
        ],
        "requirements": {
            "monitoring_infrastructure": "Mempool monitoring, oracle watchers",
            "capital_needed": "Varies (protocol-dependent)",
            "gas_bidding": "Must outbid competitors",
            "liquidation_bonus": "5-10% typical"
        },
        "profitability_factors": [
            "Liquidation bonus percentage",
            "Position size being liquidated",
            "Number of competing liquidators",
            "Gas prices and priority fees",
            "Oracle freshness and update frequency"
        ]
    }
}


# ============ MCP Tool Definitions ============

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available adversarial testing tools"""
    return [
        Tool(
            name="simulate_sandwich_attack",
            description="Simulate sandwich attack profitability for a given swap. Calculates expected profit, gas costs, and victim loss.",
            inputSchema={
                "type": "object",
                "properties": {
                    "victim_swap_amount": {
                        "type": "number",
                        "description": "Size of victim's swap transaction in USD"
                    },
                    "pool_liquidity": {
                        "type": "number",
                        "description": "Total pool liquidity in USD"
                    },
                    "slippage_protection": {
                        "type": "number",
                        "description": "Victim's max slippage tolerance percentage (0-100)"
                    },
                    "gas_price_gwei": {
                        "type": "number",
                        "description": "Current gas price in Gwei"
                    }
                },
                "required": ["victim_swap_amount", "pool_liquidity"]
            }
        ),
        Tool(
            name="simulate_flash_loan_attack",
            description="Simulate flash loan attack feasibility and profitability. Analyzes borrow amount, fees, and potential profit.",
            inputSchema={
                "type": "object",
                "properties": {
                    "borrow_amount": {
                        "type": "number",
                        "description": "Amount to borrow via flash loan in USD"
                    },
                    "attack_profit_estimate": {
                        "type": "number",
                        "description": "Estimated profit from attack before fees in USD"
                    },
                    "flash_loan_provider": {
                        "type": "string",
                        "enum": ["aave", "balancer", "dydx"],
                        "description": "Flash loan provider (affects fee rate)"
                    }
                },
                "required": ["borrow_amount", "attack_profit_estimate"]
            }
        ),
        Tool(
            name="simulate_oracle_manipulation",
            description="Simulate oracle manipulation attack. Calculates manipulation cost, potential liquidation profit, and feasibility.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pool_liquidity": {
                        "type": "number",
                        "description": "Target pool liquidity in USD"
                    },
                    "price_deviation_needed": {
                        "type": "number",
                        "description": "Required price deviation percentage to trigger exploit"
                    },
                    "liquidatable_positions": {
                        "type": "number",
                        "description": "Total value of positions that become liquidatable in USD"
                    },
                    "liquidation_bonus_pct": {
                        "type": "number",
                        "description": "Liquidation bonus percentage (e.g., 10 for 10%)"
                    }
                },
                "required": ["pool_liquidity", "price_deviation_needed", "liquidatable_positions"]
            }
        ),
        Tool(
            name="calculate_mev_profitability",
            description="Calculate MEV extraction profitability for various attack types. Returns profit/loss analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "attack_type": {
                        "type": "string",
                        "enum": ["sandwich", "arbitrage", "liquidation"],
                        "description": "Type of MEV attack"
                    },
                    "capital_required": {
                        "type": "number",
                        "description": "Capital required for attack in USD"
                    },
                    "expected_profit": {
                        "type": "number",
                        "description": "Expected profit before costs in USD"
                    },
                    "gas_cost_usd": {
                        "type": "number",
                        "description": "Estimated gas cost in USD"
                    }
                },
                "required": ["attack_type", "expected_profit", "gas_cost_usd"]
            }
        ),
        Tool(
            name="get_attack_template",
            description="Get detailed attack template with sequence, requirements, and profitability factors",
            inputSchema={
                "type": "object",
                "properties": {
                    "attack_type": {
                        "type": "string",
                        "enum": ["sandwich", "flash_loan", "oracle_manipulation", "governance_attack", "liquidation_sniping"],
                        "description": "Type of attack to get template for"
                    }
                },
                "required": ["attack_type"]
            }
        ),
        Tool(
            name="analyze_protocol_vulnerabilities",
            description="Analyze protocol for common economic attack vectors. Returns vulnerability assessment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "protocol_type": {
                        "type": "string",
                        "enum": ["dex", "lending", "governance", "staking"],
                        "description": "Type of DeFi protocol"
                    },
                    "has_oracle": {
                        "type": "boolean",
                        "description": "Does protocol use price oracles?"
                    },
                    "oracle_type": {
                        "type": "string",
                        "enum": ["chainlink", "uniswap_v2_twap", "uniswap_v3_twap", "custom", "none"],
                        "description": "Type of oracle used (if any)"
                    }
                },
                "required": ["protocol_type"]
            }
        )
    ]


# ============ Tool Implementations ============

@app.call_tool()
async def call_tool(name: str, arguments: Dict) -> List[TextContent]:
    """Handle tool calls"""

    if name == "simulate_sandwich_attack":
        return await simulate_sandwich_attack(
            arguments.get("victim_swap_amount", 0),
            arguments.get("pool_liquidity", 0),
            arguments.get("slippage_protection", 0),
            arguments.get("gas_price_gwei", 50)
        )

    elif name == "simulate_flash_loan_attack":
        return await simulate_flash_loan_attack(
            arguments.get("borrow_amount", 0),
            arguments.get("attack_profit_estimate", 0),
            arguments.get("flash_loan_provider", "aave")
        )

    elif name == "simulate_oracle_manipulation":
        return await simulate_oracle_manipulation(
            arguments.get("pool_liquidity", 0),
            arguments.get("price_deviation_needed", 0),
            arguments.get("liquidatable_positions", 0),
            arguments.get("liquidation_bonus_pct", 10)
        )

    elif name == "calculate_mev_profitability":
        return await calculate_mev_profitability(
            arguments.get("attack_type", "sandwich"),
            arguments.get("capital_required", 0),
            arguments.get("expected_profit", 0),
            arguments.get("gas_cost_usd", 0)
        )

    elif name == "get_attack_template":
        return await get_attack_template(
            arguments.get("attack_type", "sandwich")
        )

    elif name == "analyze_protocol_vulnerabilities":
        return await analyze_protocol_vulnerabilities(
            arguments.get("protocol_type", "dex"),
            arguments.get("has_oracle", False),
            arguments.get("oracle_type", "none")
        )

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ============ Tool Functions ============

async def simulate_sandwich_attack(
    victim_swap_amount: float,
    pool_liquidity: float,
    slippage_protection: float = 0,
    gas_price_gwei: float = 50
) -> List[TextContent]:
    """Simulate sandwich attack profitability"""

    # Price impact calculation (simplified constant product formula)
    swap_ratio = victim_swap_amount / pool_liquidity
    price_impact = swap_ratio * 100  # Approximate price impact %

    # Frontrun amount (typically 2-5x victim's size)
    frontrun_multiplier = 3.0
    frontrun_amount = victim_swap_amount * frontrun_multiplier
    frontrun_price_impact = (frontrun_amount / pool_liquidity) * 100

    # Victim experiences compound price impact
    victim_price_impact = frontrun_price_impact + price_impact
    victim_loss = victim_swap_amount * (victim_price_impact / 100)

    # Backrun profit (sell at inflated price)
    # Simplified: profit is roughly the victim's loss minus gas
    gas_cost_eth = 0.3  # ~300k gas for MEV bundle
    gas_cost_usd = gas_cost_eth * (gas_price_gwei / 50) * 2000  # Assume $2000 ETH

    expected_profit = victim_loss * 0.8 - gas_cost_usd  # 80% capture efficiency

    # Check if slippage protection blocks attack
    attack_blocked = slippage_protection > 0 and victim_price_impact > slippage_protection

    output = f"## 🥪 Sandwich Attack Simulation\n\n"
    output += f"### Attack Parameters\n\n"
    output += f"- **Victim Swap Amount**: ${victim_swap_amount:,.2f}\n"
    output += f"- **Pool Liquidity**: ${pool_liquidity:,.2f}\n"
    output += f"- **Slippage Protection**: {slippage_protection:.1f}%\n"
    output += f"- **Gas Price**: {gas_price_gwei} Gwei\n\n"

    output += f"### Attack Analysis\n\n"
    output += f"- **Frontrun Amount**: ${frontrun_amount:,.2f} ({frontrun_multiplier}x victim size)\n"
    output += f"- **Price Impact on Victim**: {victim_price_impact:.2f}%\n"
    output += f"- **Victim Loss**: ${victim_loss:,.2f}\n"
    output += f"- **Gas Cost**: ${gas_cost_usd:.2f}\n"
    output += f"- **Expected Profit**: ${expected_profit:,.2f}\n\n"

    if attack_blocked:
        output += f"### ✅ Attack Blocked\n\n"
        output += f"Victim's slippage protection ({slippage_protection:.1f}%) would **prevent** this attack.\n"
        output += f"Transaction would revert due to excessive price impact ({victim_price_impact:.2f}%).\n\n"
        output += f"**Attack Profitable**: ❌ NO (blocked by slippage protection)\n"
    else:
        if expected_profit > 0:
            output += f"### ⚠️ Attack Profitable\n\n"
            output += f"**Attack Profitable**: ✅ YES\n"
            output += f"**Net Profit**: ${expected_profit:,.2f}\n"
            output += f"**ROI**: {(expected_profit / frontrun_amount * 100):.1f}%\n\n"
        else:
            output += f"### Attack Not Profitable\n\n"
            output += f"**Attack Profitable**: ❌ NO\n"
            output += f"**Expected Loss**: ${abs(expected_profit):,.2f}\n\n"

    output += f"### Mitigation\n\n"
    output += f"- Implement maximum slippage tolerance (0.5-1% recommended)\n"
    output += f"- Use private transaction pools (Flashbots Protect)\n"
    output += f"- Add minimum output amount checks\n"
    output += f"- Consider time-weighted execution for large orders\n"

    return [TextContent(type="text", text=output)]


async def simulate_flash_loan_attack(
    borrow_amount: float,
    attack_profit_estimate: float,
    flash_loan_provider: str = "aave"
) -> List[TextContent]:
    """Simulate flash loan attack feasibility"""

    # Flash loan fees by provider
    flash_loan_fees = {
        "aave": 0.0009,  # 0.09%
        "balancer": 0.0000,  # 0% (but pool swap fees apply)
        "dydx": 0.0000  # 0% (but limited to specific tokens)
    }

    fee_rate = flash_loan_fees.get(flash_loan_provider, 0.0009)
    flash_loan_fee = borrow_amount * fee_rate

    # Estimated gas cost for complex flash loan attack
    gas_cost_usd = 300  # ~$300 for multi-step attack

    # Calculate net profit
    net_profit = attack_profit_estimate - flash_loan_fee - gas_cost_usd

    # Attack feasibility
    attack_viable = net_profit > 1000  # Minimum $1000 profit threshold

    output = f"## ⚡ Flash Loan Attack Simulation\n\n"
    output += f"### Attack Parameters\n\n"
    output += f"- **Borrow Amount**: ${borrow_amount:,.2f}\n"
    output += f"- **Flash Loan Provider**: {flash_loan_provider.upper()}\n"
    output += f"- **Fee Rate**: {fee_rate * 100:.2f}%\n"
    output += f"- **Estimated Attack Profit**: ${attack_profit_estimate:,.2f}\n\n"

    output += f"### Cost Analysis\n\n"
    output += f"- **Flash Loan Fee**: ${flash_loan_fee:,.2f}\n"
    output += f"- **Gas Cost**: ${gas_cost_usd:.2f}\n"
    output += f"- **Total Costs**: ${flash_loan_fee + gas_cost_usd:,.2f}\n\n"

    output += f"### Profitability\n\n"
    output += f"- **Gross Profit**: ${attack_profit_estimate:,.2f}\n"
    output += f"- **Net Profit**: ${net_profit:,.2f}\n"
    output += f"- **ROI**: {(net_profit / (flash_loan_fee + gas_cost_usd) * 100):.1f}%\n\n"

    if attack_viable:
        output += f"### ⚠️ Attack Viable\n\n"
        output += f"**Attack Profitable**: ✅ YES\n"
        output += f"**Capital Required**: $0 (flash loan)\n"
        output += f"**Expected Net Profit**: ${net_profit:,.2f}\n\n"
        output += f"**Risk Level**: MEDIUM (requires custom attack contract)\n"
    else:
        output += f"### Attack Not Viable\n\n"
        output += f"**Attack Profitable**: ❌ NO\n"
        if net_profit < 0:
            output += f"**Expected Loss**: ${abs(net_profit):,.2f}\n"
        else:
            output += f"**Profit too small**: ${net_profit:,.2f} (< $1000 threshold)\n"

    output += f"\n### Mitigation\n\n"
    output += f"- Add same-block deposit restrictions\n"
    output += f"- Use time-weighted price checks (TWAP)\n"
    output += f"- Implement flash loan detection (balance increase > threshold)\n"
    output += f"- Add reentrancy guards on all state-changing functions\n"

    return [TextContent(type="text", text=output)]


async def simulate_oracle_manipulation(
    pool_liquidity: float,
    price_deviation_needed: float,
    liquidatable_positions: float,
    liquidation_bonus_pct: float = 10
) -> List[TextContent]:
    """Simulate oracle manipulation attack"""

    # Estimate manipulation cost (capital needed to move price)
    # Using x*y=k formula: to move price by X%, need to trade ~X% of pool
    manipulation_cost = pool_liquidity * (price_deviation_needed / 100)

    # Flash loan fee for manipulation capital
    flash_loan_fee = manipulation_cost * 0.0009  # 0.09% Aave fee

    # Profit from liquidations
    liquidation_profit = liquidatable_positions * (liquidation_bonus_pct / 100)

    # Gas costs
    gas_cost_usd = 500  # Complex multi-step attack

    # Net profit
    total_cost = flash_loan_fee + gas_cost_usd
    net_profit = liquidation_profit - total_cost

    attack_profitable = net_profit > 5000  # $5000 minimum threshold for this attack type

    output = f"## 📊 Oracle Manipulation Attack Simulation\n\n"
    output += f"### Attack Parameters\n\n"
    output += f"- **Pool Liquidity**: ${pool_liquidity:,.2f}\n"
    output += f"- **Price Deviation Needed**: {price_deviation_needed:.1f}%\n"
    output += f"- **Liquidatable Positions**: ${liquidatable_positions:,.2f}\n"
    output += f"- **Liquidation Bonus**: {liquidation_bonus_pct:.1f}%\n\n"

    output += f"### Attack Cost Analysis\n\n"
    output += f"- **Manipulation Capital**: ${manipulation_cost:,.2f}\n"
    output += f"- **Flash Loan Fee**: ${flash_loan_fee:,.2f} (0.09%)\n"
    output += f"- **Gas Cost**: ${gas_cost_usd:.2f}\n"
    output += f"- **Total Cost**: ${total_cost:,.2f}\n\n"

    output += f"### Profit Analysis\n\n"
    output += f"- **Liquidation Profit**: ${liquidation_profit:,.2f}\n"
    output += f"- **Net Profit**: ${net_profit:,.2f}\n\n"

    if attack_profitable:
        output += f"### ⚠️ Attack Highly Profitable\n\n"
        output += f"**Attack Profitable**: ✅ YES\n"
        output += f"**Expected Net Profit**: ${net_profit:,.2f}\n"
        output += f"**ROI**: {(net_profit / total_cost * 100):.1f}%\n\n"
        output += f"**Risk Level**: HIGH - Oracle manipulation is a critical vulnerability\n"
    else:
        output += f"### Attack Not Profitable\n\n"
        output += f"**Attack Profitable**: ❌ NO\n"
        output += f"**Net Result**: ${net_profit:,.2f}\n"

    output += f"\n### TWAP Bypass Analysis\n\n"
    if price_deviation_needed > 5:
        output += f"- **TWAP Bypass**: Difficult (requires sustaining {price_deviation_needed:.1f}% deviation)\n"
        output += f"- A 30-minute TWAP would require holding manipulated price for multiple blocks\n"
    else:
        output += f"- **TWAP Bypass**: Possible (small deviation of {price_deviation_needed:.1f}%)\n"
        output += f"- Even TWAP oracles may be vulnerable to small deviations\n"

    output += f"\n### Mitigation\n\n"
    output += f"- **Primary**: Use Chainlink Price Feeds (external, manipulation-resistant)\n"
    output += f"- **Secondary**: Implement multi-oracle consensus (3+ sources)\n"
    output += f"- Add circuit breakers for price deviations >{price_deviation_needed:.1f}%\n"
    output += f"- Use TWAP with 30+ minute window\n"
    output += f"- Implement maximum price deviation checks between oracles\n"

    return [TextContent(type="text", text=output)]


async def calculate_mev_profitability(
    attack_type: str,
    capital_required: float,
    expected_profit: float,
    gas_cost_usd: float
) -> List[TextContent]:
    """Calculate MEV extraction profitability"""

    net_profit = expected_profit - gas_cost_usd

    # Risk-adjusted profitability
    competition_factor = {
        "sandwich": 0.7,  # 70% success rate due to competition
        "arbitrage": 0.5,  # 50% success rate (highly competitive)
        "liquidation": 0.6  # 60% success rate
    }.get(attack_type, 0.5)

    expected_value = net_profit * competition_factor

    output = f"## 💰 MEV Profitability Analysis\n\n"
    output += f"### Attack Type: {attack_type.upper()}\n\n"
    output += f"- **Capital Required**: ${capital_required:,.2f}\n"
    output += f"- **Expected Profit (Gross)**: ${expected_profit:,.2f}\n"
    output += f"- **Gas Cost**: ${gas_cost_usd:.2f}\n"
    output += f"- **Net Profit**: ${net_profit:,.2f}\n\n"

    output += f"### Competition Analysis\n\n"
    output += f"- **Competition Factor**: {competition_factor * 100:.0f}% success rate\n"
    output += f"- **Expected Value**: ${expected_value:,.2f}\n"

    if capital_required > 0:
        output += f"- **ROI**: {(net_profit / capital_required * 100):.1f}%\n"

    output += f"\n### Profitability Assessment\n\n"

    if expected_value > 1000:
        output += f"✅ **Highly Profitable** - Expected value: ${expected_value:,.2f}\n"
    elif expected_value > 100:
        output += f"⚠️ **Marginally Profitable** - Expected value: ${expected_value:,.2f}\n"
    else:
        output += f"❌ **Not Profitable** - Expected value: ${expected_value:,.2f}\n"

    return [TextContent(type="text", text=output)]


async def get_attack_template(attack_type: str) -> List[TextContent]:
    """Get detailed attack template"""

    if attack_type not in ATTACK_TEMPLATES:
        return [TextContent(
            type="text",
            text=f"Unknown attack type: {attack_type}"
        )]

    template = ATTACK_TEMPLATES[attack_type]

    output = f"## {template['name']} - Attack Template\n\n"
    output += f"**Description**: {template['description']}\n\n"

    output += f"### Attack Sequence\n\n"
    for i, step in enumerate(template['attack_sequence'], 1):
        output += f"{i}. {step}\n"

    output += f"\n### Requirements\n\n"
    for req, value in template['requirements'].items():
        output += f"- **{req.replace('_', ' ').title()}**: {value}\n"

    output += f"\n### Profitability Factors\n\n"
    for factor in template['profitability_factors']:
        output += f"- {factor}\n"

    return [TextContent(type="text", text=output)]


async def analyze_protocol_vulnerabilities(
    protocol_type: str,
    has_oracle: bool = False,
    oracle_type: str = "none"
) -> List[TextContent]:
    """Analyze protocol for attack vulnerabilities"""

    output = f"## Protocol Vulnerability Analysis\n\n"
    output += f"**Protocol Type**: {protocol_type.upper()}\n"
    output += f"**Uses Oracle**: {'Yes' if has_oracle else 'No'}\n"

    if has_oracle:
        output += f"**Oracle Type**: {oracle_type}\n"

    output += f"\n### Attack Vector Assessment\n\n"

    # DEX vulnerabilities
    if protocol_type == "dex":
        output += f"**Sandwich Attacks**: ⚠️ HIGH RISK\n"
        output += f"- Ensure all swaps have slippage protection\n"
        output += f"- Add minimum output amount requirements\n\n"

        if has_oracle:
            output += f"**Oracle Manipulation**: ⚠️ MEDIUM-HIGH RISK\n"
            if oracle_type in ["uniswap_v2_twap", "custom"]:
                output += f"- Current oracle ({oracle_type}) may be manipulable\n"
                output += f"- Consider switching to Chainlink Price Feeds\n"

    # Lending vulnerabilities
    if protocol_type == "lending":
        output += f"**Flash Loan Attacks**: ⚠️ HIGH RISK\n"
        output += f"- Add same-block deposit/borrow restrictions\n"
        output += f"- Implement flash loan detection\n\n"

        if has_oracle:
            output += f"**Oracle Manipulation**: ⚠️ CRITICAL RISK\n"
            output += f"- Liquidations depend on oracle accuracy\n"
            if oracle_type != "chainlink":
                output += f"- ⚠️ NOT using Chainlink - vulnerable to manipulation\n"

        output += f"\n**Liquidation Sniping**: ⚠️ MEDIUM RISK\n"
        output += f"- Expected MEV activity, not preventable\n"
        output += f"- Cap liquidation bonuses to limit profitability\n"

    # Governance vulnerabilities
    if protocol_type == "governance":
        output += f"**Flash Loan Governance Attack**: ⚠️ HIGH RISK\n"
        output += f"- Implement snapshot-based voting (ERC20Snapshot)\n"
        output += f"- Require minimum token holding duration\n"
        output += f"- Add time locks between proposal and execution\n"

    return [TextContent(type="text", text=output)]


# ============ Main Entry Point ============

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    asyncio.run(main())
