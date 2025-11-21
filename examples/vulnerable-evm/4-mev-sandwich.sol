// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Vulnerable MEV Sandwich Attack
 * @notice This contract demonstrates MEV (Maximal Extractable Value) sandwich attack vulnerability
 * @dev INTENTIONALLY VULNERABLE - FOR TESTING ONLY
 *
 * Vulnerability: DEX swap without slippage protection
 * Expected Detection: mev-hunter-agent
 * Severity: HIGH
 *
 * Attack Scenario (Sandwich Attack):
 * 1. Victim submits swap: 50 ETH → TOKEN
 * 2. Attacker sees this in mempool
 * 3. Attacker front-runs: Buy TOKEN with 100 ETH (price goes up)
 * 4. Victim's swap executes at worse price
 * 5. Attacker back-runs: Sell TOKEN for 105 ETH (profit: 5 ETH)
 *
 * Real-world: $900M+ extracted via sandwich attacks in 2023
 */
contract VulnerableMEVSandwich {
    // Simplified AMM (Automated Market Maker) like Uniswap
    uint256 public reserveETH;
    uint256 public reserveTOKEN;
    uint256 public constant FEE_PERCENT = 3; // 0.3% fee

    event Swap(address indexed user, uint256 ethIn, uint256 tokenOut);
    event LiquidityAdded(uint256 eth, uint256 token);

    constructor() {
        // Initialize with liquidity
        reserveETH = 1000 ether;
        reserveTOKEN = 1000000 * 1e18; // 1M tokens
    }

    /// @notice Swap ETH for TOKEN
    /// @dev VULNERABLE: No slippage protection!
    function swapETHForToken() external payable returns (uint256 tokenAmount) {
        require(msg.value > 0, "No ETH sent");

        // Calculate output using constant product formula: x * y = k
        uint256 ethWithFee = (msg.value * (1000 - FEE_PERCENT)) / 1000;
        tokenAmount = getAmountOut(ethWithFee, reserveETH, reserveTOKEN);

        // VULNERABILITY: No minimum output amount check!
        // User could receive far less than expected due to price manipulation

        // Update reserves
        reserveETH += msg.value;
        reserveTOKEN -= tokenAmount;

        // Transfer tokens (simplified)
        // token.transfer(msg.sender, tokenAmount);

        emit Swap(msg.sender, msg.value, tokenAmount);
        return tokenAmount;
    }

    /// @notice Calculate output amount
    function getAmountOut(
        uint256 amountIn,
        uint256 reserveIn,
        uint256 reserveOut
    ) public pure returns (uint256) {
        require(amountIn > 0, "Insufficient input");
        require(reserveIn > 0 && reserveOut > 0, "Insufficient liquidity");

        // Constant product formula: (x + Δx) * (y - Δy) = x * y
        uint256 numerator = amountIn * reserveOut;
        uint256 denominator = reserveIn + amountIn;
        return numerator / denominator;
    }

    /// @notice Get current price
    function getPrice() external view returns (uint256) {
        return (reserveTOKEN * 1e18) / reserveETH;
    }

    /// @notice Add liquidity
    function addLiquidity() external payable {
        // Simplified liquidity addition
        uint256 tokenAmount = (msg.value * reserveTOKEN) / reserveETH;
        reserveETH += msg.value;
        reserveTOKEN += tokenAmount;
        emit LiquidityAdded(msg.value, tokenAmount);
    }
}

/**
 * Example MEV Sandwich Attack:
 *
 * Initial State:
 * - Pool: 1000 ETH, 1M TOKEN
 * - Price: 1 ETH = 1000 TOKEN
 *
 * Step 1: Victim submits transaction
 * victim.swapETHForToken{value: 50 ETH}();
 * Expected: ~47,619 TOKEN (with 0.3% fee)
 *
 * Step 2: Attacker sees transaction in mempool
 *
 * Step 3: Attacker front-runs with higher gas
 * attacker.swapETHForToken{value: 100 ETH}();
 * - Pool now: 1100 ETH, 909,090 TOKEN
 * - Price manipulated: 1 ETH = 826 TOKEN (20% worse!)
 * - Attacker receives: 90,909 TOKEN
 *
 * Step 4: Victim's transaction executes
 * victim.swapETHForToken{value: 50 ETH}();
 * - Pool now: 1150 ETH, 870,370 TOKEN
 * - Victim receives only: 38,720 TOKEN (expected 47,619!)
 * - Victim lost 8,899 TOKEN due to slippage
 *
 * Step 5: Attacker back-runs with lower gas
 * attacker.swapTokenForETH(90,909 TOKEN);
 * - Attacker receives: ~105 ETH
 * - Profit: 5 ETH (~$10,000 at $2000/ETH)
 *
 * Fix 1: Add slippage protection (REQUIRED)
 * function swapETHForToken(uint256 minTokenOut) external payable {
 *     uint256 tokenAmount = calculateSwap(msg.value);
 *     require(tokenAmount >= minTokenOut, "Slippage exceeded");
 *     // ... rest of swap
 * }
 *
 * Fix 2: Use Flashbots or private mempool
 * - Transactions sent to Flashbots aren't visible in public mempool
 * - Prevents front-running
 *
 * Fix 3: Implement MEV-resistant mechanisms
 * - Commit-reveal scheme (2-step swap)
 * - Batch auctions (CoW Swap approach)
 * - Time-weighted pricing
 *
 * Fix 4: Set maximum price impact
 * function swapETHForToken(uint256 maxPriceImpact) external payable {
 *     uint256 priceImpact = calculatePriceImpact(msg.value);
 *     require(priceImpact <= maxPriceImpact, "Price impact too high");
 *     // ... rest of swap
 * }
 *
 * Best Practice:
 * ALWAYS include minAmountOut parameter in swap functions!
 *
 * User should calculate expected output off-chain:
 * expectedOut = getAmountOut(amountIn);
 * minOut = expectedOut * (100 - slippageTolerance) / 100;
 * swap(amountIn, minOut);
 */
