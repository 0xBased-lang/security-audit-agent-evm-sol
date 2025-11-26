#!/bin/bash
# Post-Audit Hook for Security Audit Framework
#
# This hook runs AFTER Claude Code completes an audit to:
# 1. Generate summary report
# 2. Calculate security score
# 3. Send notifications (Slack/Discord)
# 4. Archive results
# 5. Update metrics
#
# Usage: Called automatically by Claude Code or manually via:
#   .claude/hooks/post-audit.sh [results-dir] [project-name]
#
# Exit codes:
#   0 - Success
#   1 - Report generation failed
#   2 - Notification failed (non-blocking)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Arguments
RESULTS_DIR="${1:-./audit-results}"
PROJECT_NAME="${2:-unnamed-project}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  POST-AUDIT PROCESSING${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ============================================================================
# 1. VALIDATE RESULTS
# ============================================================================
echo -e "${BLUE}[1/5] Validating Audit Results${NC}"

FINDINGS_FILE="$RESULTS_DIR/adversarial-findings.json"
SLITHER_FILE="$RESULTS_DIR/slither.json"

if [ ! -f "$FINDINGS_FILE" ]; then
    echo -e "  ${YELLOW}⚠${NC} adversarial-findings.json not found"
    FINDINGS_FILE=""
fi

if [ ! -f "$SLITHER_FILE" ]; then
    echo -e "  ${YELLOW}⚠${NC} slither.json not found"
    SLITHER_FILE=""
fi

if [ -z "$FINDINGS_FILE" ] && [ -z "$SLITHER_FILE" ]; then
    echo -e "  ${RED}✗${NC} No audit results found in $RESULTS_DIR"
    exit 1
fi

echo -e "  ${GREEN}✓${NC} Audit results validated"
echo ""

# ============================================================================
# 2. CALCULATE SECURITY SCORE
# ============================================================================
echo -e "${BLUE}[2/5] Calculating Security Score${NC}"

# Parse findings from JSON
if [ -f "$FINDINGS_FILE" ]; then
    # Use Python for JSON parsing
    STATS=$(python3 << EOF
import json
import sys

try:
    with open("$FINDINGS_FILE") as f:
        data = json.load(f)

    stats = data.get("statistics", {})
    critical = stats.get("critical", 0)
    high = stats.get("high", 0)
    medium = stats.get("medium", 0)
    low = stats.get("low", 0)
    total = stats.get("total", 0)

    # Calculate security score (100 = perfect, 0 = critical issues)
    # Penalties: Critical=-50, High=-15, Medium=-5, Low=-1
    score = 100 - (critical * 50) - (high * 15) - (medium * 5) - (low * 1)
    score = max(0, min(100, score))

    # Determine grade
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"

    print(f"{score}|{grade}|{critical}|{high}|{medium}|{low}|{total}")
except Exception as e:
    print(f"0|F|0|0|0|0|0")
    sys.exit(1)
EOF
)

    IFS='|' read -r SCORE GRADE CRITICAL HIGH MEDIUM LOW TOTAL <<< "$STATS"
else
    SCORE=0
    GRADE="?"
    CRITICAL=0
    HIGH=0
    MEDIUM=0
    LOW=0
    TOTAL=0
fi

echo -e "  Security Score: ${CYAN}$SCORE/100${NC} (Grade: $GRADE)"
echo -e "  Findings:"
echo -e "    Critical: ${RED}$CRITICAL${NC}"
echo -e "    High: ${YELLOW}$HIGH${NC}"
echo -e "    Medium: ${BLUE}$MEDIUM${NC}"
echo -e "    Low: $LOW"
echo -e "    Total: $TOTAL"
echo ""

# ============================================================================
# 3. GENERATE SUMMARY REPORT
# ============================================================================
echo -e "${BLUE}[3/5] Generating Summary Report${NC}"

SUMMARY_FILE="$RESULTS_DIR/AUDIT_SUMMARY.md"

cat > "$SUMMARY_FILE" << EOF
# Security Audit Summary

