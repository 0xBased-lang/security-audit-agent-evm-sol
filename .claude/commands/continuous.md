# Continuous Security Monitoring Command

Setup continuous security monitoring for your blockchain project (CI/CD integration).

## Usage

```
/continuous <subcommand> [options]
```

## Subcommands

- `setup`: Initialize continuous monitoring for the project
- `status`: Check current monitoring configuration
- `disable`: Disable continuous monitoring

## Description

Continuous security monitoring shifts from **point-in-time audits** to **ongoing security validation**.

**Traditional Approach** (Point-in-Time):
```
Write code → Deploy → Audit (1 week later) → Find bugs → Fix → Re-audit
```

**Continuous Approach**:
```
Write code → Auto-audit (2 min) → Commit → Deploy with confidence
```

## Your Task

### For `setup` Command

1. **Detect CI/CD Environment**:
   ```bash
   # Check for existing CI/CD configuration
   if [ -f .github/workflows/*.yml ]; then
       PLATFORM="GitHub Actions"
   elif [ -f .gitlab-ci.yml ]; then
       PLATFORM="GitLab CI"
   elif [ -f .circleci/config.yml ]; then
       PLATFORM="CircleCI"
   else
       PLATFORM="Unknown - will create GitHub Actions workflow"
   fi
   ```

2. **Create CI/CD Workflow**:

   **For GitHub Actions**:
   ```bash
   # Create workflow file
   mkdir -p .github/workflows

   # Generate security workflow
   cat > .github/workflows/security-audit.yml << 'EOF'
   name: Security Audit

   on:
     push:
       branches: [ main, develop ]
     pull_request:
       branches: [ main, develop ]
     schedule:
       # Run daily at 2 AM UTC
       - cron: '0 2 * * *'

   jobs:
     security-audit:
       runs-on: ubuntu-latest

       steps:
         - uses: actions/checkout@v3

         - name: Setup Node.js
           uses: actions/setup-node@v3
           with:
             node-version: '18'

         - name: Setup Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'

         - name: Install dependencies
           run: |
             npm install
             pip install -r requirements.txt || true

         - name: Install Foundry
           uses: foundry-rs/foundry-toolchain@v1

         - name: Run security audit
           env:
             ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
           run: |
             python -m src --quick .

         - name: Upload audit results
           uses: actions/upload-artifact@v3
           with:
             name: security-audit-report
             path: audit-results/

         - name: Comment on PR (if PR)
           if: github.event_name == 'pull_request'
           uses: actions/github-script@v6
           with:
             script: |
               const fs = require('fs');
               const report = JSON.parse(fs.readFileSync('audit-results/comprehensive-report.json', 'utf8'));

               let comment = `## 🔒 Security Audit Results\n\n`;
               comment += `- **Critical**: ${report.statistics.critical}\n`;
               comment += `- **High**: ${report.statistics.high}\n`;
               comment += `- **Medium**: ${report.statistics.medium}\n`;
               comment += `- **Low**: ${report.statistics.low}\n\n`;

               if (report.statistics.critical > 0) {
                 comment += `❌ **CRITICAL VULNERABILITIES FOUND - DO NOT MERGE**\n\n`;
               } else if (report.statistics.high > 0) {
                 comment += `⚠️ **HIGH SEVERITY ISSUES FOUND - REVIEW REQUIRED**\n\n`;
               } else {
                 comment += `✅ **No critical or high severity issues found**\n\n`;
               }

               github.rest.issues.createComment({
                 issue_number: context.issue.number,
                 owner: context.repo.owner,
                 repo: context.repo.repo,
                 body: comment
               });

         - name: Fail if critical vulnerabilities
           run: |
             CRITICAL=$(jq '.statistics.critical' audit-results/comprehensive-report.json)
             if [ "$CRITICAL" -gt 0 ]; then
               echo "❌ Critical vulnerabilities found!"
               exit 1
             fi
   EOF
   ```

3. **Setup Pre-Commit Hook** (Optional):
   ```bash
   # Create git pre-commit hook
   cat > .git/hooks/pre-commit << 'EOF'
   #!/bin/bash

   echo "🔍 Running quick security audit..."

   # Run quick audit (2-5 min)
   python -m src --quick . || {
       echo "❌ Security audit failed!"
       echo "   Fix vulnerabilities or use 'git commit --no-verify' to skip"
       exit 1
   }

   echo "✅ Security audit passed"
   EOF

   chmod +x .git/hooks/pre-commit
   ```

4. **Configure Secrets**:
   - Remind user to add `ANTHROPIC_API_KEY` to repository secrets
   - Show instructions for their CI/CD platform

5. **Test Configuration**:
   ```bash
   # Verify workflow is valid
   if command -v gh &> /dev/null; then
       gh workflow view security-audit.yml
   fi
   ```

6. **Report Success**:
   ```
   ✅ Continuous monitoring configured!

   📋 What was created:
   - .github/workflows/security-audit.yml (GitHub Actions)
   - .git/hooks/pre-commit (local pre-commit hook)

   🔧 Configuration:
   - Runs on: push to main/develop, pull requests, daily at 2 AM
   - Mode: quick (2-5 min, traditional tools only)
   - Fails CI if critical vulnerabilities found

   ⚙️ Next steps:
   1. Add ANTHROPIC_API_KEY to repository secrets:
      Settings → Secrets → New repository secret

   2. Commit and push the workflow:
      git add .github/workflows/security-audit.yml
      git commit -m "feat: Add continuous security monitoring"
      git push

   3. Verify workflow runs:
      Actions tab → Security Audit workflow

   🔄 The workflow will now automatically:
   - Audit every commit
   - Comment on pull requests with findings
   - Block merges if critical vulnerabilities found
   - Send daily security reports
   ```

### For `status` Command

1. **Check Configuration**:
   ```bash
   # Check if workflow exists
   if [ -f .github/workflows/security-audit.yml ]; then
       echo "✅ GitHub Actions workflow: configured"
   else
       echo "❌ GitHub Actions workflow: not found"
   fi

   # Check pre-commit hook
   if [ -f .git/hooks/pre-commit ]; then
       echo "✅ Pre-commit hook: enabled"
   else
       echo "❌ Pre-commit hook: not configured"
   fi

   # Check recent runs (if gh CLI available)
   if command -v gh &> /dev/null; then
       echo "\n📊 Recent workflow runs:"
       gh run list --workflow=security-audit.yml --limit 5
   fi
   ```

2. **Show Configuration Details**:
   ```
   📋 Continuous Monitoring Status

   Platform: GitHub Actions
   Workflow: .github/workflows/security-audit.yml
   Status: Active ✅

   Triggers:
   - ✅ Push to main/develop
   - ✅ Pull requests
   - ✅ Daily schedule (2 AM UTC)

   Configuration:
   - Mode: quick
   - Duration: ~2-5 minutes
   - Fails on: Critical vulnerabilities

   Recent runs:
   - 2025-01-20 10:23: ✅ Success (0 critical)
   - 2025-01-19 14:15: ✅ Success (0 critical)
   - 2025-01-18 09:42: ❌ Failed (2 critical)
   ```

### For `disable` Command

1. **Remove Configuration**:
   ```bash
   # Backup before removing
   if [ -f .github/workflows/security-audit.yml ]; then
       mv .github/workflows/security-audit.yml .github/workflows/security-audit.yml.disabled
       echo "✅ Workflow disabled (renamed to .disabled)"
   fi

   # Remove pre-commit hook
   if [ -f .git/hooks/pre-commit ]; then
       rm .git/hooks/pre-commit
       echo "✅ Pre-commit hook removed"
   fi
   ```

2. **Confirm**:
   ```
   ⚠️ Continuous monitoring has been disabled.

   To re-enable:
   - Run: /continuous setup
   - Or rename: .github/workflows/security-audit.yml.disabled
   ```

## Advanced Configuration

### Custom Audit Mode

User can customize by editing `.github/workflows/security-audit.yml`:

```yaml
# Change from --quick to --standard or --deep
run: python -m src --standard .
```

### Specific Tools

```yaml
run: python -m src --quick --tools slither,mythril .
```

### Scheduled Deep Audits

```yaml
schedule:
  # Quick audit daily
  - cron: '0 2 * * *'
  # Deep audit weekly (Sunday 3 AM)
  - cron: '0 3 * * 0'

