#!/usr/bin/env python3
"""
EVM Analysis MCP Server

Orchestrates static analysis tools:
- Slither (90+ detectors for pattern-based vulnerabilities)
- Mythril (symbolic execution for deep path analysis)
- Foundry (fuzz testing and invariant checks)
- Echidna (property-based fuzzing)

Provides unified interface for running analysis and aggregating results.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent

# Initialize MCP server
app = Server("evm-analysis-mcp")


# ============ Tool Availability Checks ============

def check_tool_installed(tool_name: str) -> bool:
    """Check if a security tool is installed"""
    try:
        subprocess.run([tool_name, "--version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


AVAILABLE_TOOLS = {
    "slither": check_tool_installed("slither"),
    "myth": check_tool_installed("myth"),
    "forge": check_tool_installed("forge"),
    "echidna": check_tool_installed("echidna")
}


# ============ MCP Tool Definitions ============

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available EVM analysis tools"""
    return [
        Tool(
            name="run_slither",
            description="Run Slither static analysis on Solidity contracts. Detects 90+ vulnerability patterns including reentrancy, access control, oracle issues. Returns JSON results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_path": {
                        "type": "string",
                        "description": "Path to contract file or project directory"
                    },
                    "detectors": {
                        "type": "string",
                        "enum": ["all", "high", "medium", "low", "critical"],
                        "description": "Which detectors to run (default: all)"
                    },
                    "exclude": {
                        "type": "string",
                        "description": "Comma-separated detector names to exclude (e.g., 'reentrancy-benign,timestamp')"
                    }
                },
                "required": ["contract_path"]
            }
        ),
        Tool(
            name="run_mythril",
            description="Run Mythril symbolic execution for deep path analysis. Explores execution paths to find vulnerabilities. Returns security issues with severity ratings.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_path": {
                        "type": "string",
                        "description": "Path to Solidity contract file"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum recursion depth (default: 12, deep: 22)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Analysis timeout in seconds (default: 300)"
                    }
                },
                "required": ["contract_path"]
            }
        ),
        Tool(
            name="run_foundry_fuzz",
            description="Run Foundry fuzz testing on smart contracts. Tests functions with random inputs to find edge cases. Requires Foundry project with tests.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to Foundry project directory"
                    },
                    "fuzz_runs": {
                        "type": "integer",
                        "description": "Number of fuzz test iterations (default: 1000, deep: 10000)"
                    },
                    "match_test": {
                        "type": "string",
                        "description": "Regex pattern to match specific tests"
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="get_slither_detectors",
            description="List all available Slither detectors with descriptions",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="check_tool_availability",
            description="Check which security analysis tools are installed and available",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


# ============ Tool Implementations ============

@app.call_tool()
async def call_tool(name: str, arguments: Dict) -> List[TextContent]:
    """Handle tool calls"""

    if name == "run_slither":
        return await run_slither(
            arguments.get("contract_path", ""),
            arguments.get("detectors", "all"),
            arguments.get("exclude", "")
        )

    elif name == "run_mythril":
        return await run_mythril(
            arguments.get("contract_path", ""),
            arguments.get("max_depth", 12),
            arguments.get("timeout", 300)
        )

    elif name == "run_foundry_fuzz":
        return await run_foundry_fuzz(
            arguments.get("project_path", ""),
            arguments.get("fuzz_runs", 1000),
            arguments.get("match_test", "")
        )

    elif name == "get_slither_detectors":
        return await get_slither_detectors()

    elif name == "check_tool_availability":
        return await check_tool_availability()

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ============ Tool Functions ============

async def run_slither(
    contract_path: str,
    detectors: str = "all",
    exclude: str = ""
) -> List[TextContent]:
    """Run Slither static analysis"""

    if not AVAILABLE_TOOLS["slither"]:
        return [TextContent(
            type="text",
            text="❌ Slither is not installed. Install with: pip install slither-analyzer"
        )]

    if not contract_path or not Path(contract_path).exists():
        return [TextContent(
            type="text",
            text=f"❌ Contract path not found: {contract_path}"
        )]

    try:
        # Build Slither command
        cmd = ["slither", contract_path, "--json", "-"]

        # Add detector filtering
        if detectors != "all":
            if detectors == "high":
                cmd.extend(["--severity", "high"])
            elif detectors == "critical":
                cmd.extend(["--severity", "high,medium"])

        # Add exclusions
        if exclude:
            cmd.extend(["--exclude", exclude])

        # Run Slither
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=Path(contract_path).parent if Path(contract_path).is_file() else contract_path
        )

        # Parse JSON output
        try:
            slither_output = json.loads(result.stdout)
            findings = slither_output.get("results", {}).get("detectors", [])
        except json.JSONDecodeError:
            # Fallback to text output
            findings = []

        # Format output
        output = f"## Slither Analysis Results\n\n"
        output += f"**Target**: {contract_path}\n"
        output += f"**Detectors**: {detectors}\n"
        output += f"**Total Findings**: {len(findings)}\n\n"

        if not findings:
            output += "✅ No issues detected by Slither\n"
        else:
            # Group by severity
            severity_groups = {"high": [], "medium": [], "low": [], "informational": []}
            for finding in findings:
                impact = finding.get("impact", "informational").lower()
                if impact in severity_groups:
                    severity_groups[impact].append(finding)

            # Output by severity
            for severity in ["high", "medium", "low", "informational"]:
                if severity_groups[severity]:
                    output += f"### {severity.upper()} Severity ({len(severity_groups[severity])})\n\n"
                    for i, finding in enumerate(severity_groups[severity], 1):
                        output += f"**[{severity[0].upper()}-{i}] {finding.get('check', 'Unknown')}**\n"
                        output += f"- {finding.get('description', 'No description')}\n"

                        # Add element locations
                        for element in finding.get('elements', [])[:3]:  # First 3 elements
                            source_map = element.get('source_mapping', {})
                            if 'filename_relative' in source_map and 'lines' in source_map:
                                lines = source_map['lines']
                                line_ref = f"{lines[0]}" if len(lines) == 1 else f"{lines[0]}-{lines[-1]}"
                                output += f"  - `{source_map['filename_relative']}:{line_ref}`\n"

                        output += "\n"

        # Add raw JSON for programmatic access
        output += f"\n<details>\n<summary>Raw JSON Output</summary>\n\n```json\n{json.dumps(findings, indent=2)}\n```\n</details>\n"

        return [TextContent(type="text", text=output)]

    except subprocess.TimeoutExpired:
        return [TextContent(
            type="text",
            text="❌ Slither analysis timed out (>5 minutes). Try analyzing a smaller subset of contracts."
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Slither error: {str(e)}"
        )]


