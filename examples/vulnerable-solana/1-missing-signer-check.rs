/**
 * VULNERABLE SOLANA PROGRAM: Missing Signer Check
 *
 * INTENTIONALLY VULNERABLE - FOR TESTING ONLY
 *
 * Vulnerability: Missing signer validation on authority account
 * Expected Detection: signer-validator-agent, clippy-agent
 * Severity: CRITICAL
 *
 * Attack Scenario:
 * 1. Attacker calls withdraw() with ANY account as 'authority'
 * 2. No signer check - any account accepted!
 * 3. Funds transferred from vault to attacker
 * 4. All vault funds stolen
 *
 * Real-world examples:
 * - Wormhole Bridge: $320M (missing signature verification)
 * - Cashio Dollar: $52M (missing signer check on mint authority)
 * - Crema Finance: $8.8M (signer check on wrong account)
 *
 * This is the #1 most critical Solana vulnerability!
 */

use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    msg,
    program_error::ProgramError,
    pubkey::Pubkey,
};

entrypoint!(process_instruction);

pub fn process_instruction(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();

    // Parse instruction
    let instruction = instruction_data
        .get(0)
        .ok_or(ProgramError::InvalidInstructionData)?;

    match instruction {
        0 => process_withdraw(accounts_iter, instruction_data),
        1 => process_transfer(accounts_iter, instruction_data),
        _ => Err(ProgramError::InvalidInstructionData),
    }
}

/// VULNERABLE: Withdraw funds without signer check!
fn process_withdraw(
    accounts_iter: &mut std::slice::Iter<AccountInfo>,
    instruction_data: &[u8],
) -> ProgramResult {
    // Get accounts
    let authority = next_account_info(accounts_iter)?;  // ← Should be signer!
    let vault = next_account_info(accounts_iter)?;

    // CRITICAL VULNERABILITY: No signer check!
    // Should have: if !authority.is_signer { return Err(...) }

    // Parse amount
    let amount = u64::from_le_bytes(
        instruction_data[1..9]
            .try_into()
            .map_err(|_| ProgramError::InvalidInstructionData)?
    );

    msg!("Withdrawing {} lamports", amount);

    // Transfer funds - ANYONE can call this!
    **vault.try_borrow_mut_lamports()? -= amount;
    **authority.try_borrow_mut_lamports()? += amount;

    msg!("Withdrawal successful");
    Ok(())
}

/// VULNERABLE: Transfer with signer check on WRONG account!
fn process_transfer(
    accounts_iter: &mut std::slice::Iter<AccountInfo>,
    instruction_data: &[u8],
) -> ProgramResult {
    let user = next_account_info(accounts_iter)?;  // ← User is signer
    let authority = next_account_info(accounts_iter)?;  // ← But authority is used for auth!
    let from = next_account_info(accounts_iter)?;
    let to = next_account_info(accounts_iter)?;

    // Check if user is signer (WRONG! Should check authority)
    if !user.is_signer {
        msg!("User must be signer");
        return Err(ProgramError::MissingRequiredSignature);
    }

    // VULNERABILITY: authority is used for authorization but not checked as signer!
    // Attacker can pass their account as 'user' (signer) and victim's account as 'authority'

    // Verify authority owns the 'from' account
    if from.owner != authority.key {
        msg!("Authority doesn't own from account");
        return Err(ProgramError::IllegalOwner);
    }

    // Parse amount
    let amount = u64::from_le_bytes(
        instruction_data[1..9]
            .try_into()
            .map_err(|_| ProgramError::InvalidInstructionData)?
    );

    // Transfer (authority not validated as signer!)
    **from.try_borrow_mut_lamports()? -= amount;
    **to.try_borrow_mut_lamports()? += amount;

    msg!("Transfer successful");
    Ok(())
}

/**
 * Example Attack 1: Direct theft via process_withdraw
 *
 * Transaction:
 * {
 *   accounts: [
 *     { pubkey: attacker.publicKey, isSigner: false },  // ← Not signer!
 *     { pubkey: vault.publicKey, isSigner: false, isWritable: true }
 *   ],
 *   data: [0, ...amount_bytes]  // Instruction 0 = withdraw
 * }
 *
 * Result: Attacker receives all vault funds without being signer!
 *
 * Example Attack 2: Bypass via process_transfer
 *
 * Transaction:
 * {
 *   accounts: [
 *     { pubkey: attacker.publicKey, isSigner: true },      // Attacker is signer
 *     { pubkey: victim.publicKey, isSigner: false },       // Victim's authority (not signer!)
 *     { pubkey: victimVault.publicKey, isWritable: true }, // Victim's vault
 *     { pubkey: attacker.publicKey, isWritable: true }     // Attacker receives
 *   ],
 *   data: [1, ...amount_bytes]  // Instruction 1 = transfer
 * }
 *
 * Result: Attacker passes signer check (user), but victim's authority is used
 *         without signature validation. Funds stolen!
 *
 * FIX 1: Add signer check immediately after obtaining authority account
 *
 * fn process_withdraw(accounts_iter: &mut ...) -> ProgramResult {
 *     let authority = next_account_info(accounts_iter)?;
 *     let vault = next_account_info(accounts_iter)?;
 *
 *     // ✅ CRITICAL: Validate authority is signer!
 *     if !authority.is_signer {
 *         msg!("Authority must be a signer");
 *         return Err(ProgramError::MissingRequiredSignature);
 *     }
 *
 *     // Now safe to proceed...
 * }
 *
 * FIX 2: Use Anchor framework (automatically enforces signer checks)
 *
 * #[derive(Accounts)]
 * pub struct Withdraw<'info> {
 *     #[account(signer)]  // ← Anchor enforces this!
 *     pub authority: Signer<'info>,
 *     #[account(mut)]
 *     pub vault: Account<'info, Vault>,
 * }
 *
 * Or even better, use Signer type:
 * pub authority: Signer<'info>,  // Can only be signer!
 *
 * FIX 3: Validate signature at program entry point
 *
 * Always validate critical accounts are signers BEFORE any logic:
 *
 * pub fn process_instruction(...) -> ProgramResult {
 *     // Validate all required signers upfront
 *     validate_signers(accounts)?;
 *
 *     // Then process instruction
 *     match instruction {
 *         ...
 *     }
 * }
 *
 * BEST PRACTICES:
 *
 * 1. ALWAYS check is_signer for accounts used in authorization
 * 2. Check signer BEFORE any state changes or fund transfers
 * 3. Use descriptive error messages: "Authority must be signer"
 * 4. Consider using Anchor framework for automatic validation
 * 5. In native programs, add explicit signer checks at function start
 * 6. Never trust account metadata - always validate!
 *
 * TESTING:
 *
 * Test your program with transactions where required signers are NOT signers!
 * If it doesn't fail, you have a vulnerability.
 *
 * #[test]
 * fn test_missing_signer_fails() {
 *     let authority_not_signer = /* account without signature */;
 *     let result = withdraw(&[authority_not_signer, vault]);
 *     assert!(result.is_err());  // Should fail!
 * }
 */
