// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Vulnerable Access Control
 * @notice This contract demonstrates missing access control vulnerabilities
 * @dev INTENTIONALLY VULNERABLE - FOR TESTING ONLY
 *
 * Vulnerability: Missing onlyOwner modifier on critical functions
 * Expected Detection: Slither, Mythril
 * Severity: CRITICAL
 *
 * Attack Scenario:
 * 1. Attacker calls setOwner() and becomes owner
 * 2. Attacker calls withdraw() and drains all funds
 * 3. Or attacker calls emergencyStop() and DoS the protocol
 *
 * Real-world example: Parity Multisig ($150M), Poly Network ($611M)
 */
contract VulnerableAccessControl {
    address public owner;
    bool public paused;
    mapping(address => uint256) public balances;

    event OwnerChanged(address indexed oldOwner, address indexed newOwner);
    event FundsWithdrawn(address indexed to, uint256 amount);
    event EmergencyStop(address indexed caller);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    /// @notice Deposit ETH
    function deposit() external payable whenNotPaused {
        balances[msg.sender] += msg.value;
    }

    /// @notice VULNERABLE: Missing onlyOwner modifier!
    /// @dev Anyone can call this and become owner!
    function setOwner(address newOwner) external {
        // VULNERABILITY: No access control!
        // Should have: require(msg.sender == owner, "Not owner");
        address oldOwner = owner;
        owner = newOwner;
        emit OwnerChanged(oldOwner, newOwner);
    }

    /// @notice VULNERABLE: Missing onlyOwner modifier!
    /// @dev Anyone can withdraw all funds!
    function withdrawAll(address payable to) external {
        // VULNERABILITY: No access control!
        // Should be: function withdrawAll(address payable to) external onlyOwner
        uint256 amount = address(this).balance;
        (bool success,) = to.call{value: amount}("");
        require(success, "Transfer failed");
        emit FundsWithdrawn(to, amount);
    }

    /// @notice VULNERABLE: Missing onlyOwner modifier!
    /// @dev Anyone can pause the contract (DoS)!
    function emergencyStop() external {
        // VULNERABILITY: No access control!
        // Should be: function emergencyStop() external onlyOwner
        paused = true;
        emit EmergencyStop(msg.sender);
    }

    /// @notice Withdraw user's balance
    function withdraw(uint256 amount) external whenNotPaused {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        (bool success,) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
    }

    /// @notice Example of CORRECT access control
    function unpause() external onlyOwner {
        paused = false;
    }

    /// @notice Get contract balance
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}

/**
 * Example Attacks:
 *
 * Attack 1: Steal ownership and drain funds
 * 1. attacker.setOwner(attackerAddress);  // No access control!
 * 2. attacker.withdrawAll(attackerAddress);  // Steals all ETH
 *
 * Attack 2: Denial of Service
 * 1. attacker.emergencyStop();  // No access control!
 * 2. Contract is now paused forever (unless unpause is called by owner)
 *
 * Attack 3: Privilege escalation
 * 1. attacker.setOwner(attackerAddress);
 * 2. Now attacker has owner privileges for all future onlyOwner functions
 *
 * Fix:
 * 1. Add onlyOwner modifier to sensitive functions:
 *    function setOwner(address newOwner) external onlyOwner { ... }
 *    function withdrawAll(address payable to) external onlyOwner { ... }
 *    function emergencyStop() external onlyOwner { ... }
 *
 * 2. Use OpenZeppelin's Ownable contract:
 *    import "@openzeppelin/contracts/access/Ownable.sol";
 *    contract Vault is Ownable { ... }
 *
 * 3. For more complex scenarios, use OpenZeppelin's AccessControl:
 *    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
 *    function criticalFunction() external onlyRole(ADMIN_ROLE) { ... }
 *
 * 4. Consider using multi-sig or timelock for critical functions:
 *    require(msg.sender == multisigWallet, "Not multisig");
 *
 * Note: EVERY function that modifies critical state or handles funds
 *       should have appropriate access control!
 */
