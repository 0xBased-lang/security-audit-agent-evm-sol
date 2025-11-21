/**
 * VULNERABLE SOLANA PROGRAM: Integer Overflow
 *
 * INTENTIONALLY VULNERABLE - FOR TESTING ONLY
 *
 * Vulnerability: Unchecked arithmetic operations (overflow/underflow)
 * Expected Detection: clippy-agent (integer_arithmetic lint), cargo-audit-agent
 * Severity: CRITICAL
 *
 * Attack Scenario:
 * 1. Attacker deposits u64::MAX tokens
 * 2. Attacker deposits 1 more token
 * 3. Balance overflows to 0
 * 4. Attacker can withdraw unlimited tokens
 *
 * Real-world: Numerous Solana programs vulnerable to overflow exploits
 */

use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    msg,
    program_error::ProgramError,
    pubkey::Pubkey,
};
use borsh::{BorshDeserialize, BorshSerialize};

entrypoint!(process_instruction);

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct UserAccount {
    pub balance: u64,
    pub total_deposited: u64,
    pub reward_multiplier: u8,
}

pub fn process_instruction(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let instruction = instruction_data
        .get(0)
        .ok_or(ProgramError::InvalidInstructionData)?;

    match instruction {
        0 => process_deposit(accounts, instruction_data),
        1 => process_withdraw(accounts, instruction_data),
        2 => process_calculate_reward(accounts),
        3 => process_multiply_balance(accounts, instruction_data),
        _ => Err(ProgramError::InvalidInstructionData),
    }
}

/// VULNERABLE: Unchecked addition (overflow)
fn process_deposit(
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let user_account = next_account_info(accounts_iter)?;

    let amount = u64::from_le_bytes(
        instruction_data[1..9]
            .try_into()
            .map_err(|_| ProgramError::InvalidInstructionData)?
    );

    let mut data = user_account.try_borrow_mut_data()?;
    let mut user = UserAccount::try_from_slice(&data)?;

    // CRITICAL VULNERABILITY: Unchecked addition!
    // If balance + amount > u64::MAX, it wraps to small number
    user.balance = user.balance + amount;  // ← Can overflow!
    user.total_deposited = user.total_deposited + amount;  // ← Can overflow!

    user.serialize(&mut &mut data[..])?;

    msg!("Deposited {} (may have overflowed!)", amount);
    msg!("New balance: {} (possibly wrapped)", user.balance);
    Ok(())
}

/// VULNERABLE: Unchecked subtraction (underflow)
fn process_withdraw(
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let user_account = next_account_info(accounts_iter)?;

    let amount = u64::from_le_bytes(
        instruction_data[1..9]
            .try_into()
            .map_err(|_| ProgramError::InvalidInstructionData)?
    );

    let mut data = user_account.try_borrow_mut_data()?;
    let mut user = UserAccount::try_from_slice(&data)?;

    // CRITICAL VULNERABILITY: No balance check before subtraction!
    // If amount > balance, underflows to u64::MAX
    user.balance = user.balance - amount;  // ← Can underflow!

    user.serialize(&mut &mut data[..])?;

    msg!("Withdrew {} (may have underflowed!)", amount);
    msg!("New balance: {} (possibly wrapped to MAX)", user.balance);
    Ok(())
}

/// VULNERABLE: Unchecked multiplication (overflow)
fn process_calculate_reward(
    accounts: &[AccountInfo],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let user_account = next_account_info(accounts_iter)?;

    let mut data = user_account.try_borrow_mut_data()?;
    let mut user = UserAccount::try_from_slice(&data)?;

    // CRITICAL VULNERABILITY: Unchecked multiplication!
    // balance * reward_multiplier can overflow
    let reward = user.balance * (user.reward_multiplier as u64);  // ← Can overflow!

    user.balance = user.balance + reward;  // ← Double overflow risk!

    user.serialize(&mut &mut data[..])?;

    msg!("Calculated reward: {} (may be wrong due to overflow)", reward);
    Ok(())
}

