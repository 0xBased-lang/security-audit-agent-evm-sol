// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Vulnerable Flash Loan Oracle Manipulation
 * @notice This contract demonstrates oracle manipulation via flash loans
 * @dev INTENTIONALLY VULNERABLE - FOR TESTING ONLY
 *
 * Vulnerability: Price oracle uses spot price from Uniswap reserves
 * Expected Detection: flash-loan-detector, Slither (if custom detector)
 * Severity: CRITICAL
 *
 * Attack Scenario:
 * 1. Attacker takes flash loan of 1M USDC from Aave
 * 2. Swaps 1M USDC for TOKEN on Uniswap (manipulates price up 10x)
 * 3. Borrows maximum against inflated collateral value
 * 4. Swaps back to restore price
 * 5. Repays flash loan
 * 6. Keeps borrowed funds (profit: ~$200k)
 *
 * Real-world examples: Harvest Finance ($34M), Cream Finance ($130M), bZx ($8M)
 */

interface IUniswapV2Pair {
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}

contract VulnerableFlashLoanOracle {
    IUniswapV2Pair public uniswapPair;
    mapping(address => uint256) public deposits;
    mapping(address => uint256) public borrowed;

    uint256 public constant LTV_RATIO = 80; // 80% loan-to-value

    event Deposited(address indexed user, uint256 amount);
    event Borrowed(address indexed user, uint256 amount);

    constructor(address _uniswapPair) {
        uniswapPair = IUniswapV2Pair(_uniswapPair);
    }

    /// @notice Deposit collateral tokens
    function depositCollateral(uint256 amount) external {
        deposits[msg.sender] += amount;
        emit Deposited(msg.sender, amount);
    }

    /// @notice Borrow USDC against collateral
    /// @dev VULNERABLE: Uses manipulable spot price!
    function borrow(uint256 usdcAmount) external {
        uint256 collateralValue = getCollateralValue(msg.sender);
        uint256 maxBorrow = (collateralValue * LTV_RATIO) / 100;

        require(borrowed[msg.sender] + usdcAmount <= maxBorrow, "Exceeds borrow limit");

        borrowed[msg.sender] += usdcAmount;

        // Transfer USDC to borrower
        // ... (simplified)

        emit Borrowed(msg.sender, usdcAmount);
    }

    /// @notice Get collateral value in USDC
    /// @dev VULNERABILITY: Uses Uniswap spot price which can be manipulated!
    function getCollateralValue(address user) public view returns (uint256) {
        uint256 collateralAmount = deposits[user];
        uint256 price = getTokenPrice(); // ← VULNERABLE!
        return collateralAmount * price / 1e18;
    }

    /// @notice Get token price from Uniswap
    /// @dev CRITICAL VULNERABILITY: Spot price from reserves!
    function getTokenPrice() public view returns (uint256) {
        (uint112 reserve0, uint112 reserve1,) = uniswapPair.getReserves();

        // VULNERABILITY: Direct division of reserves = spot price
        // Can be manipulated with large swap in single transaction!
        return (uint256(reserve1) * 1e18) / uint256(reserve0);
    }

    /// @notice Get total value locked
    function getTVL() external view returns (uint256) {
        // Simplified
        return address(this).balance;
    }
}

/**
 * Example Attack:
 *
 * contract FlashLoanAttack {
 *     function attack() external {
 *         // 1. Flash loan 1M USDC from Aave
 *         aave.flashLoan(1_000_000 * 1e6);
 *     }
 *
 *     function executeOperation(...) external {
 *         // 2. Swap 1M USDC → TOKEN (price manipulated 10x)
 *         uniswap.swap(1_000_000 * 1e6, minTokenOut);
 *
 *         // 3. Deposit 1 TOKEN as collateral (valued at 10x inflated price)
 *         vault.depositCollateral(1 * 1e18);
 *
 *         // 4. Borrow maximum USDC based on inflated collateral value
 *         vault.borrow(getMaxBorrow());  // Gets ~800k USDC!
 *
 *         // 5. Swap TOKEN back → USDC (restores price)
 *         uniswap.swap(tokenAmount, minUsdcOut);
 *
 *         // 6. Repay flash loan (1M + 0.09% fee)
 *         repayFlashLoan();
 *
 *         // 7. Profit: borrowed 800k - flash loan fee = ~799k profit!
 *     }
 * }
 *
 * Fix:
 * 1. Use Chainlink price feed (tamper-resistant):
 *    price = chainlinkPriceFeed.latestAnswer();
 *
 * 2. Use Uniswap V3 TWAP (Time-Weighted Average Price):
 *    price = OracleLibrary.consult(pool, TWAP_DURATION);
 *
 * 3. At minimum, use Uniswap V2 TWAP:
 *    // Requires tracking price accumulator over multiple blocks
 *    uint256 timeElapsed = block.timestamp - blockTimestampLast;
 *    require(timeElapsed >= MIN_TWAP_WINDOW, "TWAP window too short");
 *
 * Never use spot price (reserve0 / reserve1) for anything financial!
 */
