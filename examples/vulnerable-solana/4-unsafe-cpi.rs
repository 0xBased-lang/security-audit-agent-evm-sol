/**
 * VULNERABLE SOLANA PROGRAM: Unsafe Cross-Program Invocation (CPI)
 *
 * INTENTIONALLY VULNERABLE - FOR TESTING ONLY
 *
 * Vulnerability: Arbitrary CPI and unsafe invoke_signed usage
 * Expected Detection: cpi-exploit-detector
 * Severity: CRITICAL
 *
 * Attack Scenario:
 * 1. Attacker passes malicious program ID
 * 2. Program makes CPI without validating program ID
 * 3. Attacker's program executes with vault's authority (PDA signer)
 * 4. Attacker can steal funds, manipulate state, etc.
 *
 * Real-world impact: Privilege escalation via CPI
 */

use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    instruction::{AccountMeta, Instruction},
    msg,
    program::invoke_signed,
    program_error::ProgramError,
    pubkey::Pubkey,
};

entrypoint!(process_instruction);

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let instruction = instruction_data
        .get(0)
        .ok_or(ProgramError::InvalidInstructionData)?;

    match instruction {
        0 => process_arbitrary_cpi(program_id, accounts, instruction_data),
        1 => process_unsafe_invoke_signed(program_id, accounts, instruction_data),
        _ => Err(ProgramError::InvalidInstructionData),
    }
}

/// VULNERABLE: Allows calling ANY program!
fn process_arbitrary_cpi(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let authority = next_account_info(accounts_iter)?;
    let target_program = next_account_info(accounts_iter)?;  // ← Attacker controlled!

    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // CRITICAL VULNERABILITY: No validation of target program ID!
    // Should verify: target_program.key == &spl_token::ID (or other expected program)

    // Parse CPI instruction data from our instruction data
    let cpi_data = &instruction_data[1..];

    // Build instruction to call target program
    let cpi_instruction = Instruction {
        program_id: *target_program.key,  // ← Attacker controlled!
        accounts: vec![
            AccountMeta::new(*authority.key, false),
        ],
        data: cpi_data.to_vec(),
    };

    msg!("Calling arbitrary program: {}", target_program.key);
    msg!("WARNING: Program ID not validated!");

    // DANGER: Calling unknown program!
    invoke_signed(
        &cpi_instruction,
        &[authority.clone(), target_program.clone()],
        &[],
    )?;

    Ok(())
}

/// VULNERABLE: Uses invoke_signed with user-controlled instruction!
fn process_unsafe_invoke_signed(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let vault_pda = next_account_info(accounts_iter)?;
    let target_program = next_account_info(accounts_iter)?;
    let target_account = next_account_info(accounts_iter)?;

    // Derive PDA
    let vault_seed = b"vault";
    let (expected_pda, bump) = Pubkey::find_program_address(
        &[vault_seed],
        program_id
    );

    if vault_pda.key != &expected_pda {
        return Err(ProgramError::InvalidSeeds);
    }

    // CRITICAL VULNERABILITY: Program ID not validated!
    // Attacker can make vault PDA sign arbitrary instructions!

    // Parse instruction data (attacker controlled!)
    let cpi_data = &instruction_data[1..];

    // Build instruction
    let cpi_instruction = Instruction {
        program_id: *target_program.key,  // ← Not validated!
        accounts: vec![
            AccountMeta::new(*vault_pda.key, true),  // ← PDA is signer!
            AccountMeta::new(*target_account.key, false),
        ],
        data: cpi_data.to_vec(),  // ← Attacker controlled!
    };

    msg!("Vault PDA signing arbitrary CPI!");
    msg!("Target program: {}", target_program.key);

    // DANGER: PDA signs attacker's instruction!
    invoke_signed(
        &cpi_instruction,
        &[vault_pda.clone(), target_account.clone(), target_program.clone()],
        &[&[vault_seed, &[bump]]],  // ← PDA signer seeds
    )?;

    msg!("Arbitrary CPI executed with PDA authority!");
    Ok(())
}