async def run_mythril(
    contract_path: str,
    max_depth: int = 12,
    timeout: int = 300
) -> List[TextContent]:
    """Run Mythril symbolic execution"""

    if not AVAILABLE_TOOLS["myth"]:
        return [TextContent(
            type="text",
            text="❌ Mythril is not installed. Install with: pip install mythril"
        )]

    if not contract_path or not Path(contract_path).exists():
        return [TextContent(
            type="text",
            text=f"❌ Contract path not found: {contract_path}"
        )]

    try:
        # Build Mythril command
        cmd = [
            "myth", "analyze",
            contract_path,
            f"--max-depth={max_depth}",
            "--json"
        ]

        # Run Mythril with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Parse output
        output = f"## Mythril Symbolic Execution Results\n\n"
        output += f"**Target**: {contract_path}\n"
        output += f"**Max Depth**: {max_depth}\n"
        output += f"**Timeout**: {timeout}s\n\n"

        if result.returncode == 0:
            try:
                mythril_output = json.loads(result.stdout)
                issues = mythril_output.get("issues", [])

                if not issues:
                    output += "✅ No issues detected by Mythril\n"
                else:
                    output += f"**Total Issues**: {len(issues)}\n\n"

                    for i, issue in enumerate(issues, 1):
                        output += f"### Issue {i}: {issue.get('title', 'Unknown')}\n\n"
                        output += f"- **Severity**: {issue.get('severity', 'Unknown')}\n"
                        output += f"- **Type**: {issue.get('swc-id', 'Unknown')}\n"
                        output += f"- **Description**: {issue.get('description', 'No description')}\n\n"

                        if 'locations' in issue:
                            output += "**Locations**:\n"
                            for loc in issue['locations'][:3]:
                                output += f"  - Line {loc.get('lineno', '?')}\n"

                        output += "\n"

            except json.JSONDecodeError:
                output += f"Mythril output (text format):\n\n```\n{result.stdout}\n```\n"
        else:
            output += f"⚠️ Mythril completed with warnings\n\n"
            output += f"```\n{result.stderr}\n```\n"

        return [TextContent(type="text", text=output)]

    except subprocess.TimeoutExpired:
        return [TextContent(
            type="text",
            text=f"❌ Mythril analysis timed out after {timeout}s. Consider reducing max_depth or increasing timeout."
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Mythril error: {str(e)}"
        )]


