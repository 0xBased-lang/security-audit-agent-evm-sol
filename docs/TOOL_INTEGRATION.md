# Security Tool Integration Guide

> **Complete setup and integration documentation for all security auditing tools**

---

## Table of Contents

### EVM Tools
1. [Slither - Static Analysis](#slither)
2. [Mythril - Symbolic Execution](#mythril)
3. [Echidna - Property-Based Fuzzing](#echidna)
4. [Foundry - Fast Fuzzing](#foundry)
5. [Certora Prover - Formal Verification](#certora)
6. [Securify2 - Semantic Analysis](#securify2)
7. [Tenderly - Runtime Simulation](#tenderly)
8. [Hardhat + Plugins](#hardhat)

### Solana Tools
9. [Cargo Audit - Dependency Scanner](#cargo-audit)
10. [Clippy - Rust Linter](#clippy)
11. [Anchor - Framework Lints](#anchor)
12. [Solana Program Test](#solana-program-test)
13. [Kangaroo - Fuzzer](#kangaroo)

---

# EVM Tools

## Slither

### Installation

```bash
# Python 3.8+ required
pip3 install slither-analyzer

# Verify installation
slither --version
```

### Basic Usage

```bash
# Analyze a single contract
slither contract.sol

# Analyze with specific compiler version
slither contract.sol --solc-version 0.8.19

# Output to JSON
slither contract.sol --json output.json

# Filter by severity
slither contract.sol --severity high,critical

# Exclude specific detectors
slither contract.sol --exclude reentrancy-benign,timestamp
```

### Programmatic Integration (Python)

```python
from slither import Slither
from slither.detectors.abstract_detector import AbstractDetector

# Initialize Slither
slither = Slither('contract.sol')

# Get all contracts
for contract in slither.contracts:
    print(f"Contract: {contract.name}")

    # Check functions
    for function in contract.functions:
        print(f"  Function: {function.name}")

        # Check for vulnerabilities
        if function.can_reenter():
            print(f"    VULNERABLE TO REENTRANCY")

# Run specific detectors
from slither.detectors.reentrancy.reentrancy_eth import ReentrancyEth

detector = ReentrancyEth(slither)
results = detector.detect()

for result in results:
    print(f"Finding: {result['description']}")
    print(f"Severity: {result['severity']}")
```

### CI/CD Integration

**GitHub Actions:**
```yaml
name: Slither Analysis

on: [push, pull_request]

jobs:
  slither:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Slither
        uses: crytic/slither-action@v0.3.0
        with:
          target: 'contracts/'
          slither-args: '--filter-paths "node_modules"'
          fail-on: medium
```

### Output Formats

- **JSON**: Machine-readable, best for tooling
- **Markdown**: Human-readable reports
- **Sarif**: For GitHub code scanning
- **Text**: Terminal output

### Custom Detector Example

```python
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

class CustomDetector(AbstractDetector):
    ARGUMENT = 'custom-detector'
    HELP = 'Detects custom vulnerability pattern'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    def _detect(self):
        results = []

        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions:
                # Custom detection logic
                if self.is_vulnerable(function):
                    info = f"{function.name} is vulnerable"
                    results.append(self.generate_result(info))

        return results
```

### Key Detectors

| Detector | Impact | Description |
|----------|--------|-------------|
| `reentrancy-eth` | High | Reentrancy vulnerabilities |
| `suicidal` | High | Unprotected selfdestruct |
| `unprotected-upgrade` | High | Unprotected upgradeable contracts |
| `arbitrary-send-eth` | High | Arbitrary send to any address |
| `controlled-delegatecall` | High | Delegatecall to user-supplied address |
| `tx-origin` | Medium | Dangerous tx.origin usage |
| `unchecked-transfer` | High | Unchecked ERC20 transfer |

---

## Mythril

### Installation

```bash
# Via pip
pip3 install mythril

# Via Docker
docker pull mythril/myth

# Verify
myth version
```

### Basic Usage

```bash
# Analyze contract
myth analyze contract.sol

# With specific contract
myth analyze contract.sol:ContractName

# Set analysis depth (higher = slower but deeper)
myth analyze contract.sol --max-depth 50

# Output to JSON
myth analyze contract.sol -o json > output.json

# Quick scan (faster, less thorough)
myth analyze contract.sol --quick
```

### Programmatic Integration (Python)

```python
from mythril.mythril import MythrilDisassembler, MythrilAnalyzer
from mythril.ethereum import util

# Initialize
disassembler = MythrilDisassembler()

# Analyze from source
disassembler.load_from_solidity(['contract.sol'])

analyzer = MythrilAnalyzer(
    disassembler=disassembler,
    strategy="dfs",
    execution_timeout=300,
    max_depth=50
)

# Run analysis
issues = analyzer.fire_lasers()

# Process results
for issue in issues:
    print(f"Type: {issue.type}")
    print(f"Title: {issue.title}")
    print(f"Description: {issue.description}")
    print(f"Severity: {issue.severity}")
```

### Configuration

**mythril.yaml:**
```yaml
analysis:
  max_depth: 100
  solver_timeout: 10000
  strategy: "bfs"  # or "dfs"

output:
  format: "json"
  verbose: true

detectors:
  enabled:
    - reentrancy
    - integer_overflow
    - assertion_failure
```

---

## Echidna

### Installation

```bash
# macOS
brew install echidna

# Linux - Download binary
wget https://github.com/crytic/echidna/releases/latest/download/echidna-x86_64-linux
chmod +x echidna-x86_64-linux
sudo mv echidna-x86_64-linux /usr/local/bin/echidna
```

### Basic Usage

**Test Contract:**
```solidity
contract TestContract {
    uint256 public balance;

    // Echidna will try to break this invariant
    function echidna_balance_under_1000() public view returns (bool) {
        return balance < 1000;
    }

    function deposit(uint256 amount) public {
        balance += amount;
    }
}
```

**Run Echidna:**
```bash
echidna contract.sol --contract TestContract

# With config file
echidna contract.sol --config echidna.yaml

# Continuous fuzzing
echidna contract.sol --test-limit 100000
```

### Configuration

**echidna.yaml:**
```yaml
testMode: assertion
testLimit: 50000
shrinkLimit: 5000
seqLen: 100
contractAddr: "0x1234567890123456789012345678901234567890"
deployer: "0x0000000000000000000000000000000000030000"
sender: ["0x0000000000000000000000000000000000010000"]
coverage: true
corpusDir: "corpus"

# Solc configuration
solcArgs: "--optimize"
solcVersion: "0.8.19"

# Optimization
workers: 4
```

### Property Types

**1. Boolean Properties:**
```solidity
function echidna_test_property() public view returns (bool) {
    return invariant_holds();
}
```

**2. Assertion Mode:**
```solidity
function test_function() public {
    // ...
    assert(some_condition); // Echidna will try to break this
}
```

**3. dapptest Mode:**
```solidity
function test_invariant() public {
    // setUp() called before each test
}
```

---

## Foundry

### Installation

```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Fuzzing Setup

**foundry.toml:**
```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
solc_version = "0.8.19"

[fuzz]
runs = 10000
max_test_rejects = 100000
seed = '0x1'
dictionary_weight = 40
include_storage = true
include_push_bytes = true
```

### Fuzz Testing

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";

contract FuzzTest is Test {
    MyContract target;

    function setUp() public {
        target = new MyContract();
    }

    // Foundry automatically fuzzes inputs
    function testFuzz_Deposit(uint256 amount) public {
        vm.assume(amount > 0 && amount < type(uint96).max);

        target.deposit(amount);
        assertEq(target.balanceOf(address(this)), amount);
    }

    // Bound fuzzing inputs
    function testFuzz_Transfer(
        address to,
        uint256 amount
    ) public {
        vm.assume(to != address(0));
        amount = bound(amount, 1, 1000 ether);

        // Test logic
    }
}
```

### Invariant Testing

```solidity
contract InvariantTest is Test {
    MyContract target;
    Handler handler;

    function setUp() public {
        target = new MyContract();
        handler = new Handler(target);

        // Focus fuzzing on handler
        targetContract(address(handler));
    }

    // Invariant: total supply equals sum of balances
    function invariant_TotalSupply() public {
        uint256 sumBalances = handler.ghost_sumBalances();
        assertEq(target.totalSupply(), sumBalances);
    }

    // Invariant: balance never exceeds total supply
    function invariant_UserBalanceLteTotalSupply() public {
        uint256 totalSupply = target.totalSupply();
        for (uint i = 0; i < handler.actors.length; i++) {
            address actor = handler.actors[i];
            assertLe(target.balanceOf(actor), totalSupply);
        }
    }
}
```

### Handler Pattern

```solidity
contract Handler is Test {
    MyContract target;
    uint256 public ghost_sumBalances;
    address[] public actors;

    constructor(MyContract _target) {
        target = _target;
    }

    function deposit(uint256 actorSeed, uint256 amount) public {
        // Get or create actor
        address actor = actors[actorSeed % actors.length];
        if (actors.length == 0) {
            actor = address(uint160(actorSeed));
            actors.push(actor);
        }

        // Bound amount
        amount = bound(amount, 0, 1000 ether);

        // Execute action
        vm.prank(actor);
        target.deposit{value: amount}();

        // Update ghost variable
        ghost_sumBalances += amount;
    }
}
```

### Run Tests

```bash
# Basic tests
forge test

# With verbosity
forge test -vvvv

# Specific test
forge test --match-test testFuzz_Deposit

# Invariant tests
forge test --match-contract InvariantTest

# Gas report
forge test --gas-report

# Coverage
forge coverage
```

---

## Certora

### Installation

```bash
# Install Java 11+
sudo apt install openjdk-11-jdk

# Install Certora Prover
pip3 install certora-cli

# Verify
certoraRun --version
```

### CVL Specification Example

**spec.spec:**
```
methods {
    function balanceOf(address) external returns (uint256) envfree;
    function totalSupply() external returns (uint256) envfree;
    function transfer(address, uint256) external returns (bool);
}

// Invariant: total supply = sum of balances
invariant totalSupplyIsSumOfBalances()
    totalSupply() == ghost_sumBalances;

// Rule: transfer preserves total supply
rule transferPreservesTotalSupply(address to, uint256 amount) {
    env e;
    uint256 totalBefore = totalSupply();

    transfer(e, to, amount);

    uint256 totalAfter = totalSupply();
    assert totalBefore == totalAfter;
}

// Rule: transfer can't increase recipient balance by more than amount
rule transferIncreasesRecipientBalance(address to, uint256 amount) {
    env e;
    uint256 recipientBefore = balanceOf(to);

    transfer(e, to, amount);

    uint256 recipientAfter = balanceOf(to);
    assert recipientAfter <= recipientBefore + amount;
}
```

### Running Certora

```bash
certoraRun MyContract.sol \
    --verify MyContract:spec.spec \
    --solc solc8.19 \
    --msg "Verifying transfer function"
```

**With configuration file (certora.conf):**
```json
{
    "files": ["MyContract.sol"],
    "verify": "MyContract:spec.spec",
    "solc": "solc8.19",
    "optimistic_loop": true,
    "loop_iter": 3,
    "msg": "Full verification"
}
```

```bash
certoraRun certora.conf
```

---

## Securify2

### Installation

```bash
# Clone repository
git clone https://github.com/eth-sri/securify2.git
cd securify2

# Install dependencies
pip3 install -r requirements.txt

# Build
python3 setup.py install
```

### Basic Usage

```bash
# Analyze contract
securify2 contract.sol

# Output to JSON
securify2 contract.sol --json output.json
```

**Note**: Securify2 is deprecated but still useful for complementary analysis.

---

## Tenderly

### Setup

```bash
# Install CLI
npm install -g @tenderly/cli

# Login
tenderly login

# Initialize project
tenderly init
```

### Transaction Simulation

```bash
# Simulate transaction
tenderly simulate \
    --from 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb \
    --to 0xContractAddress \
    --data 0x... \
    --value 1000000000000000000

# Fork mainnet
tenderly fork create mainnet
```

### Programmatic Simulation (JavaScript)

```javascript
const axios = require('axios');

async function simulateTransaction() {
    const response = await axios.post(
        'https://api.tenderly.co/api/v1/account/PROJECT/simulate',
        {
            from: '0x...',
            to: '0x...',
            data: '0x...',
            gas: 8000000,
            gasPrice: '0',
            value: '0',
            save: true,
            save_if_fails: true,
        },
        {
            headers: {
                'X-Access-Key': 'YOUR_API_KEY',
                'Content-Type': 'application/json',
            },
        }
    );

    return response.data;
}
```

---

## Hardhat

### Installation

```bash
npm install --save-dev hardhat
npm install --save-dev @nomicfoundation/hardhat-toolbox
npm install --save-dev @openzeppelin/hardhat-upgrades
```

### Configuration

**hardhat.config.js:**
```javascript
require("@nomicfoundation/hardhat-toolbox");
require("@openzeppelin/hardhat-upgrades");

module.exports = {
    solidity: {
        version: "0.8.19",
        settings: {
            optimizer: {
                enabled: true,
                runs: 200,
            },
        },
    },
    networks: {
        hardhat: {
            forking: {
                url: "https://eth-mainnet.alchemyapi.io/v2/YOUR_KEY",
            },
        },
    },
};
```

### Security Testing

```javascript
const { expect } = require("chai");
const { ethers, upgrades } = require("hardhat");

describe("Security Tests", function () {
    let contract;
    let owner, attacker;

    beforeEach(async function () {
        [owner, attacker] = await ethers.getSigners();

        const Contract = await ethers.getContractFactory("MyContract");
        contract = await Contract.deploy();
    });

    it("Should prevent reentrancy", async function () {
        const Attacker = await ethers.getContractFactory("ReentrancyAttacker");
        const attackerContract = await Attacker.deploy(contract.address);

        await expect(
            attackerContract.attack({ value: ethers.utils.parseEther("1") })
        ).to.be.revertedWith("ReentrancyGuard: reentrant call");
    });

    it("Should enforce access control", async function () {
        await expect(
            contract.connect(attacker).adminFunction()
        ).to.be.revertedWith("Not authorized");
    });
});
```

---

# Solana Tools

## Cargo Audit

### Installation

```bash
cargo install cargo-audit
```

### Basic Usage

```bash
# Audit dependencies
cargo audit

# Output to JSON
cargo audit --json > audit.json

# Ignore specific advisories
cargo audit --ignore RUSTSEC-2020-0071

# Database update
cargo audit --update
```

### Configuration

**.cargo/audit.toml:**
```toml
[advisories]
ignore = [
    "RUSTSEC-2020-0071",
]

[database]
path = "~/.cargo/advisory-db"
url = "https://github.com/RustSec/advisory-db.git"
```

### CI/CD Integration

**GitHub Actions:**
```yaml
name: Security Audit

on: [push, pull_request]

jobs:
  security_audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/audit-check@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```

---

## Clippy

### Installation

```bash
rustup component add clippy
```

### Basic Usage

```bash
# Run clippy
cargo clippy

# With warnings as errors
cargo clippy -- -D warnings

# All targets
cargo clippy --all-targets

# Fix automatically
cargo clippy --fix
```

### Configuration

**clippy.toml:**
```toml
# Deny specific lints
lint-level = "deny"

# Allow specific lints
allowed-lints = [
    "clippy::too_many_arguments",
]
```

### Specific to Solana

```bash
# With Solana-specific checks
cargo clippy -- \
    -D clippy::integer_arithmetic \
    -D clippy::checked_conversions \
    -W clippy::unwrap_used
```

---

## Anchor

### Installation

```bash
cargo install --git https://github.com/coral-xyz/anchor --tag v0.29.0 anchor-cli --locked
```

### Security Lints

Anchor provides built-in security checks:

```rust
use anchor_lang::prelude::*;

#[derive(Accounts)]
pub struct SecureAccounts<'info> {
    // Automatic signer check
    #[account(mut)]
    pub user: Signer<'info>,

    // PDA validation
    #[account(
        mut,
        seeds = [b"user_account", user.key().as_ref()],
        bump,
    )]
    pub user_account: Account<'info, UserAccount>,

    // Owner validation
    #[account(
        mut,
        has_one = user,
    )]
    pub user_data: Account<'info, UserData>,

    // Constraints
    #[account(
        mut,
        constraint = user_account.balance >= amount @ ErrorCode::InsufficientFunds,
    )]
    pub source: Account<'info, TokenAccount>,
}
```

### Testing

```bash
# Run tests
anchor test

# With local validator
anchor test --skip-local-validator

# Specific test
anchor test -- --nocapture test_name
```

---

## Solana Program Test

### Setup

**Cargo.toml:**
```toml
[dev-dependencies]
solana-program-test = "1.16"
solana-sdk = "1.16"
```

### Test Example

```rust
use solana_program_test::*;
use solana_sdk::{
    signature::Signer,
    transaction::Transaction,
};

#[tokio::test]
async fn test_program() {
    let program_id = Pubkey::new_unique();
    let mut program_test = ProgramTest::new(
        "my_program",
        program_id,
        processor!(process_instruction),
    );

    // Add accounts
    program_test.add_account(
        user_pubkey,
        Account {
            lamports: 1_000_000,
            data: vec![],
            owner: program_id,
            executable: false,
            rent_epoch: 0,
        },
    );

    // Start test
    let (mut banks_client, payer, recent_blockhash) = program_test.start().await;

    // Create transaction
    let mut transaction = Transaction::new_with_payer(
        &[instruction],
        Some(&payer.pubkey()),
    );
    transaction.sign(&[&payer], recent_blockhash);

    // Execute
    banks_client.process_transaction(transaction).await.unwrap();

    // Verify
    let account = banks_client
        .get_account(user_pubkey)
        .await
        .unwrap()
        .unwrap();

    assert_eq!(account.lamports, expected_balance);
}
```

---

## Kangaroo

### Installation

```bash
# Still in early stages - check latest releases
cargo install kangaroo-fuzzer
```

### Basic Usage

```rust
// Annotate fuzz targets
#[kangaroo::fuzz_target]
fn fuzz_instruction(data: &[u8]) {
    let instruction = match deserialize(data) {
        Ok(ix) => ix,
        Err(_) => return,
    };

    // Process instruction
    process_instruction(&program_id, &accounts, &instruction).ok();
}
```

---

# Integration Scripts

## Complete EVM Audit Script

**scripts/audit-evm.sh:**
```bash
#!/bin/bash

set -e

CONTRACT=$1
OUTPUT_DIR="audit-results"

mkdir -p $OUTPUT_DIR

echo "Running Slither..."
slither $CONTRACT --json $OUTPUT_DIR/slither.json

echo "Running Mythril..."
myth analyze $CONTRACT -o json > $OUTPUT_DIR/mythril.json

echo "Running Foundry tests..."
forge test --json > $OUTPUT_DIR/foundry.json

echo "Audit complete. Results in $OUTPUT_DIR/"
```

## Complete Solana Audit Script

**scripts/audit-solana.sh:**
```bash
#!/bin/bash

set -e

PROGRAM_DIR=$1
OUTPUT_DIR="audit-results"

mkdir -p $OUTPUT_DIR

echo "Running cargo audit..."
cd $PROGRAM_DIR
cargo audit --json > ../$OUTPUT_DIR/cargo-audit.json

echo "Running clippy..."
cargo clippy --message-format=json > ../$OUTPUT_DIR/clippy.json

echo "Running tests..."
cargo test-bpf -- --nocapture > ../$OUTPUT_DIR/tests.log

echo "Audit complete. Results in $OUTPUT_DIR/"
```

---

# Next Steps

1. See [AI_PATTERNS.md](./AI_PATTERNS.md) for AI orchestration workflows
2. Check [BEST_PRACTICES.md](./BEST_PRACTICES.md) for secure coding guidelines
3. Explore [examples/](../examples/) for complete audit examples

---

**Always combine multiple tools for comprehensive coverage!**
