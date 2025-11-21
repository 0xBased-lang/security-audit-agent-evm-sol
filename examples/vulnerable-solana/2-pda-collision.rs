/**
 * VULNERABLE SOLANA PROGRAM: PDA Seed Collision
 *
 * INTENTIONALLY VULNERABLE - FOR TESTING ONLY
 *
 * Vulnerability: PDA uses only static seeds without user-specific identifier
 * Expected Detection: pda-collision-detector, anchor-agent
 * Severity: CRITICAL
 *
 * Attack Scenario:
 * 1. User A initializes vault → PDA derived from ["vault"]
 * 2. User B initializes vault → SAME PDA! (collision)
 * 3. Both users deposit to same vault address
 * 4. User A withdraws all funds (including User B's deposit)
 *
 * Real-world: Cashio ($52M) - PDA collision allowed minting arbitrary tokens
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
pub struct Vault {
    pub owner: Pubkey,
    pub balance: u64,
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
        0 => process_initialize(program_id, accounts),
        1 => process_deposit(program_id, accounts, instruction_data),
        2 => process_withdraw(program_id, accounts, instruction_data),
        _ => Err(ProgramError::InvalidInstructionData),
    }
}

/// VULNERABLE: Creates PDA with only static seed!
fn process_initialize(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let user = next_account_info(accounts_iter)?;
    let vault_account = next_account_info(accounts_iter)?;

    // CRITICAL VULNERABILITY: PDA uses only static seed!
    // All users will get the SAME vault PDA!
    let (vault_pda, bump) = Pubkey::find_program_address(
        &[b"vault"],  // ← Missing user identifier!
        program_id
    );

    // Verify the provided account matches PDA
    if vault_account.key != &vault_pda {
        msg!("Invalid vault account");
        return Err(ProgramError::InvalidAccountData);
    }

    msg!("Vault PDA: {}", vault_pda);
    msg!("Bump: {}", bump);
    msg!("WARNING: All users share this same PDA!");

    // Initialize vault data
    let vault = Vault {
        owner: *user.key,  // ← Different owners, same PDA!
        balance: 0,
    };

    // Serialize (simplified - in real code, use proper account initialization)
    let mut data = vault_account.try_borrow_mut_data()?;
    vault.serialize(&mut &mut data[..])?;

    msg!("Vault initialized for {}", user.key);
    Ok(())
}

/// Deposit funds to vault
fn process_deposit(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let user = next_account_info(accounts_iter)?;
    let vault_account = next_account_info(accounts_iter)?;

    // Derive PDA (same vulnerable derivation)
    let (vault_pda, _bump) = Pubkey::find_program_address(
        &[b"vault"],
        program_id
    );

    if vault_account.key != &vault_pda {
        return Err(ProgramError::InvalidAccountData);
    }

    let amount = u64::from_le_bytes(
        instruction_data[1..9]
            .try_into()
            .map_err(|_| ProgramError::InvalidInstructionData)?
    );

    // Transfer funds
    **user.try_borrow_mut_lamports()? -= amount;
    **vault_account.try_borrow_mut_lamports()? += amount;

    // Update vault data
    let mut data = vault_account.try_borrow_mut_data()?;
    let mut vault = Vault::try_from_slice(&data)?;
    vault.balance += amount;
    vault.serialize(&mut &mut data[..])?;

    msg!("{} deposited {} to shared vault", user.key, amount);
    Ok(())
}

/// VULNERABLE: Can withdraw from shared vault!
fn process_withdraw(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let user = next_account_info(accounts_iter)?;
    let vault_account = next_account_info(accounts_iter)?;

    // Derive PDA
    let (vault_pda, _bump) = Pubkey::find_program_address(
        &[b"vault"],
        program_id
    );

    if vault_account.key != &vault_pda {
        return Err(ProgramError::InvalidAccountData);
    }

    // Parse vault data
    let data = vault_account.try_borrow_data()?;
    let vault = Vault::try_from_slice(&data)?;

    // VULNERABILITY: Only checks if user was ORIGINAL owner
    // But since all users share same PDA, first user can withdraw everyone's funds!
    if vault.owner != *user.key {
        msg!("Not vault owner");
        return Err(ProgramError::IllegalOwner);
    }

    let amount = u64::from_le_bytes(
        instruction_data[1..9]
            .try_into()
            .map_err(|_| ProgramError::InvalidInstructionData)?
    );

    // Transfer all vault funds (including other users' deposits!)
    **vault_account.try_borrow_mut_lamports()? -= amount;
    **user.try_borrow_mut_lamports()? += amount;

    msg!("{} withdrew {} (may include other users' funds!)", user.key, amount);
    Ok(())
}

/**
 * Example Attack:
 *
 * Scenario:
 * 1. Alice calls initialize()
 *    - PDA derived: find_program_address(&[b"vault"], program_id)
 *    - vault_pda = "ABC123..." (example)
 *    - Vault { owner: Alice, balance: 0 }
 *
 * 2. Alice deposits 100 SOL
 *    - Same PDA: "ABC123..."
 *    - Vault balance: 100 SOL
 *
 * 3. Bob calls initialize()
 *    - PDA derived: find_program_address(&[b"vault"], program_id)
 *    - vault_pda = "ABC123..." (SAME!)
 *    - Vault { owner: Bob, balance: 100 } ← Overwrites Alice's owner!
 *
 * 4. Bob deposits 50 SOL
 *    - Same PDA: "ABC123..."
 *    - Vault balance: 150 SOL (Alice's 100 + Bob's 50)
 *
 * 5. Bob withdraws 150 SOL
 *    - Checks: vault.owner == Bob ✓
 *    - Withdraws entire balance: 150 SOL
 *    - Bob stole Alice's 100 SOL!
 *
 * OR:
 *
 * 1. Alice initializes and deposits 100 SOL (owner: Alice)
 * 2. Alice withdraws: vault.owner == Alice ✓ → Withdraws 100 SOL
 * 3. Bob deposits 50 SOL to same PDA
 * 4. Alice withdraws 50 SOL: vault.owner == Alice ✓ → Steals Bob's deposit!
 *
 * FIX 1: Include user key in PDA seeds
 *
 * let (vault_pda, bump) = Pubkey::find_program_address(
 *     &[
 *         b"vault",
 *         user.key.as_ref(),  // ← User-specific seed!
 *     ],
 *     program_id
 * );
 *
 * Now each user gets unique PDA:
 * - Alice's vault: PDA from ["vault", alice_pubkey]
 * - Bob's vault: PDA from ["vault", bob_pubkey]
 * - No collision possible!
 *
 * FIX 2: Use Anchor with proper seeds
 *
 * #[derive(Accounts)]
 * pub struct Initialize<'info> {
 *     #[account(
 *         init,
 *         payer = user,
 *         space = 8 + 32 + 8,
 *         seeds = [b"vault", user.key().as_ref()],  // ← Unique per user
 *         bump
 *     )]
 *     pub vault: Account<'info, Vault>,
 *     #[account(mut)]
 *     pub user: Signer<'info>,
 *     pub system_program: Program<'info, System>,
 * }
 *
 * FIX 3: Add nonce/counter for multiple vaults per user
 *
 * let (vault_pda, bump) = Pubkey::find_program_address(
 *     &[
 *         b"vault",
 *         user.key.as_ref(),
 *         &vault_number.to_le_bytes(),  // ← Support multiple vaults
 *     ],
 *     program_id
 * );
 *
 * BEST PRACTICES:
 *
 * 1. Always include user-specific identifier in PDA seeds
 * 2. For token accounts: include mint address AND user address
 * 3. For pools: include both token mint addresses
 * 4. For NFTs: include mint address
 * 5. Test with multiple users to ensure unique PDAs
 * 6. Document PDA derivation clearly in code
 *
 * TESTING:
 *
 * #[test]
 * fn test_unique_pdas_per_user() {
 *     let alice_pda = derive_vault_pda(&alice.pubkey());
 *     let bob_pda = derive_vault_pda(&bob.pubkey());
 *     assert_ne!(alice_pda, bob_pda);  // Must be different!
 * }
 *
 * Common PDA patterns:
 * - User vault: ["vault", user_pubkey]
 * - Token account: ["token", mint, user_pubkey]
 * - Pool: ["pool", mint_a, mint_b]
 * - Metadata: ["metadata", mint]
 * - Escrow: ["escrow", seed, user_pubkey]
 */
