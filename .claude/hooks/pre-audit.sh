#!/bin/bash
# Pre-Audit Hook for Security Audit Framework
#
# This hook runs BEFORE Claude Code starts an audit to:
# 1. Validate tool availability
# 2. Check project structure
# 3. Verify environment setup
# 4. Estimate audit complexity
#
# Usage: Called automatically by Claude Code or manually via:
#   .claude/hooks/pre-audit.sh [project-path] [mode]
#
# Exit codes:
#   0 - All checks passed
#   1 - Critical tool missing
#   2 - Project structure invalid
#   3 - Environment issue

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Arguments
PROJECT_PATH="${1:-.}"
AUDIT_MODE="${2:-standard}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  PRE-AUDIT VALIDATION${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Track issues
WARNINGS=0
ERRORS=0

# ============================================================================
# 1. TOOL AVAILABILITY CHECK
# ============================================================================
echo -e "${BLUE}[1/4] Checking Tool Availability${NC}"

check_tool() {
    local tool=$1
    local required=$2
    local install_hint=$3

    if command -v "$tool" &> /dev/null; then
        version=$($tool --version 2>/dev/null | head -1 || echo "unknown")
        echo -e "  ${GREEN}✓${NC} $tool: $version"
        return 0
    else
        if [ "$required" = "required" ]; then
            echo -e "  ${RED}✗${NC} $tool: NOT FOUND (REQUIRED)"
            echo -e "    ${YELLOW}Install: $install_hint${NC}"
            ((ERRORS++))
            return 1
        else
            echo -e "  ${YELLOW}⚠${NC} $tool: NOT FOUND (optional)"
            ((WARNINGS++))
            return 0
        fi
    fi
}

# Required tools
check_tool "python3" "required" "brew install python3"
check_tool "node" "required" "brew install node"
check_tool "slither" "required" "pip install slither-analyzer"

# Optional but recommended tools
check_tool "forge" "optional" "curl -L https://foundry.paradigm.xyz | bash"
check_tool "myth" "optional" "pip install mythril"
check_tool "echidna" "optional" "brew install echidna"

echo ""

# ============================================================================
# 2. PROJECT STRUCTURE VALIDATION
# ============================================================================
echo -e "${BLUE}[2/4] Validating Project Structure${NC}"

# Check if project path exists
if [ ! -d "$PROJECT_PATH" ]; then
    echo -e "  ${RED}✗${NC} Project path not found: $PROJECT_PATH"
    exit 2
fi

# Detect chain type
SOL_FILES=$(find "$PROJECT_PATH" -name "*.sol" -type f 2>/dev/null | wc -l | tr -d ' ')
RS_FILES=$(find "$PROJECT_PATH" -path "*/programs/*" -name "*.rs" -type f 2>/dev/null | wc -l | tr -d ' ')

if [ "$SOL_FILES" -gt 0 ] && [ "$RS_FILES" -gt 0 ]; then
    CHAIN="multi-chain"
    echo -e "  ${GREEN}✓${NC} Chain: Multi-chain (EVM + Solana)"
elif [ "$SOL_FILES" -gt 0 ]; then
    CHAIN="evm"
    echo -e "  ${GREEN}✓${NC} Chain: EVM (found $SOL_FILES Solidity files)"
elif [ "$RS_FILES" -gt 0 ]; then
    CHAIN="solana"
    echo -e "  ${GREEN}✓${NC} Chain: Solana (found $RS_FILES Rust files)"
else
    echo -e "  ${RED}✗${NC} No smart contracts found (.sol or .rs files)"
    exit 2
fi

# Check for common config files
if [ -f "$PROJECT_PATH/foundry.toml" ]; then
    echo -e "  ${GREEN}✓${NC} Foundry project detected"
fi
if [ -f "$PROJECT_PATH/hardhat.config.js" ] || [ -f "$PROJECT_PATH/hardhat.config.ts" ]; then
    echo -e "  ${GREEN}✓${NC} Hardhat project detected"
fi
if [ -f "$PROJECT_PATH/Anchor.toml" ]; then
    echo -e "  ${GREEN}✓${NC} Anchor project detected"
fi

echo ""

# ============================================================================
# 3. ENVIRONMENT VALIDATION
# ============================================================================
echo -e "${BLUE}[3/4] Validating Environment${NC}"

# Check Python environment
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
    echo -e "  ${GREEN}✓${NC} Python version: $PYTHON_VERSION (>= 3.8)"
else
    echo -e "  ${YELLOW}⚠${NC} Python version: $PYTHON_VERSION (recommend >= 3.8)"
    ((WARNINGS++))
fi

