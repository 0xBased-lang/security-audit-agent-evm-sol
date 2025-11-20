#!/bin/bash

# Installation script for blockchain security tools
# Supports Linux, macOS, and WSL

set -e

echo "========================================="
echo "Blockchain Security Tools Installation"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "Detected OS: $MACHINE"
echo ""

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install EVM Tools
echo "========================================="
echo "Installing EVM Security Tools"
echo "========================================="
echo ""

# Python and pip
if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install Python 3.8+ first"
    exit 1
else
    echo -e "${GREEN}✓ Python 3 found${NC}"
fi

# Slither
echo "Installing Slither..."
if command_exists slither; then
    echo -e "${YELLOW}Slither already installed${NC}"
else
    pip3 install slither-analyzer
    echo -e "${GREEN}✓ Slither installed${NC}"
fi

# Mythril
echo "Installing Mythril..."
if command_exists myth; then
    echo -e "${YELLOW}Mythril already installed${NC}"
else
    pip3 install mythril
    echo -e "${GREEN}✓ Mythril installed${NC}"
fi

# Foundry
echo "Installing Foundry..."
if command_exists forge; then
    echo -e "${YELLOW}Foundry already installed${NC}"
else
    curl -L https://foundry.paradigm.xyz | bash
    echo "Run 'foundryup' after this script completes"
    echo -e "${GREEN}✓ Foundry installer downloaded${NC}"
fi

# Echidna
echo "Installing Echidna..."
if command_exists echidna; then
    echo -e "${YELLOW}Echidna already installed${NC}"
else
    if [ "$MACHINE" == "Mac" ]; then
        if command_exists brew; then
            brew install echidna
            echo -e "${GREEN}✓ Echidna installed${NC}"
        else
            echo -e "${RED}Homebrew not found. Install from: https://github.com/crytic/echidna/releases${NC}"
        fi
    else
        echo "Downloading Echidna for Linux..."
        ECHIDNA_VERSION="2.2.1"
        wget "https://github.com/crytic/echidna/releases/download/v${ECHIDNA_VERSION}/echidna-${ECHIDNA_VERSION}-x86_64-linux.tar.gz"
        tar -xzf "echidna-${ECHIDNA_VERSION}-x86_64-linux.tar.gz"
        sudo mv echidna /usr/local/bin/
        rm "echidna-${ECHIDNA_VERSION}-x86_64-linux.tar.gz"
        echo -e "${GREEN}✓ Echidna installed${NC}"
    fi
fi

echo ""
echo "========================================="
echo "Installing Solana Security Tools"
echo "========================================="
echo ""

# Rust and Cargo
if ! command_exists cargo; then
    echo "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
    echo -e "${GREEN}✓ Rust installed${NC}"
else
    echo -e "${GREEN}✓ Rust already installed${NC}"
fi

# Cargo audit
echo "Installing cargo-audit..."
if cargo audit --version >/dev/null 2>&1; then
    echo -e "${YELLOW}cargo-audit already installed${NC}"
else
    cargo install cargo-audit
    echo -e "${GREEN}✓ cargo-audit installed${NC}"
fi

# Clippy
echo "Installing clippy..."
if cargo clippy --version >/dev/null 2>&1; then
    echo -e "${YELLOW}clippy already installed${NC}"
else
    rustup component add clippy
    echo -e "${GREEN}✓ clippy installed${NC}"
fi

# Solana CLI
echo "Installing Solana CLI..."
if command_exists solana; then
    echo -e "${YELLOW}Solana CLI already installed${NC}"
else
    sh -c "$(curl -sSfL https://release.solana.com/stable/install)"
    echo -e "${GREEN}✓ Solana CLI installed${NC}"
fi

# Anchor
echo "Installing Anchor..."
if command_exists anchor; then
    echo -e "${YELLOW}Anchor already installed${NC}"
else
    cargo install --git https://github.com/coral-xyz/anchor --tag v0.29.0 anchor-cli --locked
    echo -e "${GREEN}✓ Anchor installed${NC}"
fi

echo ""
echo "========================================="
echo "Installation Summary"
echo "========================================="
echo ""

# Verify installations
echo "Checking installed tools..."
echo ""

check_tool() {
    if command_exists "$1"; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1 - Not found${NC}"
    fi
}

echo "EVM Tools:"
check_tool slither
check_tool myth
check_tool forge
check_tool echidna

echo ""
echo "Solana Tools:"
check_tool cargo
check_tool "cargo-audit"
check_tool clippy
check_tool solana
check_tool anchor

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. If Foundry was installed, run: foundryup"
echo "2. Restart your terminal or run: source ~/.bashrc (or ~/.zshrc)"
echo "3. Set your Anthropic API key: export ANTHROPIC_API_KEY=your_key_here"
echo "4. Run: npm run tools (to verify all tools)"
echo "5. Try an audit: npm run audit -- --project ./your-project"
echo ""
