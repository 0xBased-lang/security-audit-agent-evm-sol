# Contributing to Security Audit Framework

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Node version, tool versions)

### Suggesting Features

1. Open an issue with the "feature request" label
2. Describe the feature and its use case
3. Explain why it would be valuable

### Contributing Code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write/update tests as needed
5. Ensure all tests pass
6. Update documentation
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to your branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/security-audit-agent-evm-sol.git
cd security-audit-agent-evm-sol

# Install dependencies
npm install

# Install security tools
bash scripts/install-tools.sh

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run tests
npm test
```

## Code Style

- Use clear, descriptive variable names
- Add JSDoc comments for functions
- Follow existing code patterns
- Keep functions focused and small
- Handle errors explicitly

## Adding New Tools

To integrate a new security tool:

1. Add tool executor in `src/evm/` or `src/solana/`
2. Implement finding parser to standard format
3. Add tool to configuration options
4. Update documentation in `docs/TOOL_INTEGRATION.md`
5. Add tests

Example:
```javascript
async runNewTool() {
    const command = 'newtool analyze ./contracts';
    const { stdout } = await execAsync(command);
    return {
        findings: this.parseNewToolFindings(JSON.parse(stdout)),
        raw: stdout
    };
}
```

## Adding Vulnerability Patterns

To add new vulnerability detection:

1. Research the vulnerability thoroughly
2. Add detection pattern to relevant auditor
3. Document in `docs/VULNERABILITIES.md`:
   - Description
   - Vulnerable code example
   - Secure code example
   - Detection methods
   - Mitigation strategies
4. Add test cases

## Documentation

- Update README.md for user-facing changes
- Update relevant docs in `docs/` directory
- Add examples in `examples/` if applicable
- Update CLAUDE.md for Claude Code integration changes

## Testing

### Running Tests

```bash
# All tests
npm test

# Specific test file
npm test -- path/to/test.js

# With coverage
npm test -- --coverage
```

### Writing Tests

- Test happy path and edge cases
- Mock external dependencies
- Use descriptive test names
- Keep tests focused and independent

Example:
```javascript
describe('EVMAuditor', () => {
    it('should detect reentrancy vulnerabilities', async () => {
        const auditor = new EVMAuditor(config);
        const results = await auditor.audit();

        const reentrancyFindings = results.findings.filter(
            f => f.category === 'reentrancy'
        );

        expect(reentrancyFindings.length).toBeGreaterThan(0);
    });
});
```

## Pull Request Process

1. Update CHANGELOG.md with your changes
2. Ensure all tests pass
3. Update documentation as needed
4. Request review from maintainers
5. Address review feedback
6. Once approved, a maintainer will merge

## Code of Conduct

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

## Questions?

- Open a discussion on GitHub
- Check existing documentation
- Review closed issues for similar questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to blockchain security! 🔒
