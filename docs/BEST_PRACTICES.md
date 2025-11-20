# Blockchain Security Best Practices

> **Comprehensive secure coding guidelines for EVM and Solana smart contracts**

---

## Table of Contents

1. [EVM/Solidity Best Practices](#evm-best-practices)
2. [Solana/Rust Best Practices](#solana-best-practices)
3. [General Smart Contract Security](#general-security)
4. [DeFi-Specific Considerations](#defi-security)
5. [Testing and Auditing](#testing-auditing)

---

# EVM Best Practices

## 1. Access Control

### ✅ DO

```solidity
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract Secure is Ownable, AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    function adminFunction() public onlyRole(ADMIN_ROLE) {
        // Protected function
    }

    function ownerFunction() public onlyOwner {
        // Owner-only function
    }
}
```

### ❌ DON'T

```solidity
// WRONG: Using tx.origin
function withdraw() public {
    require(tx.origin == owner); // Phishing vulnerable!
}

// WRONG: No access control
function setAdmin(address _admin) public {
    admin = _admin; // Anyone can call!
}
```

## 2. Reentrancy Protection

### ✅ DO

```solidity
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract Secure is ReentrancyGuard {
    mapping(address => uint) balances;

    // Checks-Effects-Interactions pattern + ReentrancyGuard
    function withdraw() public nonReentrant {
        uint amount = balances[msg.sender];
        require(amount > 0, "No balance");

        // Effects: Update state BEFORE external call
        balances[msg.sender] = 0;

        // Interactions: External call LAST
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
    }
}
```

### ❌ DON'T

```solidity
// WRONG: External call before state update
function withdraw() public {
    uint amount = balances[msg.sender];

    (bool success, ) = msg.sender.call{value: amount}("");
    require(success);

    balances[msg.sender] = 0; // TOO LATE!
}
```

## 3. Safe External Calls

### ✅ DO

```solidity
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract Secure {
    using SafeERC20 for IERC20;

    function transferTokens(IERC20 token, address to, uint amount) public {
        // Safe transfer that handles all edge cases
        token.safeTransfer(to, amount);
    }

    function lowLevelCall(address target) public returns (bool) {
        (bool success, ) = target.call{value: 1 ether}("");
        require(success, "Call failed");
        return success;
    }
}
```

### ❌ DON'T

```solidity
// WRONG: Ignoring return values
function transferTokens(IERC20 token, address to, uint amount) public {
    token.transfer(to, amount); // Return value ignored!
}

// WRONG: Unchecked call
function sendEther(address to) public {
    to.call{value: 1 ether}(""); // Success not checked!
}
```

## 4. Integer Safety

### ✅ DO

```solidity
// Solidity 0.8.0+ has built-in overflow protection
pragma solidity ^0.8.0;

contract Secure {
    function add(uint a, uint b) public pure returns (uint) {
        return a + b; // Reverts on overflow
    }

    // Use unchecked only when certain no overflow
    function increment(uint counter) public pure returns (uint) {
        unchecked {
            return counter + 1; // Gas optimization
        }
    }

    // Always multiply before divide
    function calculateFee(uint amount) public pure returns (uint) {
        return (amount * FEE_PERCENT) / 100;
    }
}
```

### ❌ DON'T

```solidity
// WRONG: Division before multiplication (precision loss)
function calculateShare(uint amount, uint rate) public pure returns (uint) {
    return amount / 100 * rate; // Loses precision!
}

// WRONG: No zero check
function divide(uint a, uint b) public pure returns (uint) {
    return a / b; // Can divide by zero!
}
```

## 5. Oracle Security

### ✅ DO

```solidity
interface IChainlinkOracle {
    function latestRoundData() external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    );
}

contract Secure {
    IChainlinkOracle public oracle1;
    IChainlinkOracle public oracle2;

    uint public constant MAX_PRICE_DEVIATION = 10; // 10%
    uint public constant STALENESS_THRESHOLD = 3600; // 1 hour

    function getPrice() public view returns (uint) {
        (
            uint80 roundId1,
            int256 price1,
            ,
            uint256 updatedAt1,
            uint80 answeredInRound1
        ) = oracle1.latestRoundData();

        (
            uint80 roundId2,
            int256 price2,
            ,
            uint256 updatedAt2,
            uint80 answeredInRound2
        ) = oracle2.latestRoundData();

        // Validate freshness
        require(
            block.timestamp - updatedAt1 < STALENESS_THRESHOLD,
            "Oracle 1 stale"
        );
        require(
            block.timestamp - updatedAt2 < STALENESS_THRESHOLD,
            "Oracle 2 stale"
        );

        // Validate round completion
        require(answeredInRound1 >= roundId1, "Oracle 1 incomplete");
        require(answeredInRound2 >= roundId2, "Oracle 2 incomplete");

        // Check price deviation
        uint deviation = abs(uint(price1) - uint(price2)) * 100 / uint(price1);
        require(deviation < MAX_PRICE_DEVIATION, "Price deviation too high");

        // Return median of two prices
        return (uint(price1) + uint(price2)) / 2;
    }
}
```

### ❌ DON'T

```solidity
// WRONG: Single oracle, no validation
function getPrice() public view returns (uint) {
    (, int256 price, , , ) = oracle.latestRoundData();
    return uint(price); // No freshness or validity checks!
}
```

## 6. Upgradeable Contracts

### ✅ DO

```solidity
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";

contract SecureUpgradeable is Initializable, OwnableUpgradeable, UUPSUpgradeable {
    uint256 public value;

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    function initialize(uint256 _value) public initializer {
        __Ownable_init();
        __UUPSUpgradeable_init();
        value = _value;
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}
}
```

### ❌ DON'T

```solidity
// WRONG: Unprotected initializer
contract Unsafe {
    function initialize() public {
        // Anyone can call!
    }
}

// WRONG: Using constructor instead of initializer
contract Unsafe {
    constructor(uint _value) {
        value = _value; // Won't work with proxies!
    }
}
```

---

# Solana Best Practices

## 1. Account Validation

### ✅ DO

```rust
use anchor_lang::prelude::*;

#[derive(Accounts)]
pub struct SecureInstruction<'info> {
    // Automatic signer validation
    #[account(mut)]
    pub user: Signer<'info>,

    // PDA validation with seeds
    #[account(
        mut,
        seeds = [b"user_account", user.key().as_ref()],
        bump,
    )]
    pub user_account: Account<'info, UserAccount>,

    // Owner validation
    #[account(
        mut,
        has_one = user @ ErrorCode::Unauthorized,
    )]
    pub user_data: Account<'info, UserData>,

    // Constraint validation
    #[account(
        constraint = user_account.balance >= amount @ ErrorCode::InsufficientFunds,
    )]
    pub source: Account<'info, TokenAccount>,

    // System program validation
    pub system_program: Program<'info, System>,
}
```

### ❌ DON'T

```rust
// WRONG: No validation
pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    data: &[u8],
) -> ProgramResult {
    let account = &accounts[0];
    // No owner check, no signer check!
    let mut account_data = account.try_borrow_mut_data()?;
    // ... dangerous!
}
```

## 2. Integer Safety

### ✅ DO

```rust
use anchor_lang::prelude::*;

pub fn add_funds(ctx: Context<AddFunds>, amount: u64) -> Result<()> {
    let account = &mut ctx.accounts.user_account;

    // ALWAYS use checked arithmetic
    account.balance = account.balance
        .checked_add(amount)
        .ok_or(ErrorCode::ArithmeticOverflow)?;

    Ok(())
}

pub fn calculate_reward(principal: u64, rate: u64) -> Result<u64> {
    let reward = principal
        .checked_mul(rate)
        .ok_or(ErrorCode::ArithmeticOverflow)?
        .checked_div(100)
        .ok_or(ErrorCode::DivisionByZero)?;

    Ok(reward)
}
```

### ❌ DON'T

```rust
// WRONG: Unchecked arithmetic (overflows silently in release mode!)
pub fn add_funds(amount: u64) -> u64 {
    balance + amount // Silent overflow!
}
```

## 3. PDA Security

### ✅ DO

```rust
use anchor_lang::prelude::*;

#[derive(Accounts)]
pub struct InitializeAccount<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8,
        seeds = [
            b"user_account_v1", // Version prefix
            user.key().as_ref(), // User-specific
            &index.to_le_bytes(), // Unique per user
        ],
        bump,
    )]
    pub user_account: Account<'info, UserAccount>,

    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

// Always store bump seed
#[account]
pub struct UserAccount {
    pub bump: u8,
    pub owner: Pubkey,
    pub balance: u64,
}
```

### ❌ DON'T

```rust
// WRONG: Predictable PDA seeds
let (pda, bump) = Pubkey::find_program_address(
    &[b"user"], // Same for all users!
    program_id,
);

// WRONG: Not storing bump
#[account]
pub struct UserAccount {
    // Missing bump field!
    pub owner: Pubkey,
}
```

## 4. CPI Security

### ✅ DO

```rust
use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount, Transfer};

pub fn safe_transfer(ctx: Context<SafeTransfer>, amount: u64) -> Result<()> {
    // Validate program ID
    if ctx.accounts.token_program.key() != token::ID {
        return Err(ErrorCode::InvalidTokenProgram.into());
    }

    // Use Anchor's type-safe CPI
    let cpi_accounts = Transfer {
        from: ctx.accounts.from.to_account_info(),
        to: ctx.accounts.to.to_account_info(),
        authority: ctx.accounts.authority.to_account_info(),
    };

    let cpi_program = ctx.accounts.token_program.to_account_info();
    let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);

    token::transfer(cpi_ctx, amount)?;

    Ok(())
}

#[derive(Accounts)]
pub struct SafeTransfer<'info> {
    #[account(mut)]
    pub from: Account<'info, TokenAccount>,
    #[account(mut)]
    pub to: Account<'info, TokenAccount>,
    pub authority: Signer<'info>,
    pub token_program: Program<'info, Token>, // Type-safe!
}
```

### ❌ DON'T

```rust
// WRONG: No program validation
pub fn unsafe_transfer(
    token_program: &AccountInfo,
    from: &AccountInfo,
    to: &AccountInfo,
) -> ProgramResult {
    // Attacker can pass malicious program!
    invoke(
        &transfer_instruction,
        &[token_program, from, to],
    )?;
}
```

## 5. Account Discriminators

### ✅ DO

```rust
use anchor_lang::prelude::*;

// Anchor automatically adds 8-byte discriminator
#[account]
pub struct UserAccount {
    pub owner: Pubkey,
    pub balance: u64,
}

#[account]
pub struct AdminAccount {
    pub authority: Pubkey,
    pub permissions: u64,
}

// Manual verification if needed
pub fn verify_account_type(account_data: &[u8]) -> Result<()> {
    let discriminator = &account_data[0..8];
    let expected = UserAccount::discriminator();

    if discriminator != expected {
        return Err(ErrorCode::InvalidAccountType.into());
    }

    Ok(())
}
```

### ❌ DON'T

```rust
// WRONG: No discriminator (type confusion possible!)
#[derive(BorshSerialize, BorshDeserialize)]
pub struct Account {
    pub data: u64,
}
```

---

# General Security

## 1. Input Validation

### Always Validate:
- ✅ Address parameters (not zero address)
- ✅ Amount parameters (not zero, within bounds)
- ✅ Array lengths (not empty, not too large)
- ✅ Enum values (within valid range)
- ✅ Timestamps (not in past when required)

## 2. Gas Optimization vs Security

### ✅ Safe Optimizations:
- Use `unchecked` blocks for counter increments (when certain)
- Cache storage variables in memory
- Use appropriate data types (uint256 vs uint128)
- Pack struct variables efficiently

### ❌ Dangerous Optimizations:
- Skipping input validation
- Removing safety checks
- Using assembly without understanding

## 3. Testing Requirements

### Minimum Test Coverage:
- ✅ Unit tests for all functions
- ✅ Integration tests for contract interactions
- ✅ Fuzz testing for input validation
- ✅ Invariant testing for core properties
- ✅ Test failure cases, not just happy paths

### Example (Foundry):
```solidity
function testFuzz_Deposit(uint256 amount) public {
    vm.assume(amount > 0 && amount < type(uint96).max);

    vm.prank(user);
    contract.deposit(amount);

    assertEq(contract.balanceOf(user), amount);
}

function invariant_TotalSupplyEqualsBalances() public {
    uint256 sum = 0;
    for (uint i = 0; i < users.length; i++) {
        sum += contract.balanceOf(users[i]);
    }
    assertEq(contract.totalSupply(), sum);
}
```

---

# DeFi Security

## 1. Flash Loan Protection

```solidity
contract FlashLoanProtected {
    mapping(address => uint) public lastAction;

    modifier noFlashLoan() {
        require(
            lastAction[msg.sender] != block.number,
            "Flash loan detected"
        );
        lastAction[msg.sender] = block.number;
        _;
    }

    function vote(uint proposalId) public noFlashLoan {
        // Protected against flash loan governance attacks
    }
}
```

## 2. Slippage Protection

```solidity
function swap(
    uint amountIn,
    uint amountOutMin, // User-specified minimum
    uint deadline
) public {
    require(block.timestamp <= deadline, "Expired");

    uint amountOut = calculateOutput(amountIn);
    require(amountOut >= amountOutMin, "Slippage too high");

    // Execute swap
}
```

## 3. Oracle Manipulation Prevention

- ✅ Use multiple oracle sources
- ✅ Implement TWAP (Time-Weighted Average Price)
- ✅ Set maximum price deviation thresholds
- ✅ Check oracle freshness and validity
- ✅ Use decentralized oracles (Chainlink, Pyth)

---

# Testing & Auditing

## Pre-Audit Checklist

- [ ] All functions have access control
- [ ] External calls use checks-effects-interactions
- [ ] Integer arithmetic uses safe math
- [ ] All inputs are validated
- [ ] Oracles are properly validated
- [ ] Upgradeable contracts are properly secured
- [ ] Emergency pause mechanism exists
- [ ] Test coverage > 95%
- [ ] Fuzzing tests written
- [ ] Invariant tests written
- [ ] Documentation is complete

## Audit Process

1. **Automated Analysis**: Run Slither, Mythril, etc.
2. **Manual Review**: Expert code review
3. **Formal Verification**: For critical functions (optional)
4. **Testing**: Comprehensive test suite
5. **Fix and Retest**: Address all findings
6. **Final Review**: Verify all fixes

## Post-Deployment

- ✅ Monitor transactions and events
- ✅ Have incident response plan
- ✅ Implement circuit breakers
- ✅ Bug bounty program
- ✅ Continuous monitoring

---

**Remember**: Security is not a one-time effort but an ongoing process!
