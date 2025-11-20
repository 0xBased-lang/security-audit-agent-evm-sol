#!/usr/bin/env python3
"""
Unified CLI for Security Audit Framework

Provides command-line interface for running unified audits.
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path

from .unified_framework import (
    UnifiedSecurityFramework,
    quick_audit,
    standard_audit,
    deep_audit,
)
from .config import AuditConfig


def setup_cli_parser() -> argparse.ArgumentParser:
    """Setup command-line argument parser"""

    parser = argparse.ArgumentParser(
        description='Unified Blockchain Security Audit Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick audit (2-5 min)
  %(prog)s --quick ./my-project

  # Standard audit (30-60 min)
  %(prog)s ./my-project

  # Deep audit (2-4 hours)
  %(prog)s --deep ./my-project

  # Specify chain
  %(prog)s --chain polygon ./my-project

  # Custom configuration
  %(prog)s --tools slither,mythril --iterations 5000 ./my-project
        """
    )

    # Project path
    parser.add_argument(
        'project_path',
        type=str,
        help='Path to smart contract project'
    )

    # Audit modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--quick',
        action='store_const',
        const='quick',
        dest='mode',
        help='Quick audit (traditional tools only, 2-5 min)'
    )
    mode_group.add_argument(
        '--standard',
        action='store_const',
        const='standard',
        dest='mode',
        help='Standard audit (traditional + basic adversarial, 30-60 min) [default]'
    )
    mode_group.add_argument(
        '--deep',
        action='store_const',
        const='deep',
        dest='mode',
        help='Deep audit (full 10-layer AASS, 2-4 hours)'
    )

    # Chain configuration
    parser.add_argument(
        '--chain',
        type=str,
        default='ethereum',
        help='Blockchain (ethereum, polygon, solana, etc.) [default: ethereum]'
    )
    parser.add_argument(
        '--fork-block',
        type=int,
        help='Block number to fork from'
    )

    # Traditional audit settings
    parser.add_argument(
        '--tools',
        type=str,
        help='Comma-separated list of tools to run (e.g., slither,mythril)'
    )
    parser.add_argument(
        '--no-traditional',
        action='store_true',
        help='Disable traditional audit tools'
    )

    # Adversarial testing settings
    parser.add_argument(
        '--no-adversarial',
        action='store_true',
        help='Disable adversarial testing'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        help='Number of adversarial iterations'
    )
    parser.add_argument(
        '--strategies',
        type=str,
        help='Comma-separated list of adversarial strategies'
    )

    # AI settings
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Disable AI synthesis'
    )

    # Output settings
    parser.add_argument(
        '--output',
        type=str,
        default='./audit-results',
        help='Output directory [default: ./audit-results]'
    )
    parser.add_argument(
        '--format',
        type=str,
        default='json,markdown',
        help='Output formats (json,markdown,html) [default: json,markdown]'
    )

    # Verbosity
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    parser.set_defaults(mode='standard')

    return parser


async def main():
    """Main CLI entry point"""

    # Parse arguments
    parser = setup_cli_parser()
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger('unified_cli')

    # Validate project path
    project_path = Path(args.project_path)
    if not project_path.exists():
        logger.error(f"Project path does not exist: {project_path}")
        sys.exit(1)

    # Build configuration
    config = AuditConfig(
        mode=args.mode,
        chain=args.chain,
        fork_block=args.fork_block,
        traditional_enabled=not args.no_traditional,
        traditional_tools=args.tools.split(',') if args.tools else None,
        adversarial_enabled=not args.no_adversarial,
        adversarial_iterations=args.iterations if args.iterations else None,
        adversarial_strategies=args.strategies.split(',') if args.strategies else None,
        ai_enabled=not args.no_ai,
        output_dir=args.output,
        output_formats=args.format.split(','),
        verbose=args.verbose,
    )

    # Display configuration
    logger.info("=" * 70)
    logger.info("Unified Blockchain Security Audit Framework")
    logger.info("=" * 70)
    logger.info(f"Project: {project_path}")
    logger.info(f"Mode: {config.mode}")
    logger.info(f"Chain: {config.chain}")
    logger.info(f"Traditional audit: {'enabled' if config.traditional_enabled else 'disabled'}")
    logger.info(f"Adversarial testing: {'enabled' if config.adversarial_enabled else 'disabled'}")
    if config.adversarial_enabled:
        logger.info(f"  Iterations: {config.adversarial_iterations}")
    logger.info(f"AI synthesis: {'enabled' if config.ai_enabled else 'disabled'}")
    logger.info(f"Output: {config.output_dir}")
    logger.info("=" * 70)

    try:
        # Initialize framework
        framework = UnifiedSecurityFramework(config=config)

        # Run audit
        logger.info("Starting audit...")
        report = await framework.audit(str(project_path))

        # Display summary
        logger.info("=" * 70)
        logger.info("AUDIT COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Duration: {report.duration_seconds:.1f}s")
        logger.info(f"Total vulnerabilities: {report.total_vulnerabilities}")
        logger.info(f"  Critical: {report.critical_count}")
        logger.info(f"  High: {report.high_count}")
        logger.info(f"  Medium: {report.medium_count}")
        logger.info(f"  Low: {report.low_count}")
        logger.info(f"  Info: {report.info_count}")
        logger.info("=" * 70)

        # Display critical vulnerabilities
        if report.critical_count > 0:
            logger.info("CRITICAL VULNERABILITIES:")
            for vuln in report.get_critical_vulnerabilities():
                logger.info(f"  • {vuln.title} ({vuln.location.file}:{vuln.location.line})")

        # Report location
        logger.info(f"\nFull report saved to: {config.output_dir}/")

        # Exit with appropriate code
        if report.critical_count > 0:
            sys.exit(2)  # Critical vulnerabilities found
        elif report.high_count > 0:
            sys.exit(1)  # High vulnerabilities found
        else:
            sys.exit(0)  # Success

    except KeyboardInterrupt:
        logger.info("\nAudit interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Audit failed: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
