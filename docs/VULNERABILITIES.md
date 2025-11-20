# Comprehensive Blockchain Security Vulnerabilities Reference

> **Complete vulnerability detection checklist for EVM and Solana smart contracts**
> Based on OWASP Top 10 (2025), research papers, and real-world exploits

Last Updated: 2025
Total tracked losses in 2024: **$1.42 Billion**

---

## Table of Contents

### EVM/Solidity Vulnerabilities
1. [Access Control Vulnerabilities](#1-access-control-vulnerabilities)
2. [Reentrancy Attacks](#2-reentrancy-attacks)
3. [Price Oracle Manipulation](#3-price-oracle-manipulation)
4. [Arithmetic Issues](#4-arithmetic-issues)
5. [Logic Errors](#5-logic-errors)
6. [Input Validation](#6-input-validation)
7. [External Call Safety](#7-external-call-safety)
8. [Flash Loan Attacks](#8-flash-loan-attacks)
9. [Randomness Issues](#9-randomness-issues)
10. [Denial of Service](#10-denial-of-service)
11. [Additional EVM Vulnerabilities](#11-additional-evm-vulnerabilities)

### Solana/Rust Vulnerabilities
12. [Account Validation Issues](#12-account-validation-issues)
13. [PDA (Program Derived Address) Vulnerabilities](#13-pda-vulnerabilities)
14. [Integer Safety in Rust](#14-integer-safety-in-rust)
15. [Deserialization Vulnerabilities](#15-deserialization-vulnerabilities)
16. [CPI (Cross-Program Invocation) Security](#16-cpi-security)
17. [Additional Solana Vulnerabilities](#17-additional-solana-vulnerabilities)

---

# EVM/Solidity Vulnerabilities

## 1. Access Control Vulnerabilities

**OWASP Rank**: #1 (2025)
**2024 Losses**: $953.2 Million
**Severity**: CRITICAL

### Description
Access control flaws allow unauthorized users to access or modify contract data/functions. These arise when code fails to enforce proper permission checks.

### Common Patterns

#### 1.1 Missing Access Control Modifiers

**Vulnerable Code:**
```solidity
contract Vulnerable {
    address public owner;

    // CRITICAL: Anyone can change the owner!
    function setOwner(address _newOwner) public {
        owner = _newOwner;
    }
}
```

**Secure Code:**
```solidity
contract Secure {
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    function setOwner(address _newOwner) public onlyOwner {
        owner = _newOwner;
    }
}
```

#### 1.2 tx.origin Authentication

**Vulnerable Code:**
```solidity
function withdraw() public {
    require(tx.origin == owner); // WRONG!
    payable(msg.sender).transfer(address(this).balance);
}
```

**Why It's Vulnerable:**
- `tx.origin` can be manipulated through phishing attacks
- Attacker contract can call victim's contract while tx.origin is the user

**Secure Code:**
```solidity
function withdraw() public {
    require(msg.sender == owner); // Use msg.sender!
    payable(msg.sender).transfer(address(this).balance);
}
```

#### 1.3 Unprotected Initialization

**Vulnerable Code:**
```solidity
contract Proxy {
    address public implementation;

    // CRITICAL: Anyone can initialize!
    function initialize(address _impl) public {
        implementation = _impl;
    }
}
```

**Secure Code:**
```solidity
contract Proxy {
    address public implementation;
    bool private initialized;

    function initialize(address _impl) public {
        require(!initialized, "Already initialized");
        implementation = _impl;
        initialized = true;
    }
}
```

#### 1.4 Delegatecall to Untrusted Contract

**Vulnerable Code:**
```solidity
function proxyCall(address target, bytes memory data) public {
    // CRITICAL: Allows arbitrary code execution in proxy context!
    target.delegatecall(data);
}
```

**Impact**: Attacker can change proxy storage, steal funds, or take control.

### Detection Tools
- **Slither**: `unprotected-function`, `tx-origin`, `missing-zero-check`
- **Mythril**: Access control analysis
- **Certora**: Formal verification of permission rules
- **Manual Review**: Role-based access control logic

### Real-World Examples
- Parity Wallet Hack (2017): $150M+ frozen due to unprotected initialization
- Multiple 2024 exploits totaling $953.2M

---

## 2. Reentrancy Attacks

**OWASP Rank**: #5 (2025) - Down from #1 but still critical
**2024 Losses**: $35.7 Million
**Severity**: CRITICAL

### Description
Reentrancy exploits occur when external calls allow malicious contracts to re-enter the calling function before state updates complete.

### Attack Types

#### 2.1 Classic Reentrancy

**Vulnerable Code:**
```solidity
mapping(address => uint) public balances;

function withdraw() public {
    uint amount = balances[msg.sender];

    // CRITICAL: External call before state update!
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success);

    balances[msg.sender] = 0; // Too late!
}
```

**Attack Contract:**
```solidity
contract Attacker {
    Vulnerable victim;

    receive() external payable {
        if (address(victim).balance > 0) {
            victim.withdraw(); // Re-enter!
        }
    }
}
```

**Secure Code (Checks-Effects-Interactions):**
```solidity
function withdraw() public {
    uint amount = balances[msg.sender];

    // Update state BEFORE external call
    balances[msg.sender] = 0;

    (bool success, ) = msg.sender.call{value: amount}("");
    require(success);
}
```

#### 2.2 Cross-Function Reentrancy

**Vulnerable Code:**
```solidity
function withdraw() public {
    uint amount = balances[msg.sender];
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success);
    balances[msg.sender] = 0;
}

function transfer(address to, uint amount) public {
    // CRITICAL: Uses stale balance during reentrancy!
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount;
    balances[to] += amount;
}
```

**Attacker can call `transfer()` during `withdraw()` before balance is updated!**

#### 2.3 Read-Only Reentrancy

**Vulnerable Code:**
```solidity
// Protocol A
function getPrice() public view returns (uint) {
    return reserves0 / reserves1; // Stale during reentrancy!
}

// Protocol B relies on Protocol A's price
function liquidate(address user) public {
    uint price = protocolA.getPrice(); // Gets manipulated price!
    // ... liquidation logic
}
```

#### 2.4 Cross-Contract Reentrancy

Multiple contracts share state, allowing reentrancy across contract boundaries.

### Mitigation Strategies

**1. ReentrancyGuard (OpenZeppelin)**
```solidity
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract Secure is ReentrancyGuard {
    function withdraw() public nonReentrant {
        // Protected!
    }
}
```

**2. Checks-Effects-Interactions Pattern**
```solidity
function action() public {
    // 1. Checks
    require(condition);

    // 2. Effects (state changes)
    state = newState;

    // 3. Interactions (external calls)
    externalContract.call();
}
```

**3. Pull Payment Pattern**
```solidity
mapping(address => uint) public pendingWithdrawals;

function withdraw() public {
    uint amount = pendingWithdrawals[msg.sender];
    pendingWithdrawals[msg.sender] = 0;
    payable(msg.sender).transfer(amount);
}
```

### Detection Tools
- **Slither**: `reentrancy-eth`, `reentrancy-no-eth`, `reentrancy-benign`
- **Mythril**: Symbolic execution detects reentrancy paths
- **Echidna**: Property-based testing with invariants
- **Foundry**: Invariant testing with `forge test`

### Real-World Examples
- The DAO Hack (2016): $60M stolen
- Cream Finance (2021): $130M exploit
- 2024 exploits: $35.7M total

---

## 3. Price Oracle Manipulation

**OWASP Rank**: #2 (2025) - New major category
**2024 Losses**: $8.8 Million (direct) + oracle-related: $52M
**Severity**: CRITICAL for DeFi

### Description
Attackers exploit weak oracle mechanisms to manipulate asset prices, causing forced liquidations, incorrect valuations, or arbitrage opportunities.

### Attack Vectors

#### 3.1 Single Source Oracle

**Vulnerable Code:**
```solidity
interface IOracle {
    function getPrice() external view returns (uint);
}

contract DeFiProtocol {
    IOracle public oracle;

    function liquidate(address user) public {
        // CRITICAL: Single point of failure!
        uint price = oracle.getPrice();
        // ... liquidation logic
    }
}
```

**Problem**: Attacker can manipulate the single oracle source.

#### 3.2 Flash Loan Price Manipulation

**Attack Pattern:**
```solidity
// 1. Take flash loan of Token A
// 2. Swap massive amount: A -> B (crashes B price on DEX)
// 3. Protocol reads manipulated price from DEX
// 4. Exploit protocol with fake price
// 5. Reverse swap
// 6. Repay flash loan + profit
```

**Real Example - Polter Finance:**
```
1. Flash loan BOO tokens
2. Manipulated BOO price on SpookySwap
3. Used inflated price to borrow from Polter
4. Profit: $313k+
```

#### 3.3 Low Liquidity Manipulation

**Vulnerable Setup:**
```solidity
// Using low-liquidity pool as price source
uint price = (reserveA * 1e18) / reserveB;
```

**Attack**: Small trade in low-liquidity pool causes huge price impact.

### Mitigation Strategies

**1. Multi-Oracle Architecture**
```solidity
contract SecureOracle {
    IChainlink public chainlink;
    IPyth public pyth;
    ITellor public tellor;

    function getPrice() public view returns (uint) {
        uint p1 = chainlink.latestAnswer();
        uint p2 = pyth.getPrice();
        uint p3 = tellor.getPrice();

        // Use median or validate deviation
        return median(p1, p2, p3);
    }
}
```

**2. Time-Weighted Average Price (TWAP)**
```solidity
function getTWAP(uint period) public view returns (uint) {
    uint[] memory prices;
    for (uint i = 0; i < period; i++) {
        prices[i] = getPriceAtBlock(block.number - i);
    }
    return average(prices);
}
```

**3. Price Deviation Checks**
```solidity
function getPrice() public view returns (uint) {
    uint newPrice = oracle.getPrice();
    uint lastPrice = previousPrice;

    // Reject if price changed > 10% in one block
    uint deviation = abs(newPrice - lastPrice) * 100 / lastPrice;
    require(deviation < 10, "Price manipulation detected");

    previousPrice = newPrice;
    return newPrice;
}
```

**4. Liquidity Depth Requirements**
```solidity
function getPrice() public view returns (uint) {
    (uint reserve0, uint reserve1, ) = pair.getReserves();
    require(reserve0 > MIN_LIQUIDITY && reserve1 > MIN_LIQUIDITY);
    return (reserve0 * 1e18) / reserve1;
}
```

### Detection Tools
- **Foundry**: Simulate flash loan attacks in tests
- **Echidna**: Invariant testing for price bounds
- **Tenderly**: Transaction simulation with price changes
- **Manual Review**: Essential for oracle architecture

### Real-World Examples
- Mango Markets (2022): $114M via oracle manipulation
- Polter Finance (2025): $313K BOO token manipulation
- Euler Finance (2023): $197M (included oracle issues)

---

## 4. Arithmetic Issues

**OWASP Rank**: #8 (2025) - Down from #2 due to Solidity 0.8.0+
**Severity**: HIGH (Legacy code), LOW (Modern Solidity)

### Description
Integer overflow/underflow, division by zero, and precision loss issues.

### 4.1 Integer Overflow/Underflow

**Solidity < 0.8.0 - Vulnerable:**
```solidity
function add(uint a, uint b) public pure returns (uint) {
    return a + b; // Can overflow!
}

uint8 balance = 255;
balance = balance + 1; // Wraps to 0
```

**Solidity >= 0.8.0 - Protected:**
```solidity
// Built-in overflow protection - reverts on overflow
uint8 balance = 255;
balance = balance + 1; // Reverts automatically
```

**Explicit Unchecked (Be Careful!):**
```solidity
unchecked {
    // Overflow protection disabled for gas optimization
    counter++;
}
```

### 4.2 Division by Zero

**Vulnerable Code:**
```solidity
function calculateShare(uint amount, uint totalSupply) public pure returns (uint) {
    // CRITICAL: What if totalSupply is 0?
    return amount * 1e18 / totalSupply;
}
```

**Secure Code:**
```solidity
function calculateShare(uint amount, uint totalSupply) public pure returns (uint) {
    require(totalSupply > 0, "Division by zero");
    return amount * 1e18 / totalSupply;
}
```

### 4.3 Precision Loss

**Vulnerable Code:**
```solidity
// WRONG: Integer division loses precision
uint fee = amount * 25 / 10000; // 0.25%
uint result = principal / rate * time; // Loss of precision!
```

**Secure Code:**
```solidity
// CORRECT: Multiply before divide
uint fee = (amount * 25) / 10000;
uint result = (principal * time) / rate;

// Use higher precision
uint result = (principal * time * 1e18) / rate / 1e18;
```

### 4.4 Truncation in Division

**Problem:**
```solidity
uint a = 3;
uint b = 2;
uint result = a / b; // result = 1 (not 1.5)
```

**Solution for Percentages:**
```solidity
uint BASIS_POINTS = 10000;
uint feePercentage = 250; // 2.5%
uint fee = (amount * feePercentage) / BASIS_POINTS;
```

### Detection Tools
- **Slither**: `divide-before-multiply`, `weak-prng`
- **Mythril**: Arithmetic checks
- **Foundry**: Property testing for bounds
- **Certora**: Formal verification of mathematical properties

---

## 5. Logic Errors

**OWASP Rank**: #3 (2025) - Up from #7
**2024 Losses**: $63.8 Million
**Severity**: HIGH to CRITICAL

### Description
Flaws in business logic leading to unintended outcomes: incorrect token distribution, miscalculated interest, state machine errors.

### Common Patterns

#### 5.1 Incorrect State Transitions

**Vulnerable Code:**
```solidity
enum State { Pending, Active, Closed }
State public state;

function activate() public {
    state = State.Active; // Missing validation!
}

function close() public {
    state = State.Closed; // Can close from any state!
}
```

**Secure Code:**
```solidity
function activate() public {
    require(state == State.Pending, "Invalid state");
    state = State.Active;
}

function close() public {
    require(state == State.Active, "Must be active to close");
    state = State.Closed;
}
```

#### 5.2 Incorrect Reward Calculation

**Vulnerable Code:**
```solidity
function claimRewards() public {
    uint reward = balanceOf[msg.sender] * rewardRate;
    // CRITICAL: Can claim multiple times!
    token.transfer(msg.sender, reward);
}
```

**Secure Code:**
```solidity
mapping(address => uint) public lastClaimTime;

function claimRewards() public {
    uint timeSinceLastClaim = block.timestamp - lastClaimTime[msg.sender];
    uint reward = balanceOf[msg.sender] * rewardRate * timeSinceLastClaim;

    lastClaimTime[msg.sender] = block.timestamp;
    token.transfer(msg.sender, reward);
}
```

#### 5.3 Flash Loan Vulnerability in Logic

**Vulnerable Code:**
```solidity
function vote(uint proposalId) public {
    uint votingPower = token.balanceOf(msg.sender);
    proposals[proposalId].votes += votingPower;
}
```

**Attack**: Get flash loan → Vote with massive balance → Return loan

**Secure Code:**
```solidity
mapping(address => mapping(uint => bool)) public hasVoted;

function vote(uint proposalId) public {
    require(!hasVoted[msg.sender][proposalId], "Already voted");

    uint votingPower = token.balanceOf(msg.sender);
    require(votingPower > 0, "No voting power");

    proposals[proposalId].votes += votingPower;
    hasVoted[msg.sender][proposalId] = true;
}
```

#### 5.4 Rounding Errors in DeFi

**Vulnerable Code:**
```solidity
// AMM constant product formula: x * y = k
function swap(uint amountIn) public returns (uint amountOut) {
    uint k = reserve0 * reserve1;
    reserve0 += amountIn;
    reserve1 = k / reserve0; // CRITICAL: Truncation!
    amountOut = reserve1Old - reserve1;
}
```

### Detection Tools
- **Manual Review**: Essential for business logic
- **Foundry**: Invariant testing
- **Echidna**: Property-based fuzzing
- **Certora**: Formal verification of invariants

---

## 6. Input Validation

**OWASP Rank**: #5 (2025) - New addition
**2024 Losses**: $14.6 Million
**Severity**: MEDIUM to HIGH

### Description
Failure to validate user inputs allows attackers to inject malicious data, causing unexpected behaviors.

### Common Issues

#### 6.1 Missing Address Validation

**Vulnerable Code:**
```solidity
function setAdmin(address _admin) public onlyOwner {
    admin = _admin; // CRITICAL: What if _admin is address(0)?
}
```

**Secure Code:**
```solidity
function setAdmin(address _admin) public onlyOwner {
    require(_admin != address(0), "Invalid address");
    admin = _admin;
}
```

#### 6.2 Missing Amount Validation

**Vulnerable Code:**
```solidity
function deposit(uint amount) public {
    token.transferFrom(msg.sender, address(this), amount);
    balances[msg.sender] += amount;
}
```

**Issues**:
- What if amount is 0?
- What if amount is type(uint).max?

**Secure Code:**
```solidity
function deposit(uint amount) public {
    require(amount > 0, "Amount must be positive");
    require(amount <= MAX_DEPOSIT, "Amount too large");

    token.transferFrom(msg.sender, address(this), amount);
    balances[msg.sender] += amount;
}
```

#### 6.3 Array Length Validation

**Vulnerable Code:**
```solidity
function batchTransfer(address[] memory recipients, uint[] memory amounts) public {
    for (uint i = 0; i < recipients.length; i++) {
        // CRITICAL: What if arrays have different lengths?
        token.transfer(recipients[i], amounts[i]);
    }
}
```

**Secure Code:**
```solidity
function batchTransfer(address[] memory recipients, uint[] memory amounts) public {
    require(recipients.length == amounts.length, "Length mismatch");
    require(recipients.length > 0 && recipients.length <= 100, "Invalid length");

    for (uint i = 0; i < recipients.length; i++) {
        require(recipients[i] != address(0), "Invalid recipient");
        require(amounts[i] > 0, "Invalid amount");
        token.transfer(recipients[i], amounts[i]);
    }
}
```

### Detection Tools
- **Slither**: `missing-zero-check`, `uninitialized-state`
- **Manual Review**: Essential

---

## 7. External Call Safety

**OWASP Rank**: #6 (2025)
**2024 Losses**: $550.7K
**Severity**: MEDIUM to HIGH

### Description
Failing to verify success of external calls leads to incorrect assumptions about transaction outcomes.

### 7.1 Unchecked Low-Level Calls

**Vulnerable Code:**
```solidity
function sendEther(address recipient, uint amount) public {
    // CRITICAL: Ignores return value!
    recipient.call{value: amount}("");
}
```

**Secure Code:**
```solidity
function sendEther(address recipient, uint amount) public {
    (bool success, ) = recipient.call{value: amount}("");
    require(success, "Transfer failed");
}
```

### 7.2 Unchecked Token Transfers

**Vulnerable Code:**
```solidity
function withdrawTokens(address token, uint amount) public {
    // CRITICAL: Some tokens don't revert on failure!
    IERC20(token).transfer(msg.sender, amount);
}
```

**Secure Code:**
```solidity
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

function withdrawTokens(address token, uint amount) public {
    SafeERC20.safeTransfer(IERC20(token), msg.sender, amount);
}
```

### Detection Tools
- **Slither**: `unchecked-transfer`, `unchecked-lowlevel`
- **Mythril**: External call analysis

---

## 8. Flash Loan Attacks

**OWASP Rank**: #7 (2025) - New distinct category
**2024 Losses**: $33.8 Million
**Severity**: HIGH for DeFi

### Description
Flash loans enable attackers to borrow massive amounts without collateral, execute multiple actions in a single transaction to exploit protocols.

### Attack Patterns

#### 8.1 Price Manipulation with Flash Loans

**Attack Flow:**
```
1. Flash loan 1,000,000 USDC
2. Swap USDC → TOKEN (crashes TOKEN price)
3. Use manipulated price to liquidate positions
4. Swap back TOKEN → USDC (profit from liquidations)
5. Repay flash loan
6. Keep profit
```

#### 8.2 Governance Attacks

**Vulnerable Code:**
```solidity
function vote(uint proposalId, bool support) public {
    uint votes = governanceToken.balanceOf(msg.sender);
    proposals[proposalId].votes[support] += votes;
}
```

**Attack**:
1. Flash loan governance tokens
2. Vote on malicious proposal
3. Return tokens (vote remains!)

**Mitigation:**
```solidity
mapping(address => uint) public voteLockTimestamp;

function lockTokensForVoting(uint amount) public {
    governanceToken.transferFrom(msg.sender, address(this), amount);
    votingPower[msg.sender] = amount;
    voteLockTimestamp[msg.sender] = block.timestamp + LOCK_PERIOD;
}

function vote(uint proposalId, bool support) public {
    require(voteLockTimestamp[msg.sender] <= block.timestamp, "Tokens locked");
    proposals[proposalId].votes[support] += votingPower[msg.sender];
}
```

### Detection Tools
- **Foundry**: Simulate flash loan attacks in tests
- **Manual Review**: Essential for DeFi mechanisms

---

## 9. Randomness Issues

**OWASP Rank**: #9 (2025)
**Severity**: HIGH for gambling/gaming

### Vulnerable Sources

**Bad:**
```solidity
// CRITICAL: All predictable!
uint random = uint(blockhash(block.number - 1)); // Miners can manipulate
uint random = uint(keccak256(abi.encodePacked(block.timestamp))); // Predictable
uint random = uint(keccak256(abi.encodePacked(msg.sender, block.number))); // Predictable
```

**Better:**
```solidity
// Use Chainlink VRF
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";

contract RandomNumber is VRFConsumerBase {
    bytes32 internal keyHash;
    uint256 internal fee;

    function getRandomNumber() public returns (bytes32 requestId) {
        return requestRandomness(keyHash, fee);
    }

    function fulfillRandomness(bytes32 requestId, uint256 randomness) internal override {
        // Use randomness here
    }
}
```

### Detection Tools
- **Slither**: `weak-prng`
- **Manual Review**: Check randomness sources

---

## 10. Denial of Service

**OWASP Rank**: #10 (2025)
**Severity**: MEDIUM to HIGH

### 10.1 Unbounded Loops

**Vulnerable Code:**
```solidity
address[] public users;

function distributeRewards() public {
    // CRITICAL: Can run out of gas!
    for (uint i = 0; i < users.length; i++) {
        token.transfer(users[i], reward);
    }
}
```

**Secure Code:**
```solidity
uint public lastProcessedIndex;

function distributeRewards(uint batchSize) public {
    uint endIndex = min(lastProcessedIndex + batchSize, users.length);

    for (uint i = lastProcessedIndex; i < endIndex; i++) {
        token.transfer(users[i], reward);
    }

    lastProcessedIndex = endIndex;
}
```

### 10.2 Block Gas Limit DoS

**Vulnerable Code:**
```solidity
function vote(address candidate) public {
    voters.push(msg.sender); // Array grows unbounded!
    votes[candidate]++;
}
```

### Detection Tools
- **Slither**: `costly-loop`
- **Foundry**: Gas profiling

---

## 11. Additional EVM Vulnerabilities

### 11.1 Front-Running / MEV

**Attack**: Attacker observes pending transactions and submits their own with higher gas.

**Mitigation**: Use commit-reveal schemes or private mempools.

### 11.2 Timestamp Dependence

**Vulnerable:**
```solidity
require(block.timestamp > deadline); // Miners can manipulate ±15 seconds
```

### 11.3 Signature Replay

**Vulnerable:**
```solidity
function claimWithSignature(bytes memory signature) public {
    address signer = recoverSigner(signature);
    // CRITICAL: Can replay signature!
}
```

**Secure:**
```solidity
mapping(bytes32 => bool) public usedSignatures;

function claimWithSignature(bytes memory signature) public {
    bytes32 sigHash = keccak256(signature);
    require(!usedSignatures[sigHash], "Signature already used");
    usedSignatures[sigHash] = true;
}
```

### 11.4 Contract Size Limitations

Maximum contract size: 24KB. Use proxy patterns for larger systems.

---

# Solana/Rust Vulnerabilities

## 12. Account Validation Issues

**Severity**: CRITICAL for Solana
**Common Impact**: Unauthorized access, fund theft

### Description
Solana's account model requires explicit validation. Missing checks allow attackers to substitute accounts.

### 12.1 Missing Owner Checks

**Vulnerable Code (Rust):**
```rust
pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let account = &accounts[0];

    // CRITICAL: No owner validation!
    let mut data = account.try_borrow_mut_data()?;
    // ... modify data
}
```

**Secure Code:**
```rust
pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let account = &accounts[0];

    // Validate owner
    if account.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }

    let mut data = account.try_borrow_mut_data()?;
    // ... modify data
}
```

### 12.2 Missing Signer Checks

**Vulnerable Code:**
```rust
pub fn withdraw(
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let user_account = &accounts[0];

    // CRITICAL: Anyone can withdraw!
    **user_account.try_borrow_mut_lamports()? -= amount;
}
```

**Secure Code:**
```rust
pub fn withdraw(
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let user_account = &accounts[0];

    // Verify signer
    if !user_account.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    **user_account.try_borrow_mut_lamports()? -= amount;
}
```

### 12.3 Anchor Framework Protection

**Secure Code (Anchor):**
```rust
use anchor_lang::prelude::*;

#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut, has_one = owner)]
    pub user_account: Account<'info, UserAccount>,

    #[account(mut)]
    pub owner: Signer<'info>,
}
```

Anchor provides built-in validation:
- `Signer<'info>`: Automatic signer check
- `has_one = owner`: Validates account relationship
- `#[account(mut)]`: Validates mutability

### Detection Tools
- **Anchor Lints**: Built-in validation
- **Cargo Clippy**: Some validation checks
- **Manual Review**: Essential

---

## 13. PDA (Program Derived Address) Vulnerabilities

**Severity**: CRITICAL
**Impact**: Account spoofing, unauthorized access

### Description
PDAs are addresses derived from seeds and program ID. Improper derivation/validation allows attacks.

### 13.1 PDA Seed Collisions

**Vulnerable Code:**
```rust
// CRITICAL: Can collide!
let seeds = &[
    b"voting",
    &session_id.to_le_bytes(), // Predictable!
];
let (pda, bump) = Pubkey::find_program_address(seeds, program_id);
```

**Attack**: Attacker creates session_id that collides with existing PDA.

**Secure Code:**
```rust
let seeds = &[
    b"voting_v1", // Version prefix
    user.key.as_ref(), // User-specific
    &session_id.to_le_bytes(),
    &nonce.to_le_bytes(), // Additional entropy
];
let (pda, bump) = Pubkey::find_program_address(seeds, program_id);
```

### 13.2 Missing Bump Seed Validation

**Vulnerable Code:**
```rust
pub fn create_pda(
    seeds: &[&[u8]],
    bump: u8,
) -> Result<Pubkey, ProgramError> {
    // CRITICAL: Doesn't validate bump is canonical!
    Pubkey::create_program_address(seeds, program_id)
}
```

**Secure Code:**
```rust
pub fn create_pda(
    seeds: &[&[u8]],
    expected_pda: &Pubkey,
) -> Result<(Pubkey, u8), ProgramError> {
    let (pda, bump) = Pubkey::find_program_address(seeds, program_id);

    if pda != *expected_pda {
        return Err(ProgramError::InvalidSeeds);
    }

    Ok((pda, bump))
}
```

### 13.3 Anchor PDA Validation

**Secure Code (Anchor):**
```rust
#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8,
        seeds = [b"user_account", user.key().as_ref()],
        bump, // Anchor validates canonical bump automatically!
    )]
    pub user_account: Account<'info, UserAccount>,

    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}
```

### Detection Tools
- **Anchor**: Automatic PDA validation
- **Manual Review**: Essential for custom PDA logic

---

## 14. Integer Safety in Rust

**Severity**: HIGH
**Impact**: Overflow/underflow in production

### Description
Rust's overflow checks are **DISABLED in release mode** by default! Solana programs use release mode.

### Vulnerable Code

```rust
pub fn add_funds(amount: u64) -> Result<u64, ProgramError> {
    // CRITICAL: Overflows silently in release mode!
    let new_balance = balance + amount;
    Ok(new_balance)
}
```

### Secure Approaches

**1. Checked Math:**
```rust
pub fn add_funds(amount: u64) -> Result<u64, ProgramError> {
    let new_balance = balance
        .checked_add(amount)
        .ok_or(ProgramError::ArithmeticOverflow)?;
    Ok(new_balance)
}
```

**2. Saturating Math:**
```rust
// Caps at max value instead of wrapping
let new_balance = balance.saturating_add(amount);
```

**3. Wrapping Math (Explicit):**
```rust
// Only use when overflow is intended!
let counter = counter.wrapping_add(1);
```

### Detection Tools
- **Clippy**: `arithmetic_overflow` (limited)
- **Custom Linters**: Check for unchecked arithmetic
- **Manual Review**: Essential

---

## 15. Deserialization Vulnerabilities

**Severity**: CRITICAL
**Impact**: Type confusion, memory corruption

### 15.1 Type Cosplay

**Vulnerable Code:**
```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct AdminAccount {
    pub is_admin: bool,
    pub authority: Pubkey,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct UserAccount {
    pub is_admin: bool, // Same layout as AdminAccount!
    pub authority: Pubkey,
}

pub fn admin_action(account: &AccountInfo) -> ProgramResult {
    // CRITICAL: Deserializes without type checking!
    let admin = AdminAccount::try_from_slice(&account.data.borrow())?;

    if admin.is_admin {
        // Attacker can pass UserAccount with is_admin = true!
    }
}
```

**Secure Code:**
```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct AdminAccount {
    pub discriminator: [u8; 8], // Type identifier
    pub is_admin: bool,
    pub authority: Pubkey,
}

pub fn admin_action(account: &AccountInfo) -> ProgramResult {
    let data = account.data.borrow();

    // Verify discriminator
    if data[0..8] != ADMIN_ACCOUNT_DISCRIMINATOR {
        return Err(ProgramError::InvalidAccountData);
    }

    let admin = AdminAccount::try_from_slice(&data)?;
    // ... safe to use
}
```

**Anchor Automatic Protection:**
```rust
#[account]
pub struct AdminAccount {
    pub is_admin: bool,
    pub authority: Pubkey,
}
// Anchor adds 8-byte discriminator automatically!
```

### Detection Tools
- **Anchor**: Automatic discriminators
- **Manual Review**: Essential for raw programs

---

## 16. CPI (Cross-Program Invocation) Security

**Severity**: CRITICAL
**Impact**: Unauthorized program execution

### 16.1 Unchecked CPI Calls

**Vulnerable Code:**
```rust
pub fn transfer_tokens(
    token_program: &AccountInfo,
    from: &AccountInfo,
    to: &AccountInfo,
    amount: u64,
) -> ProgramResult {
    // CRITICAL: No validation of token_program!
    invoke(
        &transfer_instruction,
        &[token_program, from, to],
    )?;
}
```

**Attack**: Attacker passes malicious program instead of real token program.

**Secure Code:**
```rust
use spl_token::ID as TOKEN_PROGRAM_ID;

pub fn transfer_tokens(
    token_program: &AccountInfo,
    from: &AccountInfo,
    to: &AccountInfo,
    amount: u64,
) -> ProgramResult {
    // Validate program ID
    if token_program.key != &TOKEN_PROGRAM_ID {
        return Err(ProgramError::IncorrectProgramId);
    }

    invoke(
        &transfer_instruction,
        &[token_program, from, to],
    )?;
}
```

### Detection Tools
- **Manual Review**: Essential
- **Anchor**: Provides type-safe CPI helpers

---

## 17. Additional Solana Vulnerabilities

### 17.1 Account Reallocation

**Issue**: Accounts can be reallocated, changing their size/data.

### 17.2 Rent Exemption

**Vulnerable Code:**
```rust
// CRITICAL: Account might get cleaned up!
invoke(
    &system_instruction::create_account(...),
    &[...],
)?;
```

**Secure**: Always ensure rent exemption:
```rust
let rent = Rent::get()?;
let min_balance = rent.minimum_balance(account_size);
```

### 17.3 Close Account Vulnerabilities

**Vulnerable Code:**
```rust
pub fn close_account(account: &AccountInfo) -> ProgramResult {
    // CRITICAL: Can close wrong account!
    **account.try_borrow_mut_lamports()? = 0;
}
```

### 17.4 Duplicate Mutable Accounts

**Vulnerable Code:**
```rust
pub fn swap(
    accounts: &[AccountInfo],
) -> ProgramResult {
    let account_a = &accounts[0];
    let account_b = &accounts[1];

    // CRITICAL: What if account_a == account_b?
    let mut data_a = account_a.try_borrow_mut_data()?;
    let mut data_b = account_b.try_borrow_mut_data()?; // Panics!
}
```

**Secure Code:**
```rust
if account_a.key == account_b.key {
    return Err(ProgramError::InvalidArgument);
}
```

---

# Detection Tool Matrix

## EVM Tools

| Tool | Type | Speed | Coverage | Best For |
|------|------|-------|----------|----------|
| **Slither** | Static | <1s | High | All audits (primary) |
| **Mythril** | Symbolic | Slow | Deep | Complex logic |
| **Echidna** | Fuzzing | Medium | Invariants | Property testing |
| **Foundry** | Fuzzing | Fast | Invariants | Dev testing |
| **Certora** | Formal | Slow | Mathematical | Critical DeFi |
| **Securify2** | Static | Fast | Semantic | Complementary |
| **Tenderly** | Runtime | Fast | Simulation | Pre-deployment |

## Solana Tools

| Tool | Type | Coverage | Best For |
|------|------|----------|----------|
| **Cargo Audit** | Dependency | Dependencies | All projects |
| **Clippy** | Linter | Common bugs | Development |
| **Anchor Lints** | Static | Solana-specific | Anchor projects |
| **solana-test** | Testing | Integration | All projects |
| **Kangaroo** | Fuzzing | Deep | Advanced testing |
| **Rudra** | Static | Memory safety | Unsafe code |
| **VRust** | Static | 8 vuln types | All projects |

---

# Severity Classification

## Critical
- Direct fund loss possible
- Complete protocol compromise
- Examples: Reentrancy, access control, PDA issues

## High
- Significant impact on protocol
- Large financial loss potential
- Examples: Oracle manipulation, logic errors

## Medium
- Limited impact
- Specific conditions required
- Examples: DoS, input validation

## Low
- Minimal impact
- Best practice violations
- Examples: Gas optimization, code quality

---

# Next Steps

1. Review [TOOL_INTEGRATION.md](./TOOL_INTEGRATION.md) for setup
2. Check [AI_PATTERNS.md](./AI_PATTERNS.md) for analysis workflows
3. See [BEST_PRACTICES.md](./BEST_PRACTICES.md) for secure coding
4. Explore [examples/](../examples/) for test cases

---

**Remember**: No combination of tools replaces manual expert review for high-value protocols!