**Project**: $PROJECT_NAME
**Date**: $(date +"%Y-%m-%d %H:%M:%S")
**Audit Framework Version**: 1.0.0

---

## Security Score

| Metric | Value |
|--------|-------|
| **Score** | $SCORE/100 |
| **Grade** | $GRADE |
| **Risk Level** | $([ "$CRITICAL" -gt 0 ] && echo "🔴 CRITICAL" || ([ "$HIGH" -gt 0 ] && echo "🟠 HIGH" || ([ "$MEDIUM" -gt 0 ] && echo "🟡 MEDIUM" || echo "🟢 LOW"))) |

## Findings Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | $CRITICAL |
| 🟠 High | $HIGH |
| 🟡 Medium | $MEDIUM |
| 🔵 Low | $LOW |
| **Total** | **$TOTAL** |

## Risk Assessment

$(if [ "$CRITICAL" -gt 0 ]; then
    echo "### 🚨 CRITICAL ISSUES FOUND"
    echo ""
    echo "**DO NOT DEPLOY** until all critical issues are resolved."
    echo ""
    echo "Critical vulnerabilities can result in:"
    echo "- Complete loss of funds"
    echo "- Protocol takeover"
    echo "- Irreversible damage"
elif [ "$HIGH" -gt 0 ]; then
    echo "### ⚠️  HIGH SEVERITY ISSUES"
    echo ""
    echo "**Address before deployment.** High severity issues may lead to significant financial loss."
else
    echo "### ✅ No Critical/High Issues"
    echo ""
    echo "The protocol appears reasonably secure. Review medium/low findings for improvements."
fi)

## Recommendations

1. **Immediate Actions**:
$([ "$CRITICAL" -gt 0 ] && echo "   - Fix all critical vulnerabilities immediately" || echo "   - No critical issues requiring immediate action")
$([ "$HIGH" -gt 0 ] && echo "   - Address high severity findings before deployment")

2. **Before Deployment**:
   - Conduct professional audit review
   - Run comprehensive test suite
   - Verify fixes don't introduce new issues

3. **Ongoing Security**:
   - Implement monitoring and alerting
   - Consider bug bounty program
   - Regular security reviews

## Files Generated