# Check Node.js version
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | tr -d 'v')
    NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d'.' -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        echo -e "  ${GREEN}✓${NC} Node.js version: $NODE_VERSION (>= 18)"
    else
        echo -e "  ${YELLOW}⚠${NC} Node.js version: $NODE_VERSION (recommend >= 18)"
        ((WARNINGS++))
    fi
fi

# Check disk space (need at least 1GB for reports)
AVAILABLE_SPACE=$(df -k . | awk 'NR==2 {print $4}')
if [ "$AVAILABLE_SPACE" -gt 1048576 ]; then
    echo -e "  ${GREEN}✓${NC} Disk space: $(($AVAILABLE_SPACE / 1024))MB available"
else
    echo -e "  ${YELLOW}⚠${NC} Low disk space: $(($AVAILABLE_SPACE / 1024))MB available"
    ((WARNINGS++))
fi

echo ""

# ============================================================================
# 4. COMPLEXITY ESTIMATION
# ============================================================================
echo -e "${BLUE}[4/4] Estimating Audit Complexity${NC}"

# Count lines of code
if [ "$CHAIN" = "evm" ] || [ "$CHAIN" = "multi-chain" ]; then
    SOL_LOC=$(find "$PROJECT_PATH" -name "*.sol" -type f -exec cat {} \; 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  Solidity LOC: $SOL_LOC"
fi

if [ "$CHAIN" = "solana" ] || [ "$CHAIN" = "multi-chain" ]; then
    RS_LOC=$(find "$PROJECT_PATH" -path "*/programs/*" -name "*.rs" -type f -exec cat {} \; 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  Rust LOC: $RS_LOC"
fi

# Estimate time based on mode and LOC
TOTAL_LOC=$((${SOL_LOC:-0} + ${RS_LOC:-0}))

case $AUDIT_MODE in
    quick)
        if [ "$TOTAL_LOC" -lt 500 ]; then
            ESTIMATE="1-2 minutes"
        elif [ "$TOTAL_LOC" -lt 2000 ]; then
            ESTIMATE="2-5 minutes"
        else
            ESTIMATE="5-10 minutes"
        fi
        ;;
    standard)
        if [ "$TOTAL_LOC" -lt 500 ]; then
            ESTIMATE="5-10 minutes"
        elif [ "$TOTAL_LOC" -lt 2000 ]; then
            ESTIMATE="10-20 minutes"
        else
            ESTIMATE="20-30 minutes"
        fi
        ;;
    deep)
        if [ "$TOTAL_LOC" -lt 500 ]; then
            ESTIMATE="15-30 minutes"
        elif [ "$TOTAL_LOC" -lt 2000 ]; then
            ESTIMATE="30-60 minutes"
        else
            ESTIMATE="60+ minutes"
        fi
        ;;
esac

echo -e "  ${BLUE}Estimated audit time ($AUDIT_MODE mode): $ESTIMATE${NC}"

# Complexity flags
COMPLEXITY="low"
if [ "$TOTAL_LOC" -gt 2000 ]; then
    COMPLEXITY="high"
    echo -e "  ${YELLOW}⚠${NC} Large codebase - consider using wave mode"
elif [ "$TOTAL_LOC" -gt 1000 ]; then
    COMPLEXITY="medium"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  PRE-AUDIT SUMMARY${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "  Chain: $CHAIN"
echo -e "  Mode: $AUDIT_MODE"
echo -e "  Complexity: $COMPLEXITY"
echo -e "  Total LOC: $TOTAL_LOC"
echo -e "  Estimated time: $ESTIMATE"
echo -e "  Warnings: $WARNINGS"
echo -e "  Errors: $ERRORS"
echo ""

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}✗ Pre-audit validation FAILED${NC}"
    echo -e "${RED}  Please fix $ERRORS error(s) before proceeding${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Pre-audit validation PASSED${NC}"
    if [ "$WARNINGS" -gt 0 ]; then
        echo -e "${YELLOW}  ($WARNINGS warning(s) - audit can proceed)${NC}"
    fi
fi

# Output JSON for Claude Code to read
cat > /tmp/pre-audit-result.json << EOF
{
  "status": "passed",
  "chain": "$CHAIN",
  "mode": "$AUDIT_MODE",
  "complexity": "$COMPLEXITY",
  "total_loc": $TOTAL_LOC,
  "estimated_time": "$ESTIMATE",
  "warnings": $WARNINGS,
  "errors": $ERRORS,
  "tools": {
    "slither": $(command -v slither &> /dev/null && echo "true" || echo "false"),
    "mythril": $(command -v myth &> /dev/null && echo "true" || echo "false"),
    "foundry": $(command -v forge &> /dev/null && echo "true" || echo "false"),
    "echidna": $(command -v echidna &> /dev/null && echo "true" || echo "false")
  }
}
EOF

echo -e "\n${BLUE}Pre-audit data saved to /tmp/pre-audit-result.json${NC}"
exit 0