/**
 * Attack Scenario 1: Arbitrary CPI to Malicious Program
 *
 * Attacker creates malicious program:
 *
 * // Malicious program
 * pub fn steal_funds(accounts: &[AccountInfo]) -> ProgramResult {
 *     let victim = &accounts[0];
 *     let attacker = &accounts[1];
 *
 *     // Transfer all lamports
 *     **victim.lamports.borrow_mut() = 0;
 *     **attacker.lamports.borrow_mut() += victim_balance;
 *     Ok(())
 * }
 *
 * Attacker calls vulnerable program:
 * process_arbitrary_cpi(
 *     accounts: [
 *         authority (attacker's account, signer),
 *         malicious_program,  // ← Attacker's program!
 *     ],
 *     data: [0, /* malicious instruction data */]
 * )
 *
 * Result: Vulnerable program makes CPI to malicious program!
 *
 * Attack Scenario 2: PDA Signing Arbitrary Instruction
 *
 * Vault PDA holds funds. Attacker wants to steal them.
 *
 * Attacker calls process_unsafe_invoke_signed:
 * accounts: [
 *     vault_pda,
 *     system_program,  // ← OR malicious program
 *     attacker_account
 * ]
 * data: [1, /* transfer instruction data */]
 *
 * Vulnerable program does:
 * invoke_signed(
 *     Instruction {
 *         program_id: system_program,
 *         accounts: [vault_pda (signer!), attacker_account],
 *         data: transfer_all_funds
 *     },
 *     &[&[b"vault", &[bump]]]  // ← PDA signs!
 * )
 *
 * Result: Vault PDA transfers all its funds to attacker!
 *
 * FIX 1: Validate program ID before CPI
 *
 * fn process_cpi(...) -> ProgramResult {
 *     ...
 *     let target_program = next_account_info(accounts_iter)?;
 *
 *     // ✅ CRITICAL: Validate program ID!
 *     if target_program.key != &spl_token::ID {
 *         msg!("Invalid program ID");
 *         return Err(ProgramError::IncorrectProgramId);
 *     }
 *
 *     // Now safe to make CPI
 *     invoke(...)
 * }
 *
 * FIX 2: Use specific CPI functions instead of arbitrary invoke
 *
 * // Instead of arbitrary invoke, use SPL Token's CPI helpers:
 * use spl_token::instruction::transfer;
 *
 * let transfer_ix = transfer(
 *     &spl_token::ID,  // ← Hardcoded program ID
 *     source,
 *     destination,
 *     authority,
 *     &[],
 *     amount
 * )?;
 *
 * invoke_signed(&transfer_ix, accounts, signer_seeds)?;
 *
 * FIX 3: Whitelist allowed programs
 *
 * const ALLOWED_PROGRAMS: &[Pubkey] = &[
 *     spl_token::ID,
 *     spl_associated_token_account::ID,
 * ];
 *
 * if !ALLOWED_PROGRAMS.contains(target_program.key) {
 *     return Err(ProgramError::IncorrectProgramId);
 * }
 *
 * FIX 4: Never use invoke_signed with user-controlled data
 *
 * // BAD: User controls instruction
 * invoke_signed(&user_instruction, accounts, signer_seeds)?;
 *
 * // GOOD: Program controls instruction completely
 * let transfer_ix = create_specific_instruction(...);
 * invoke_signed(&transfer_ix, accounts, signer_seeds)?;
 *
 * FIX 5: Use Anchor CPI module
 *
 * use anchor_spl::token::{self, Transfer};
 *
 * let cpi_ctx = CpiContext::new_with_signer(
 *     ctx.accounts.token_program.to_account_info(),
 *     Transfer {
 *         from: ctx.accounts.from.to_account_info(),
 *         to: ctx.accounts.to.to_account_info(),
 *         authority: ctx.accounts.vault_pda.to_account_info(),
 *     },
 *     signer_seeds
 * );
 *
 * token::transfer(cpi_ctx, amount)?;
 *
 * // Anchor ensures:
 * // - Program ID is spl_token::ID
 * // - Accounts match expected types
 * // - Instruction is valid
 *
 * BEST PRACTICES:
 *
 * 1. Always validate program ID before CPI:
 *    require_keys_eq!(program.key(), EXPECTED_PROGRAM_ID);
 *
 * 2. Never let users control:
 *    - Target program ID
 *    - Instruction data for invoke_signed
 *    - Accounts for privileged CPIs
 *
 * 3. Use specific CPI helpers instead of raw invoke:
 *    - spl_token::instruction::transfer
 *    - anchor_spl::token::transfer
 *    - etc.
 *
 * 4. Whitelist allowed programs if multiple programs supported
 *
 * 5. Document which programs your program can CPI to
 *
 * 6. Be extremely careful with invoke_signed:
 *    - Only use for specific, well-defined operations
 *    - Never with user-controlled instructions
 *    - Validate all parameters
 *
 * TESTING:
 *
 * #[test]
 * fn test_rejects_arbitrary_program() {
 *     let malicious_program = create_malicious_program();
 *     let result = process_cpi(&[authority, malicious_program]);
 *     assert_eq!(result.unwrap_err(), ProgramError::IncorrectProgramId);
 * }
 *
 * #[test]
 * fn test_only_allows_spl_token() {
 *     let random_program = Pubkey::new_unique();
 *     let result = process_cpi_to(random_program);
 *     assert!(result.is_err());
 *
 *     let result = process_cpi_to(spl_token::ID);
 *     assert!(result.is_ok());  // Only SPL Token allowed
 * }
 *
 * Real-world lessons:
 * - Solana documentation emphasizes CPI security
 * - Many protocols have been exploited via unsafe CPI
 * - invoke_signed is powerful but dangerous
 * - Always validate program IDs!
 */
