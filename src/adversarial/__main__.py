#!/usr/bin/env python3
"""
Entry point for running adversarial testing as a module.

Usage:
    python -m src.adversarial.unified_orchestrator --project ./path --mode quick

Or via CLI:
    node src/cli.js adversarial --project ./path --mode quick
"""

from .unified_orchestrator import main

if __name__ == "__main__":
    main()