jobs:
  quick-audit:
    # ... quick audit configuration

  deep-audit:
    if: github.event.schedule == '0 3 * * 0'
    # ... deep audit configuration
```

## CI/CD Platform Support

### GitHub Actions
- Full support with PR comments
- Artifact uploads
- Secret management

### GitLab CI
```yaml
# .gitlab-ci.yml
security-audit:
  stage: test
  script:
    - python -m src --quick .
  artifacts:
    paths:
      - audit-results/
    expire_in: 30 days
  only:
    - merge_requests
    - main
```

### CircleCI
```yaml
# .circleci/config.yml
jobs:
  security-audit:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run: pip install -r requirements.txt
      - run: python -m src --quick .
      - store_artifacts:
          path: audit-results/
```

## Benefits of Continuous Monitoring

1. **Early Detection**: Find vulnerabilities in hours, not weeks
2. **Prevent Regressions**: Catch new bugs immediately
3. **Block Risky Merges**: CI fails if critical issues found
4. **Audit Trail**: Historical record of security posture
5. **Developer Feedback**: Instant feedback loop
6. **Cost Savings**: Catch bugs before external audit

## Best Practices

1. **Start with Quick Mode**: Fast feedback (2-5 min)
2. **Deep Audits Weekly**: Comprehensive check (2-4 hours)
3. **Block Critical**: Always fail CI on critical findings
4. **Daily Scans**: Catch supply chain issues
5. **Track History**: Keep audit artifacts for compliance

## Example Workflow

```
Developer Flow:
1. Developer writes code
2. Pre-commit hook: Quick audit (2 min)
3. Push to branch
4. CI runs: Quick audit (2 min)
5. Open PR
6. CI comments on PR with findings
7. Developer fixes issues
8. Merge to main (blocked if critical)
9. Daily deep audit (scheduled)
```

## Troubleshooting

**"Workflow not found"**:
- Ensure `.github/workflows/` directory exists
- Check file permissions

**"ANTHROPIC_API_KEY not set"**:
- Add to repository secrets (Settings → Secrets)

**"Audit takes too long"**:
- Use `--quick` mode for CI
- Reserve `--deep` for scheduled runs

**"Too many false positives"**:
- Customize tools: `--tools slither,mythril`
- Add suppression rules (future feature)

## Reference

- `docs/MLSS_ARCHITECTURE_PART3.md`: Layer 10 - Continuous Risk Engine
- `docs/UNIFIED_FRAMEWORK_GUIDE.md`: Framework usage

---

**Pro Tip**: Start with quick audits on PR. Once stable, add weekly deep audits for comprehensive security.
