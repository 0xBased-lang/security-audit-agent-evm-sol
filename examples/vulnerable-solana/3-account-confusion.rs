/**
 * VULNERABLE SOLANA PROGRAM: Account Confusion / Missing Owner Check
 *
 * INTENTIONALLY VULNERABLE - FOR TESTING ONLY
 *
 * Vulnerability: Missing account owner validation (type cosplay attack)
 * Expected Detection: account-confusion-detector, clippy-agent
 * Severity: CRITICAL
 *
 * Attack Scenario:
 * 1. Attacker creates malicious account with vault-like data structure
 * 2. Attacker passes malicious account as 'vault' parameter
 * 3. Program doesn't verify account owner
 * 4. Attacker can manipulate program logic with fake data
 *
 * Types of attacks:
 * - Type cosplay: Account pretends to be different type
 * - Wrong program owner: Account owned by wrong program
 * - Uninitialized account: Random data interpreted as valid
 */

use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    msg,
    program_error::ProgramError,
    pubkey::Pubkey,
    program_pack::Pack,
};
use borsh::{BorshDeserialize, BorshSerialize};

entrypoint!(process_instruction);

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct Vault {
    pub authority: Pubkey,
    pub balance: u64,
    pub is_initialized: bool,
}

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let instruction = instruction_data
        .get(0)
        .ok_or(ProgramError::InvalidInstructionData)?;

    match instruction {
        0 => process_transfer(program_id, accounts, instruction_data),
        1 => process_withdraw_token(program_id, accounts, instruction_data),
        _ => Err(ProgramError::InvalidInstructionData),
    }
}

/// VULNERABLE: No owner check on vault account!
fn process_transfer(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let authority = next_account_info(accounts_iter)?;
    let vault = next_account_info(accounts_iter)?;  // ← No owner check!
    let recipient = next_account_info(accounts_iter)?;

    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // CRITICAL VULNERABILITY: No owner check!
    // Should verify: vault.owner == program_id

    // Deserialize vault data (could be fake data from attacker's account!)
    let data = vault.try_borrow_data()?;
    let vault_data = Vault::try_from_slice(&data)?;

    // Verify authority matches
    if vault_data.authority != *authority.key {
        msg!("Unauthorized");
        return Err(ProgramError::IllegalOwner);
    }

    // VULNERABILITY: vault could be owned by any program!
    // Attacker can create account with matching authority field

    let amount = u64::from_le_bytes(
        instruction_data[1..9]
            .try_into()
            .map_err(|_| ProgramError::InvalidInstructionData)?
    );

    // Transfer funds from potentially fake vault
    **vault.try_borrow_mut_lamports()? -= amount;
    **recipient.try_borrow_mut_lamports()? += amount;

    msg!("Transferred {} from possibly fake vault", amount);
    Ok(())
}

/// VULNERABLE: No SPL Token program owner check!
fn process_withdraw_token(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let authority = next_account_info(accounts_iter)?;
    let token_account = next_account_info(accounts_iter)?;  // ← No owner check!
    let recipient_token_account = next_account_info(accounts_iter)?;

    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // CRITICAL VULNERABILITY: No check that token_account is owned by SPL Token program!
    // Attacker can pass ANY account, including one they control

    // Should verify:
    // if token_account.owner != &spl_token::ID {
    //     return Err(ProgramError::IllegalOwner);
    // }

    let amount = u64::from_le_bytes(
        instruction_data[1..9]
            .try_into()
            .map_err(|_| ProgramError::InvalidInstructionData)?
    );

    msg!("Attempting to transfer {} tokens", amount);
    msg!("WARNING: token_account owner not verified!");

    // In real code, would call SPL Token transfer
    // But without owner check, attacker can pass fake token account

    Ok(())
}

