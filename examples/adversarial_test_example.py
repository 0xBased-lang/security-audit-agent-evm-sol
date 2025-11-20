"""
Adversarial Testing Example

Demonstrates how to use the adversarial agent framework to test
a DeFi protocol for MEV and economic exploits.

This example tests a simple AMM for sandwich attacks, oracle manipulation,
and flash loan exploits.

Usage:
    python examples/adversarial_test_example.py
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from adversarial import (
    AdversarialOrchestrator,
    AdversarialTestConfig,
    AdversarialTestResults
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def basic_example():
    """
    Basic example: Test an AMM for common exploits

    This example demonstrates:
    1. Configuring adversarial testing
    2. Running evolutionary search
    3. Analyzing results
    """
    print("\n" + "="*60)
    print("Adversarial Testing Example - Basic AMM Test")
    print("="*60 + "\n")

    # Configure test
    config = AdversarialTestConfig(
        chain='evm',
        project_path='./examples/vulnerable-amm',  # Example project
        fork_block=18500000,  # Recent Ethereum mainnet block
        strategies=['sandwich', 'oracle_manipulation'],
        search_algorithm='evolutionary',
        max_iterations=100,  # Reduced for quick demo
        population_size=20,
        use_historical_mev=False,  # Disabled for demo
        ai_orchestration=False  # Disabled for demo (requires API key)
    )

    print("Configuration:")
    print(f"  Chain: {config.chain}")
    print(f"  Fork Block: {config.fork_block}")
    print(f"  Strategies: {', '.join(config.strategies)}")
    print(f"  Search Algorithm: {config.search_algorithm}")
    print(f"  Max Iterations: {config.max_iterations}\n")

    # Note: This example requires Foundry (Anvil) to be installed
    print("⚠️  Note: This example requires Foundry (Anvil)")
    print("    Install: curl -L https://foundry.paradigm.xyz | bash && foundryup\n")

    try:
        # Create orchestrator
        print("Creating adversarial orchestrator...")
        orchestrator = AdversarialOrchestrator(config)

        # Run test
        print("\n🔍 Starting adversarial testing...\n")
        results = orchestrator.run_adversarial_test()

        # Display results
        print("\n" + "="*60)
        print("✅ Test Complete!")
        print("="*60 + "\n")

        print(f"📊 Summary:")
        print(f"  Vulnerabilities found: {len(results.vulnerabilities)}")
        print(f"  Max exploit profit: ${results.max_exploit_profit:,.2f}")
        print(f"  Invariants broken: {len(results.invariants_violated)}")
        print(f"  Successful strategies: {len(results.successful_strategies)}\n")

        # Show vulnerabilities
        if results.vulnerabilities:
            print("🚨 Vulnerabilities Found:\n")
            for i, vuln in enumerate(results.vulnerabilities, 1):
                print(f"{i}. {vuln['type'].upper()}")
                print(f"   Severity: {vuln['severity']}")
                print(f"   Profit: ${vuln['profit']:,.2f}")
                print(f"   Description: {vuln['description']}\n")
        else:
            print("✅ No vulnerabilities found!\n")

        # Show recommendations
        if results.recommendations:
            print("💡 Recommendations:\n")
            for i, rec in enumerate(results.recommendations, 1):
                print(f"{i}. {rec}\n")

        # Save report
        output_file = './adversarial-report-example.md'
        orchestrator.generate_report(
            output_path=output_file,
            format='markdown'
        )
        print(f"📄 Full report saved to: {output_file}\n")

    except ImportError as e:
        print(f"\n❌ Error: Missing dependency - {e}")
        print("   Install: pip install -r requirements-adversarial.txt\n")
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure Foundry (Anvil) is installed and in your PATH\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        logger.exception("Adversarial test failed")


def advanced_example():
    """
    Advanced example: Comprehensive testing with all strategies

    This example demonstrates:
    1. Testing multiple attack vectors
    2. Using hybrid search algorithm
    3. Enabling AI orchestration
    4. Analyzing complex results
    """
    print("\n" + "="*60)
    print("Adversarial Testing Example - Advanced Multi-Strategy Test")
    print("="*60 + "\n")

    config = AdversarialTestConfig(
        chain='evm',
        project_path='./examples/defi-protocol',
        fork_block=18500000,
        strategies=[
            'sandwich',
            'oracle_manipulation',
            'flash_loan',
        ],
        search_algorithm='hybrid',  # Combine evolutionary + MCTS + DRL
        max_iterations=500,
        population_size=50,
        use_historical_mev=True,  # Learn from real MEV data
        ai_orchestration=True  # Use Claude for synthesis (requires API key)
    )

    print("⚠️  Note: This advanced example requires:")
    print("    1. Foundry (Anvil) installed")
    print("    2. ANTHROPIC_API_KEY environment variable set")
    print("    3. Longer runtime (~30-60 minutes)\n")

    try:
        orchestrator = AdversarialOrchestrator(config)
        print("🔍 Starting comprehensive adversarial testing...\n")

        results = orchestrator.run_adversarial_test()

        print("\n" + "="*60)
        print("✅ Comprehensive Test Complete!")
        print("="*60 + "\n")

        print(f"📊 Detailed Summary:")
        print(f"  Total vulnerabilities: {len(results.vulnerabilities)}")
        print(f"  Critical: {sum(1 for v in results.vulnerabilities if v['severity'] == 'CRITICAL')}")
        print(f"  High: {sum(1 for v in results.vulnerabilities if v['severity'] == 'HIGH')}")
        print(f"  Medium: {sum(1 for v in results.vulnerabilities if v['severity'] == 'MEDIUM')}")
        print(f"  Low: {sum(1 for v in results.vulnerabilities if v['severity'] == 'LOW')}\n")

        print(f"💰 Economic Impact:")
        print(f"  Maximum single exploit: ${results.max_exploit_profit:,.2f}")
        print(f"  Total potential loss: ${sum(v['profit'] for v in results.vulnerabilities):,.2f}\n")

        # Save detailed report
        orchestrator.generate_report(
            output_path='./adversarial-report-advanced.md',
            format='markdown'
        )

        print("📄 Detailed report saved to: ./adversarial-report-advanced.md\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        logger.exception("Advanced adversarial test failed")


def quick_check():
    """
    Quick check: Verify framework is properly installed

    Runs a minimal test to verify all components are working.
    """
    print("\n" + "="*60)
    print("Adversarial Framework - Quick Installation Check")
    print("="*60 + "\n")

    checks = {
        'Python packages': False,
        'Foundry (Anvil)': False,
        'Framework imports': False
    }

    # Check Python packages
    try:
        import web3
        import anthropic
        checks['Python packages'] = True
        print("✅ Python packages installed")
    except ImportError as e:
        print(f"❌ Missing Python packages: {e}")
        print("   Install: pip install -r requirements-adversarial.txt")

    # Check Foundry
    try:
        import subprocess
        result = subprocess.run(
            ['anvil', '--version'],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            checks['Foundry (Anvil)'] = True
            version = result.stdout.decode().strip()
            print(f"✅ Foundry installed: {version}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ Foundry (Anvil) not found")
        print("   Install: curl -L https://foundry.paradigm.xyz | bash && foundryup")

    # Check framework imports
    try:
        from adversarial.orchestrator import AdversarialOrchestrator
        from adversarial.simulation import EVMEnvironment
        from adversarial.strategies import SandwichAttack
        from adversarial.search import EvolutionarySearch
        from adversarial.agents import AttackerAgentFactory
        checks['Framework imports'] = True
        print("✅ Framework components available")
    except ImportError as e:
        print(f"❌ Framework import failed: {e}")

    # Summary
    print("\n" + "-"*60)
    all_good = all(checks.values())
    if all_good:
        print("✅ All checks passed! Ready to run adversarial tests.")
        print("\nNext steps:")
        print("  1. Run basic example: python examples/adversarial_test_example.py --basic")
        print("  2. Read docs: docs/ADVERSARIAL_QUICKSTART.md")
        print("  3. Try on your protocol!")
    else:
        print("⚠️  Some checks failed. Please install missing dependencies.")
        print("\nSee docs/ADVERSARIAL_QUICKSTART.md for installation guide.")
    print("-"*60 + "\n")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Adversarial Testing Example')
    parser.add_argument(
        '--mode',
        choices=['quick', 'basic', 'advanced'],
        default='quick',
        help='Test mode to run'
    )

    args = parser.parse_args()

    if args.mode == 'quick':
        quick_check()
    elif args.mode == 'basic':
        basic_example()
    elif args.mode == 'advanced':
        advanced_example()
