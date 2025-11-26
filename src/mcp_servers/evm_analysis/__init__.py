"""
EVM Analysis MCP Server
Orchestrates static analysis tools (Slither, Mythril, Foundry)
"""

from .server import app

__all__ = ["app"]
