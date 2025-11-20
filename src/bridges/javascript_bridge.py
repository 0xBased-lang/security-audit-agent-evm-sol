"""
JavaScript Bridge

Executes Phase 1 traditional audit tools (JavaScript) from Python.
Handles subprocess management, error handling, and result parsing.
"""

import subprocess
import json
import os
import logging
import time
from typing import Dict, List, Optional, Any
from pathlib import Path


class AuditError(Exception):
    """Custom exception for audit failures"""
    pass


class JavaScriptBridge:
    """
    Bridge to execute JavaScript audit tools from Python

    Handles:
    - Subprocess management
    - Timeout handling
    - Error recovery
    - Result parsing
    - JSON communication
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize JavaScript bridge

        Args:
            project_root: Root directory of the project (where package.json is)
        """
        self.project_root = project_root or os.getcwd()
        self.logger = logging.getLogger(__name__)

        # Verify npm is available
        self._check_npm_available()

    def _check_npm_available(self):
        """Verify npm is installed"""
        try:
            result = subprocess.run(
                ['npm', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise AuditError("npm not available")

            self.logger.debug(f"npm version: {result.stdout.strip()}")

        except FileNotFoundError:
            raise AuditError(
                "npm not found. Install Node.js and npm:\n"
                "  https://nodejs.org/"
            )
        except subprocess.TimeoutExpired:
            raise AuditError("npm command timed out")

    def run_traditional_audit(
        self,
        project_path: str,
        tools: Optional[List[str]] = None,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        Run Phase 1 traditional audit tools

        Args:
            project_path: Path to the smart contract project
            tools: List of specific tools to run (None = all tools)
            timeout: Maximum execution time in seconds

        Returns:
            Dict containing audit results in standardized format

        Raises:
            AuditError: If audit fails
        """
        self.logger.info(f"Running traditional audit on {project_path}")

        # Build command
        cmd = [
            'npm', 'run', 'audit', '--',
            '--project', project_path,
            '--format', 'json'
        ]

        if tools:
            cmd.extend(['--tools', ','.join(tools)])

        self.logger.debug(f"Executing: {' '.join(cmd)}")

        try:
            start_time = time.time()

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            duration = time.time() - start_time
            self.logger.info(f"Traditional audit completed in {duration:.1f}s")

            # Parse results
            if result.returncode != 0:
                # Check if it's a tool availability issue
                if 'not found' in result.stderr.lower():
                    self.logger.warning(
                        f"Some tools not available: {result.stderr}"
                    )
                    # Try to parse partial results
                    return self._parse_partial_results(result.stdout, result.stderr)
                else:
                    raise AuditError(
                        f"Traditional audit failed (code {result.returncode}):\n"
                        f"{result.stderr}"
                    )

            # Parse JSON output
            return self._parse_audit_output(result.stdout)

        except subprocess.TimeoutExpired:
            self.logger.error(f"Traditional audit timed out after {timeout}s")
            raise AuditError(
                f"Traditional audit timed out after {timeout}s. "
                f"Try running with fewer tools or increase timeout."
            )

        except FileNotFoundError:
            raise AuditError(
                "npm audit command not found. "
                "Ensure you're in the project root directory."
            )

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse audit output: {e}")
            self.logger.debug(f"Output was: {result.stdout[:500]}")
            raise AuditError(f"Failed to parse audit output: {e}")

    def run_evm_audit(
        self,
        project_path: str,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        Run EVM-specific audit tools

        Args:
            project_path: Path to the EVM smart contract project
            timeout: Maximum execution time in seconds

        Returns:
            Dict containing EVM audit results
        """
        self.logger.info(f"Running EVM audit on {project_path}")

        cmd = [
            'npm', 'run', 'audit:evm', '--',
            '--project', project_path,
            '--format', 'json'
        ]

        return self._execute_audit_command(cmd, timeout)

    def run_solana_audit(
        self,
        project_path: str,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        Run Solana-specific audit tools

        Args:
            project_path: Path to the Solana smart contract project
            timeout: Maximum execution time in seconds

        Returns:
            Dict containing Solana audit results
        """
        self.logger.info(f"Running Solana audit on {project_path}")

        cmd = [
            'npm', 'run', 'audit:solana', '--',
            '--project', project_path,
            '--format', 'json'
        ]

        return self._execute_audit_command(cmd, timeout)

    def _execute_audit_command(
        self,
        cmd: List[str],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Execute audit command with error handling

        Args:
            cmd: Command to execute
            timeout: Timeout in seconds

        Returns:
            Parsed audit results
        """
        try:
            start_time = time.time()

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            duration = time.time() - start_time

            if result.returncode != 0:
                # Partial results handling
                if result.stdout:
                    self.logger.warning(
                        f"Audit completed with errors (code {result.returncode})"
                    )
                    return self._parse_partial_results(result.stdout, result.stderr)
                else:
                    raise AuditError(
                        f"Audit failed:\n{result.stderr}"
                    )

            return self._parse_audit_output(result.stdout)

        except subprocess.TimeoutExpired:
            raise AuditError(f"Audit timed out after {timeout}s")

        except json.JSONDecodeError as e:
            raise AuditError(f"Failed to parse audit output: {e}")

    def _parse_audit_output(self, output: str) -> Dict[str, Any]:
        """
        Parse JSON audit output

        Args:
            output: JSON output from audit tools

        Returns:
            Parsed audit results
        """
        try:
            data = json.loads(output)

            # Validate required fields
            required_fields = ['vulnerabilities', 'summary']
            for field in required_fields:
                if field not in data:
                    self.logger.warning(
                        f"Missing required field '{field}' in audit output"
                    )

            return data

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON output: {e}")
            self.logger.debug(f"Output: {output[:500]}")

            # Try to extract useful information anyway
            return {
                'vulnerabilities': [],
                'summary': {
                    'error': 'Failed to parse output',
                    'raw_output': output[:1000]
                },
                'tools_executed': [],
                'parsing_error': str(e)
            }

    def _parse_partial_results(
        self,
        stdout: str,
        stderr: str
    ) -> Dict[str, Any]:
        """
        Parse partial results when some tools fail

        Args:
            stdout: Standard output
            stderr: Standard error output

        Returns:
            Partial audit results with warnings
        """
        self.logger.warning("Parsing partial results")

        try:
            # Try to parse whatever JSON we got
            data = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            data = {}

        # Add warning about partial results
        data['warnings'] = data.get('warnings', [])
        data['warnings'].append(
            f"Partial results: {stderr[:200]}"
        )

        # Ensure required fields exist
        data.setdefault('vulnerabilities', [])
        data.setdefault('summary', {})
        data.setdefault('tools_executed', [])

        return data

    def check_tools_available(self) -> Dict[str, bool]:
        """
        Check which audit tools are available

        Returns:
            Dict mapping tool names to availability status
        """
        self.logger.info("Checking tool availability")

        cmd = ['npm', 'run', 'tools']

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse output to determine which tools are available
            # Expected format: JSON with tool statuses
            if result.stdout:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Fallback: parse text output
                    return self._parse_tool_list_text(result.stdout)

            return {}

        except subprocess.TimeoutExpired:
            self.logger.warning("Tool check timed out")
            return {}

        except Exception as e:
            self.logger.error(f"Failed to check tools: {e}")
            return {}

    def _parse_tool_list_text(self, text: str) -> Dict[str, bool]:
        """
        Parse text-based tool list output

        Args:
            text: Text output from tools command

        Returns:
            Dict mapping tool names to availability
        """
        tools = {}

        for line in text.split('\n'):
            line = line.strip()
            if '✓' in line or 'available' in line.lower():
                # Extract tool name
                tool_name = line.split()[0].replace('✓', '').strip()
                tools[tool_name] = True
            elif '✗' in line or 'not available' in line.lower():
                tool_name = line.split()[0].replace('✗', '').strip()
                tools[tool_name] = False

        return tools
