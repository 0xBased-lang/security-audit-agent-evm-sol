// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Vulnerable Unchecked Return Values
 * @notice This contract demonstrates unchecked external call return values
 * @dev INTENTIONALLY VULNERABLE - FOR TESTING ONLY
 *
 * Vulnerability: Ignored return values from external calls
 * Expected Detection: Slither, Mythril
 * Severity: HIGH to CRITICAL
 *
 * Attack Scenario:
 * 1. User calls withdraw() with failing token transfer
 * 2. Transfer silently fails but balance is still decreased
 * 3. User loses funds without receiving tokens
 *
 * Real-world: Numerous token contracts have failed due to this issue
 */

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
}

contract VulnerableUncheckedReturn {
    IERC20 public token;
    mapping(address => uint256) public deposits;

    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);

    constructor(address _token) {
        token = IERC20(_token);
    }

    /// @notice Deposit tokens
    /// @dev VULNERABLE: Unchecked transferFrom return value!
    function deposit(uint256 amount) external {
        // VULNERABILITY: transferFrom returns false on failure, but we don't check!
        // If transfer fails, deposits mapping is still updated!
        token.transferFrom(msg.sender, address(this), amount);

        // State updated even if transfer failed!
        deposits[msg.sender] += amount;

        emit Deposited(msg.sender, amount);
    }

    /// @notice Withdraw tokens
    /// @dev VULNERABLE: Unchecked transfer return value!
    function withdraw(uint256 amount) external {
        require(deposits[msg.sender] >= amount, "Insufficient balance");

        // Update state first (correct pattern)
        deposits[msg.sender] -= amount;

        // VULNERABILITY: transfer returns false on failure, but we don't check!
        // User's balance decreased but they didn't receive tokens!
        token.transfer(msg.sender, amount);

        emit Withdrawn(msg.sender, amount);
    }

    /// @notice Batch transfer (multiple vulnerabilities)
    /// @dev VULNERABILITY: Silent failures in loop!
    function batchTransfer(address[] calldata recipients, uint256[] calldata amounts) external {
        require(recipients.length == amounts.length, "Length mismatch");

        uint256 totalAmount = 0;
        for (uint256 i = 0; i < amounts.length; i++) {
            totalAmount += amounts[i];
        }

        require(deposits[msg.sender] >= totalAmount, "Insufficient balance");
        deposits[msg.sender] -= totalAmount;

        // VULNERABILITY: If ANY transfer fails, we continue anyway!
        // Some recipients get tokens, others don't, but all amounts are deducted
        for (uint256 i = 0; i < recipients.length; i++) {
            token.transfer(recipients[i], amounts[i]);  // Unchecked!
        }
    }

    /// @notice Approve tokens for spending
    /// @dev VULNERABLE: Unchecked approve!
    function approveSpender(address spender, uint256 amount) external {
        // VULNERABILITY: approve can fail silently
        // User thinks they approved but they didn't!
        token.approve(spender, amount);
    }

    /// @notice Emergency withdraw (owner only, but still vulnerable)
    function emergencyWithdraw(address recipient, uint256 amount) external {
        // Simplified: assume msg.sender is owner

        // VULNERABILITY: Even emergency functions should check return values!
        token.transfer(recipient, amount);
    }
}

/**
 * Attack Scenarios:
 *
 * Scenario 1: Deposit with failing transferFrom
 * 1. Attacker hasn't approved contract
 * 2. Calls deposit(100) → transferFrom fails (returns false)
 * 3. Contract doesn't check return value
 * 4. deposits[attacker] += 100 anyway!
 * 5. Attacker can withdraw 100 tokens they never deposited
 *
 * Scenario 2: Withdraw with failing transfer
 * 1. User calls withdraw(100)
 * 2. deposits[user] -= 100 (correct)
 * 3. transfer fails (e.g., token paused, insufficient balance in contract)
 * 4. Contract doesn't revert
 * 5. User lost 100 from balance but received nothing!
 *
 * Scenario 3: Batch transfer partial failure
 * 1. User calls batchTransfer([addr1, addr2, addr3], [10, 10, 10])
 * 2. deposits[user] -= 30
 * 3. Transfer to addr1: success (10 tokens sent)
 * 4. Transfer to addr2: FAILS (but not checked!)
 * 5. Transfer to addr3: success (10 tokens sent)
 * 6. Result: User lost 30 from balance but only 20 tokens were sent!
 *
 * Why transfers can fail:
 * - Token contract paused
 * - Recipient is blacklisted
 * - Insufficient balance in contract
 * - Gas limit reached in fallback
 * - Transfer amount exceeds allowance
 * - Some tokens (like USDT) don't return boolean
 *
 * Fix 1: Check return value explicitly
 * bool success = token.transfer(msg.sender, amount);
 * require(success, "Transfer failed");
 *
 * Fix 2: Use OpenZeppelin's SafeERC20 (RECOMMENDED)
 * import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
 *
 * using SafeERC20 for IERC20;
 *
 * function deposit(uint256 amount) external {
 *     token.safeTransferFrom(msg.sender, address(this), amount);
 *     deposits[msg.sender] += amount;
 * }
 *
 * function withdraw(uint256 amount) external {
 *     deposits[msg.sender] -= amount;
 *     token.safeTransfer(msg.sender, amount);  // Reverts if fails!
 * }
 *
 * SafeERC20 advantages:
 * - Automatically checks return value
 * - Reverts if transfer fails
 * - Handles tokens that don't return boolean (USDT, BNB)
 * - Handles tokens with non-standard return values
 *
 * Fix 3: Require pattern for simple checks
 * require(
 *     token.transfer(msg.sender, amount),
 *     "Transfer failed"
 * );
 *
 * Best Practice:
 * ALWAYS use SafeERC20 for token operations in production contracts!
 * NEVER ignore return values from external calls!
 *
 * Note: This vulnerability is especially dangerous because:
 * - Contract appears to work correctly in happy path
 * - Only fails silently in edge cases
 * - Can lead to loss of user funds
 * - Hard to detect without thorough testing
 */