/**
 * Attack Scenario 1: Type Cosplay on Vault
 *
 * 1. Attacker creates their own account (not owned by this program)
 * 2. Attacker writes Vault-like data to their account:
 *    Vault {
 *        authority: attacker_pubkey,
 *        balance: 1000000,  // ← Fake balance!
 *        is_initialized: true
 *    }
 *
 * 3. Attacker calls process_transfer:
 *    accounts: [
 *        attacker (signer),
 *        attacker_fake_vault,  // ← Owned by attacker, not program!
 *        victim_account
 *    ]
 *
 * 4. Program deserializes fake vault data
 * 5. Authority check passes: vault_data.authority == attacker ✓
 * 6. But vault.owner is attacker's program, not this program!
 * 7. Depending on implementation, could lead to:
 *    - Reading fake balance
 *    - Bypassing checks
 *    - Corrupting state
 *
 * Attack Scenario 2: Wrong Token Account Owner
 *
 * 1. Attacker creates fake "token account" owned by their program
 * 2. Fake account has spl_token::Account-like structure
 * 3. Attacker calls process_withdraw_token with fake token account
 * 4. Program doesn't verify token_account.owner == spl_token::ID
 * 5. Program attempts to work with fake token account
 * 6. Attacker can manipulate balances, mint, authority fields
 *
 * FIX 1: Always verify account owner
 *
 * fn process_transfer(...) -> ProgramResult {
 *     ...
 *     let vault = next_account_info(accounts_iter)?;
 *
 *     // ✅ CRITICAL: Verify account is owned by this program!
 *     if vault.owner != program_id {
 *         msg!("Vault account has incorrect owner");
 *         return Err(ProgramError::IllegalOwner);
 *     }
 *
 *     // Now safe to deserialize
 *     let vault_data = Vault::try_from_slice(&vault.data.borrow())?;
 *     ...
 * }
 *
 * FIX 2: Verify SPL Token account owner
 *
 * fn process_withdraw_token(...) -> ProgramResult {
 *     ...
 *     let token_account = next_account_info(accounts_iter)?;
 *
 *     // ✅ Verify owned by SPL Token program!
 *     if token_account.owner != &spl_token::ID {
 *         msg!("Token account has incorrect owner");
 *         return Err(ProgramError::IllegalOwner);
 *     }
 *
 *     // Now safe to work with token account
 *     ...
 * }
 *
 * FIX 3: Use Anchor framework (automatic checks)
 *
 * #[derive(Accounts)]
 * pub struct Transfer<'info> {
 *     pub authority: Signer<'info>,
 *
 *     #[account(
 *         mut,
 *         has_one = authority  // ← Validates authority field matches
 *     )]
 *     pub vault: Account<'info, Vault>,  // ← Automatically checks owner!
 *
 *     /// CHECK: This account is not read or written
 *     pub recipient: AccountInfo<'info>,
 * }
 *
 * Anchor's Account<'info, T> automatically validates:
 * - Account owner is this program
 * - Account data deserializes to type T
 * - Account has correct discriminator
 *
 * FIX 4: Add discriminator to prevent type confusion
 *
 * #[derive(BorshSerialize, BorshDeserialize)]
 * pub struct Vault {
 *     pub discriminator: [u8; 8],  // ← Unique identifier
 *     pub authority: Pubkey,
 *     pub balance: u64,
 * }
 *
 * const VAULT_DISCRIMINATOR: [u8; 8] = [1, 2, 3, 4, 5, 6, 7, 8];
 *
 * fn validate_vault(account: &AccountInfo) -> Result<Vault, ProgramError> {
 *     let data = account.try_borrow_data()?;
 *     let vault = Vault::try_from_slice(&data)?;
 *
 *     if vault.discriminator != VAULT_DISCRIMINATOR {
 *         return Err(ProgramError::InvalidAccountData);
 *     }
 *
 *     Ok(vault)
 * }
 *
 * BEST PRACTICES:
 *
 * 1. Always verify account.owner for program-owned accounts
 *    if account.owner != program_id { return Err(...) }
 *
 * 2. Verify SPL Token accounts are owned by spl_token::ID
 *    if token_account.owner != &spl_token::ID { return Err(...) }
 *
 * 3. Add discriminators to prevent type confusion
 *
 * 4. Use Anchor framework for automatic validation
 *
 * 5. Validate account is initialized before using
 *    if !vault.is_initialized { return Err(...) }
 *
 * 6. Document expected account owners in code
 *
 * TESTING:
 *
 * #[test]
 * fn test_rejects_wrong_owner() {
 *     let fake_vault = create_account_with_wrong_owner();
 *     let result = process_transfer(&[authority, fake_vault, recipient]);
 *     assert_eq!(result.unwrap_err(), ProgramError::IllegalOwner);
 * }
 *
 * #[test]
 * fn test_rejects_fake_token_account() {
 *     let fake_token = create_non_spl_token_account();
 *     let result = process_withdraw_token(&[authority, fake_token, ...]);
 *     assert_eq!(result.unwrap_err(), ProgramError::IllegalOwner);
 * }
 *
 * Common owner checks needed:
 * - Program accounts → program_id
 * - SPL Token accounts → spl_token::ID
 * - Associated Token accounts → spl_associated_token_account::ID
 * - System accounts → system_program::ID
 * - Rent sysvar → sysvar::rent::ID
 */
