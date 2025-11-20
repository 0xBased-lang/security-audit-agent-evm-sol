"""
Allow running the unified framework as a module:
python -m src <args>
"""

from .unified_cli import main
import asyncio

if __name__ == '__main__':
    asyncio.run(main())