- \`adversarial-findings.json\` - Detailed findings in JSON format
- \`slither.json\` - Slither analysis results (if available)
- \`AUDIT_SUMMARY.md\` - This summary report

---

*Generated by Security Audit Framework*
*Report ID: ${TIMESTAMP}*
EOF

echo -e "  ${GREEN}✓${NC} Summary report: $SUMMARY_FILE"
echo ""

# ============================================================================
# 4. SEND NOTIFICATIONS
# ============================================================================
echo -e "${BLUE}[4/5] Sending Notifications${NC}"

# Check for Slack webhook
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    SLACK_COLOR=$([ "$CRITICAL" -gt 0 ] && echo "danger" || ([ "$HIGH" -gt 0 ] && echo "warning" || echo "good"))

    curl -s -X POST -H 'Content-type: application/json' \
        --data "{
            \"attachments\": [{
                \"color\": \"$SLACK_COLOR\",
                \"title\": \"Security Audit Complete: $PROJECT_NAME\",
                \"text\": \"Score: $SCORE/100 ($GRADE) | Critical: $CRITICAL | High: $HIGH | Medium: $MEDIUM | Low: $LOW\",
                \"footer\": \"Security Audit Framework\",
                \"ts\": $(date +%s)
            }]
        }" \
        "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 && \
        echo -e "  ${GREEN}✓${NC} Slack notification sent" || \
        echo -e "  ${YELLOW}⚠${NC} Slack notification failed"
else
    echo -e "  ${YELLOW}⚠${NC} SLACK_WEBHOOK_URL not set - skipping Slack notification"
fi

# Check for Discord webhook
if [ -n "$DISCORD_WEBHOOK_URL" ]; then
    DISCORD_COLOR=$([ "$CRITICAL" -gt 0 ] && echo "15158332" || ([ "$HIGH" -gt 0 ] && echo "16776960" || echo "3066993"))

    curl -s -X POST -H 'Content-type: application/json' \
        --data "{
            \"embeds\": [{
                \"title\": \"Security Audit Complete: $PROJECT_NAME\",
                \"description\": \"Score: $SCORE/100 ($GRADE)\",
                \"color\": $DISCORD_COLOR,
                \"fields\": [
                    {\"name\": \"Critical\", \"value\": \"$CRITICAL\", \"inline\": true},
                    {\"name\": \"High\", \"value\": \"$HIGH\", \"inline\": true},
                    {\"name\": \"Medium\", \"value\": \"$MEDIUM\", \"inline\": true}
                ]
            }]
        }" \
        "$DISCORD_WEBHOOK_URL" > /dev/null 2>&1 && \
        echo -e "  ${GREEN}✓${NC} Discord notification sent" || \
        echo -e "  ${YELLOW}⚠${NC} Discord notification failed"
else
    echo -e "  ${YELLOW}⚠${NC} DISCORD_WEBHOOK_URL not set - skipping Discord notification"
fi

echo ""

# ============================================================================
# 5. ARCHIVE RESULTS
# ============================================================================
echo -e "${BLUE}[5/5] Archiving Results${NC}"

ARCHIVE_DIR="$RESULTS_DIR/archive"
mkdir -p "$ARCHIVE_DIR"

ARCHIVE_NAME="${PROJECT_NAME}_${TIMESTAMP}"
ARCHIVE_PATH="$ARCHIVE_DIR/$ARCHIVE_NAME"

mkdir -p "$ARCHIVE_PATH"
cp -r "$RESULTS_DIR"/*.json "$ARCHIVE_PATH/" 2>/dev/null || true
cp -r "$RESULTS_DIR"/*.md "$ARCHIVE_PATH/" 2>/dev/null || true

echo -e "  ${GREEN}✓${NC} Results archived to: $ARCHIVE_PATH"

# Create metrics entry
METRICS_FILE="$RESULTS_DIR/metrics.csv"
if [ ! -f "$METRICS_FILE" ]; then
    echo "timestamp,project,score,grade,critical,high,medium,low,total" > "$METRICS_FILE"
fi
echo "$TIMESTAMP,$PROJECT_NAME,$SCORE,$GRADE,$CRITICAL,$HIGH,$MEDIUM,$LOW,$TOTAL" >> "$METRICS_FILE"
echo -e "  ${GREEN}✓${NC} Metrics updated: $METRICS_FILE"

echo ""

# ============================================================================
# FINAL SUMMARY
# ============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  POST-AUDIT COMPLETE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "  Project: $PROJECT_NAME"
echo -e "  Score: ${CYAN}$SCORE/100${NC} (Grade: $GRADE)"
echo -e "  Risk Level: $([ "$CRITICAL" -gt 0 ] && echo "${RED}CRITICAL${NC}" || ([ "$HIGH" -gt 0 ] && echo "${YELLOW}HIGH${NC}" || ([ "$MEDIUM" -gt 0 ] && echo "${BLUE}MEDIUM${NC}" || echo "${GREEN}LOW${NC}")))"
echo ""
echo -e "  ${GREEN}✓${NC} Summary report: $SUMMARY_FILE"
echo -e "  ${GREEN}✓${NC} Archive: $ARCHIVE_PATH"
echo ""

# Output JSON for Claude Code
cat > /tmp/post-audit-result.json << EOF
{
  "status": "success",
  "project": "$PROJECT_NAME",
  "timestamp": "$TIMESTAMP",
  "score": $SCORE,
  "grade": "$GRADE",
  "findings": {
    "critical": $CRITICAL,
    "high": $HIGH,
    "medium": $MEDIUM,
    "low": $LOW,
    "total": $TOTAL
  },
  "files": {
    "summary": "$SUMMARY_FILE",
    "archive": "$ARCHIVE_PATH"
  }
}
EOF

echo -e "${BLUE}Post-audit data saved to /tmp/post-audit-result.json${NC}"
exit 0