/// VULNERABLE: Unchecked division (div by zero not checked either)
fn process_multiply_balance(
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let user_account = next_account_info(accounts_iter)?;

    let multiplier = u64::from_le_bytes(
        instruction_data[1..9]
            .try_into()
            .map_err(|_| ProgramError::InvalidInstructionData)?
    );

    let mut data = user_account.try_borrow_mut_data()?;
    let mut user = UserAccount::try_from_slice(&data)?;

    // VULNERABILITY 1: Unchecked multiplication
    let new_balance = user.balance * multiplier;  // ← Can overflow!

    // VULNERABILITY 2: If we divide and multiplier is 0, no check
    let avg = user.balance / multiplier;  // ← Div by zero if multiplier == 0!

    user.balance = new_balance;
    user.serialize(&mut &mut data[..])?;

    msg!("Multiplied balance by {} (overflow possible)", multiplier);
    msg!("Average: {} (crash if multiplier was 0)", avg);
    Ok(())
}

/**
 * Attack Scenario 1: Deposit Overflow
 *
 * Initial state:
 * - user.balance = u64::MAX - 100 (18,446,744,073,709,551,515)
 *
 * Attacker deposits 200:
 * - balance + 200 = u64::MAX + 99
 * - Overflows to 99!
 *
 * Result: User had u64::MAX balance, now has 99 balance. Lost everything!
 *
 * Attack Scenario 2: Withdraw Underflow
 *
 * Initial state:
 * - user.balance = 10
 *
 * Attacker withdraws 100:
 * - balance - 100 = 10 - 100
 * - Underflows to u64::MAX - 89!
 *
 * Result: User now has u64::MAX balance, can withdraw unlimited funds!
 *
 * Attack Scenario 3: Reward Multiplication Overflow
 *
 * Initial state:
 * - user.balance = 10,000,000,000,000,000,000 (10^19)
 * - user.reward_multiplier = 10
 *
 * Calculate reward:
 * - reward = balance * multiplier
 * - 10^19 * 10 = 10^20
 * - u64::MAX = 1.8 * 10^19
 * - Overflows!
 *
 * Result: Reward calculation wrong, user gets less than expected
 *
 * FIX 1: Use checked arithmetic (RECOMMENDED)
 *
 * fn process_deposit(...) -> ProgramResult {
 *     ...
 *     // ✅ checked_add returns None on overflow
 *     user.balance = user.balance
 *         .checked_add(amount)
 *         .ok_or(ProgramError::ArithmeticOverflow)?;
 *
 *     user.total_deposited = user.total_deposited
 *         .checked_add(amount)
 *         .ok_or(ProgramError::ArithmeticOverflow)?;
 *     ...
 * }
 *
 * fn process_withdraw(...) -> ProgramResult {
 *     ...
 *     // ✅ checked_sub returns None on underflow
 *     user.balance = user.balance
 *         .checked_sub(amount)
 *         .ok_or(ProgramError::InsufficientFunds)?;
 *     ...
 * }
 *
 * fn process_calculate_reward(...) -> ProgramResult {
 *     ...
 *     // ✅ checked_mul returns None on overflow
 *     let reward = user.balance
 *         .checked_mul(user.reward_multiplier as u64)
 *         .ok_or(ProgramError::ArithmeticOverflow)?;
 *
 *     user.balance = user.balance
 *         .checked_add(reward)
 *         .ok_or(ProgramError::ArithmeticOverflow)?;
 *     ...
 * }
 *
 * fn process_divide(...) -> ProgramResult {
 *     ...
 *     // ✅ checked_div returns None if divisor is 0
 *     let result = numerator
 *         .checked_div(denominator)
 *         .ok_or(ProgramError::InvalidArgument)?;
 *     ...
 * }
 *
 * FIX 2: Add explicit checks before operations
 *
 * fn process_deposit(...) -> ProgramResult {
 *     ...
 *     // ✅ Explicit overflow check
 *     if user.balance > u64::MAX - amount {
 *         msg!("Deposit would overflow balance");
 *         return Err(ProgramError::ArithmeticOverflow);
 *     }
 *
 *     user.balance = user.balance + amount;
 *     ...
 * }
 *
 * fn process_withdraw(...) -> ProgramResult {
 *     ...
 *     // ✅ Explicit underflow/bounds check
 *     if user.balance < amount {
 *         msg!("Insufficient balance");
 *         return Err(ProgramError::InsufficientFunds);
 *     }
 *
 *     user.balance = user.balance - amount;
 *     ...
 * }
 *
 * FIX 3: Use saturating arithmetic (for specific cases)
 *
 * // Saturating operations clamp to min/max instead of wrapping
 * user.balance = user.balance.saturating_add(amount);  // Stops at u64::MAX
 * user.balance = user.balance.saturating_sub(amount);  // Stops at 0
 *
 * // Only use if clamping to limit is acceptable behavior!
 * // Usually, you want to return error instead
 *
 * FIX 4: Use wider types for intermediate calculations
 *
 * // If multiplying u64 values, use u128 for intermediate
 * let balance_u128 = user.balance as u128;
 * let multiplier_u128 = multiplier as u128;
 * let product = balance_u128 * multiplier_u128;
 *
 * if product > u64::MAX as u128 {
 *     return Err(ProgramError::ArithmeticOverflow);
 * }
 *
 * let result = product as u64;
 *
 * FIX 5: Enable Clippy lints to catch unchecked arithmetic
 *
 * // In Cargo.toml or rustc flags:
 * [lints.clippy]
 * integer_arithmetic = "deny"  // Fails build on unchecked arithmetic
 *
 * // This forces you to use checked_* methods
 *
 * BEST PRACTICES:
 *
 * 1. ALWAYS use checked arithmetic for financial operations:
 *    - checked_add, checked_sub, checked_mul, checked_div
 *
 * 2. Validate inputs before arithmetic:
 *    - Check bounds
 *    - Ensure non-zero for division
 *
 * 3. Use appropriate types:
 *    - u64 for token amounts
 *    - u128 for intermediate calculations
 *    - Never use i64 for balances (no negative balances!)
 *
 * 4. Enable Clippy lint `integer_arithmetic`:
 *    #![deny(clippy::integer_arithmetic)]
 *
 * 5. Test with edge cases:
 *    - u64::MAX
 *    - 0
 *    - u64::MAX - 1
 *
 * 6. Use Anchor's constraint system:
 *    #[account(
 *        constraint = amount <= vault.balance @ ErrorCode::InsufficientFunds
 *    )]
 *
 * TESTING:
 *
 * #[test]
 * fn test_deposit_overflow_fails() {
 *     let mut user = UserAccount { balance: u64::MAX - 10, ... };
 *     let result = deposit(&mut user, 20);
 *     assert_eq!(result.unwrap_err(), ProgramError::ArithmeticOverflow);
 * }
 *
 * #[test]
 * fn test_withdraw_underflow_fails() {
 *     let mut user = UserAccount { balance: 10, ... };
 *     let result = withdraw(&mut user, 20);
 *     assert_eq!(result.unwrap_err(), ProgramError::InsufficientFunds);
 * }
 *
 * #[test]
 * fn test_multiply_overflow_fails() {
 *     let balance: u64 = u64::MAX / 2;
 *     let result = balance.checked_mul(3);
 *     assert!(result.is_none());  // Overflow detected!
 * }
 *
 * Common arithmetic operations in Solana:
 * - Token transfers: balance +/- amount
 * - Reward calculation: balance * rate / precision
 * - Price calculation: amount_in * price / decimals
 * - Fee calculation: amount * fee_bps / 10000
 *
 * All of these can overflow if not checked!
 */