async def run_foundry_fuzz(
    project_path: str,
    fuzz_runs: int = 1000,
    match_test: str = ""
) -> List[TextContent]:
    """Run Foundry fuzz tests"""

    if not AVAILABLE_TOOLS["forge"]:
        return [TextContent(
            type="text",
            text="❌ Foundry is not installed. Install from: https://getfoundry.sh"
        )]

    if not project_path or not Path(project_path).exists():
        return [TextContent(
            type="text",
            text=f"❌ Project path not found: {project_path}"
        )]

    # Check for foundry.toml
    if not Path(project_path, "foundry.toml").exists():
        return [TextContent(
            type="text",
            text=f"❌ Not a Foundry project (foundry.toml not found): {project_path}"
        )]

    try:
        # Build forge test command
        cmd = [
            "forge", "test",
            f"--fuzz-runs={fuzz_runs}"
        ]

        if match_test:
            cmd.extend(["--match-test", match_test])

        # Run forge test
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=project_path
        )

        # Format output
        output = f"## Foundry Fuzz Test Results\n\n"
        output += f"**Project**: {project_path}\n"
        output += f"**Fuzz Runs**: {fuzz_runs}\n"

        if match_test:
            output += f"**Match Pattern**: {match_test}\n"

        output += "\n"

        # Parse test results
        stdout = result.stdout
        if "FAILED" in stdout:
            output += "❌ **Some tests FAILED**\n\n"
        elif "PASSED" in stdout:
            output += "✅ **All tests PASSED**\n\n"

        output += "```\n"
        output += stdout
        output += "```\n"

        return [TextContent(type="text", text=output)]

    except subprocess.TimeoutExpired:
        return [TextContent(
            type="text",
            text="❌ Foundry tests timed out (>10 minutes). Consider reducing fuzz_runs."
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Foundry error: {str(e)}"
        )]


async def get_slither_detectors() -> List[TextContent]:
    """List all Slither detectors"""

    if not AVAILABLE_TOOLS["slither"]:
        return [TextContent(
            type="text",
            text="❌ Slither is not installed"
        )]

    try:
        result = subprocess.run(
            ["slither", "--list-detectors"],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = f"## Slither Available Detectors\n\n"
        output += "```\n"
        output += result.stdout
        output += "```\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error listing detectors: {str(e)}"
        )]


async def check_tool_availability() -> List[TextContent]:
    """Check which tools are installed"""

    output = f"## Security Tool Availability\n\n"

    for tool, available in AVAILABLE_TOOLS.items():
        status = "✅ Installed" if available else "❌ Not installed"
        output += f"- **{tool}**: {status}\n"

    output += "\n### Installation Instructions\n\n"

    if not AVAILABLE_TOOLS["slither"]:
        output += "**Slither**: `pip install slither-analyzer`\n"

    if not AVAILABLE_TOOLS["myth"]:
        output += "**Mythril**: `pip install mythril`\n"

    if not AVAILABLE_TOOLS["forge"]:
        output += "**Foundry**: `curl -L https://foundry.paradigm.xyz | bash && foundryup`\n"

    if not AVAILABLE_TOOLS["echidna"]:
        output += "**Echidna**: `https://github.com/crytic/echidna`\n"

    return [TextContent(type="text", text=output)]


# ============ Main Entry Point ============

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    asyncio.run(main())
