"""
TOON Format Encoder

Encodes security audit reports to Token-Oriented Object Notation (TOON) format.

Benefits:
- 30-60% token reduction vs JSON
- Better LLM parsing accuracy (73.9% vs 69.7%)
- Human-readable tabular format
- Perfect for vulnerability arrays

Reference: https://github.com/toon-format/toon
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime


class TOONEncoder:
    """
    TOON format encoder optimized for blockchain security reports

    TOON combines YAML-like indentation with CSV-like tabular arrays:
    - Objects: YAML-style (key: value)
    - Arrays: Tabular with schema declaration

    Example:
        vulnerabilities[50]{id,severity,title}:
          vuln-001,CRITICAL,Reentrancy in withdraw
          vuln-002,HIGH,Oracle manipulation
    """

    def __init__(self, indent: str = '  '):
        """
        Initialize TOON encoder

        Args:
            indent: Indentation string (default: 2 spaces)
        """
        self.indent = indent

    def encode(self, data: Any, depth: int = 0) -> str:
        """
        Encode Python data to TOON format

        Args:
            data: Data to encode (dict, list, or primitive)
            depth: Current indentation depth

        Returns:
            TOON-encoded string
        """
        if isinstance(data, dict):
            return self._encode_object(data, depth)
        elif isinstance(data, list):
            return self._encode_array(data, depth)
        else:
            return self._encode_primitive(data)

    def _encode_object(self, obj: Dict[str, Any], depth: int) -> str:
        """Encode object (YAML-style)"""
        lines = []
        prefix = self.indent * depth

        for key, value in obj.items():
            if isinstance(value, dict):
                # Nested object
                lines.append(f"{prefix}{key}:")
                lines.append(self._encode_object(value, depth + 1))
            elif isinstance(value, list):
                # Array
                lines.append(f"{prefix}{key}{self._encode_array(value, depth)}")
            else:
                # Primitive
                lines.append(f"{prefix}{key}: {self._encode_primitive(value)}")

        return '\n'.join(lines)

    def _encode_array(self, arr: List[Any], depth: int = 0) -> str:
        """
        Encode array (tabular if uniform objects)

        For uniform arrays of objects, uses tabular format:
            [N]{field1,field2,...}:
              value1,value2,...
              value1,value2,...

        For primitive arrays or non-uniform arrays, uses inline format:
            [N]: item1,item2,item3
        """
        if not arr:
            return "[0]:"

        # Check if array contains uniform objects
        if all(isinstance(item, dict) for item in arr):
            # Check if all objects have same keys
            first_keys = set(arr[0].keys())
            if all(set(item.keys()) == first_keys for item in arr):
                return self._encode_uniform_array(arr, depth)

        # Fall back to inline format for primitives or non-uniform arrays
        return self._encode_inline_array(arr)

    def _encode_uniform_array(self, arr: List[Dict[str, Any]], depth: int) -> str:
        """
        Encode uniform array of objects in tabular format

        Example:
            [3]{id,name,score}:
              1,Alice,95
              2,Bob,87
              3,Carol,92
        """
        if not arr:
            return "[0]:"

        # Extract schema from first object
        fields = list(arr[0].keys())
        count = len(arr)

        # Build header: [N]{field1,field2,...}:
        header = f"[{count}]{{{','.join(fields)}}}:"

        # Build rows
        rows = []
        prefix = self.indent * (depth + 1)

        for item in arr:
            values = [self._format_value(item.get(field)) for field in fields]
            rows.append(prefix + ','.join(values))

        return header + '\n' + '\n'.join(rows)

    def _encode_inline_array(self, arr: List[Any]) -> str:
        """
        Encode array in inline format

        Example:
            [3]: apple,banana,cherry
        """
        count = len(arr)
        values = ','.join(self._format_value(v) for v in arr)
        return f"[{count}]: {values}"

    def _encode_primitive(self, value: Any) -> str:
        """Encode primitive value"""
        return self._format_value(value)

    def _format_value(self, value: Any) -> str:
        """
        Format value for TOON output

        Handles:
        - None → empty string
        - bool → true/false
        - numbers → string representation
        - strings → escaped (commas, newlines)
        - datetime → ISO format
        - nested objects → JSON fallback
        """
        if value is None:
            return ''
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Escape special characters
            return self._escape_string(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (dict, list)):
            # For nested structures, fall back to compact JSON
            return json.dumps(value, separators=(',', ':'))
        else:
            return str(value)

    def _escape_string(self, s: str) -> str:
        """
        Escape string for TOON format

        Commas are field separators, so must be escaped
        """
        # Escape commas
        s = s.replace(',', '\\,')

        # Escape newlines
        s = s.replace('\n', '\\n')

        # Escape backslashes
        s = s.replace('\\', '\\\\')

        return s

    def encode_vulnerabilities(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> str:
        """
        Encode vulnerability array to TOON format

        Optimized for UnifiedVulnerability schema.

        Example output:
            vulnerabilities[50]{id,type,severity,title,file,line,...}:
              vuln-001,reentrancy,CRITICAL,Reentrancy in withdraw,Bank.sol,42,...
              vuln-002,oracle_manipulation,HIGH,Oracle price manipulation,Oracle.sol,15,...
        """
        if not vulnerabilities:
            return "vulnerabilities[0]:"

        # Flatten nested location objects for better TOON representation
        flattened = []
        for vuln in vulnerabilities:
            flat_vuln = dict(vuln)

            # Flatten location if present
            if 'location' in flat_vuln and isinstance(flat_vuln['location'], dict):
                loc = flat_vuln.pop('location')
                flat_vuln['file'] = loc.get('file', '')
                flat_vuln['line'] = loc.get('line', '')
                flat_vuln['function'] = loc.get('function', '')

            flattened.append(flat_vuln)

        return "vulnerabilities" + self._encode_uniform_array(flattened, 0)

    def encode_report(self, report: Dict[str, Any]) -> str:
        """
        Encode complete audit report to TOON format

        Structure:
        - Metadata (YAML-style)
        - Statistics (tabular)
        - Vulnerabilities (tabular)

        Returns compact, human-readable report optimized for LLM input.
        """
        toon_parts = []

        # Metadata (YAML-style)
        metadata_fields = [
            'project_name',
            'project_path',
            'chain',
            'audit_date',
            'audit_mode',
            'duration_seconds',
        ]

        for field in metadata_fields:
            if field in report:
                value = self._encode_primitive(report[field])
                toon_parts.append(f"{field}: {value}")

        toon_parts.append('')  # Blank line

        # Statistics (inline object for compactness)
        if 'statistics' in report:
            stats = report['statistics']
            toon_parts.append("statistics{critical,high,medium,low,info}:")
            toon_parts.append(
                f"  {stats['critical']},{stats['high']},{stats['medium']},"
                f"{stats['low']},{stats['info']}"
            )
            toon_parts.append('')

        # Tools executed (inline array)
        if 'tools_executed' in report and report['tools_executed']:
            tools = report['tools_executed']
            toon_parts.append(f"tools_executed[{len(tools)}]: {','.join(tools)}")
            toon_parts.append('')

        # Vulnerabilities (tabular - the main content)
        if 'vulnerabilities' in report:
            toon_parts.append(self.encode_vulnerabilities(report['vulnerabilities']))

        # Synthesis (if present)
        if 'synthesis' in report and report['synthesis']:
            toon_parts.append('')
            toon_parts.append("synthesis:")
            # Indent synthesis text
            synthesis_lines = report['synthesis'].split('\n')
            for line in synthesis_lines:
                toon_parts.append(f"  {line}")

        return '\n'.join(toon_parts)

    def estimate_token_savings(
        self,
        json_str: str,
        toon_str: str
    ) -> Dict[str, Any]:
        """
        Estimate token savings from using TOON vs JSON

        Uses simple heuristic: ~4 chars per token (GPT-3 tokenizer approximation)

        Args:
            json_str: JSON-encoded report
            toon_str: TOON-encoded report

        Returns:
            Dict with token counts and savings percentage
        """
        # Simple token estimation (chars / 4)
        json_tokens = len(json_str) / 4
        toon_tokens = len(toon_str) / 4

        savings_tokens = json_tokens - toon_tokens
        savings_percent = (savings_tokens / json_tokens) * 100 if json_tokens > 0 else 0

        # Estimate cost (Claude Sonnet pricing: $3/million input tokens)
        cost_per_token = 3 / 1_000_000
        json_cost = json_tokens * cost_per_token
        toon_cost = toon_tokens * cost_per_token
        cost_savings = json_cost - toon_cost

        return {
            'json_tokens': int(json_tokens),
            'toon_tokens': int(toon_tokens),
            'tokens_saved': int(savings_tokens),
            'savings_percent': round(savings_percent, 1),
            'json_cost': round(json_cost, 6),
            'toon_cost': round(toon_cost, 6),
            'cost_savings': round(cost_savings, 6),
        }


def demo_encoding():
    """
    Demonstration of TOON encoding for security reports

    Shows token savings and improved readability.
    """
    # Sample vulnerability data
    vulnerabilities = [
        {
            'id': 'vuln-001',
            'type': 'reentrancy',
            'severity': 'CRITICAL',
            'title': 'Reentrancy in withdraw function',
            'file': 'Bank.sol',
            'line': 42,
            'function': 'withdraw',
            'detected_by': 'slither',
            'confidence': 0.95,
            'feasibility_score': 88,
            'potential_loss_usd': 5000000,
        },
        {
            'id': 'vuln-002',
            'type': 'oracle_manipulation',
            'severity': 'HIGH',
            'title': 'Oracle manipulation via flash loan',
            'file': 'Oracle.sol',
            'line': 15,
            'function': 'getPrice',
            'detected_by': 'adversarial_agent',
            'confidence': 0.92,
            'feasibility_score': 75,
            'potential_loss_usd': 2500000,
        },
        {
            'id': 'vuln-003',
            'type': 'unchecked_call',
            'severity': 'HIGH',
            'title': 'Unchecked external call return value',
            'file': 'Vault.sol',
            'line': 78,
            'function': 'transfer',
            'detected_by': 'mythril',
            'confidence': 0.88,
            'feasibility_score': 65,
            'potential_loss_usd': 1000000,
        },
    ]

    # Sample report
    report = {
        'project_name': 'DeFi Protocol',
        'chain': 'ethereum',
        'audit_date': '2025-01-20T22:00:00',
        'audit_mode': 'standard',
        'duration_seconds': 1234.56,
        'statistics': {
            'critical': 1,
            'high': 2,
            'medium': 5,
            'low': 3,
            'info': 1,
        },
        'tools_executed': ['slither', 'mythril', 'adversarial_agent'],
        'vulnerabilities': vulnerabilities,
    }

    # Encode to TOON
    encoder = TOONEncoder()
    toon_output = encoder.encode_report(report)

    # Encode to JSON for comparison
    json_output = json.dumps(report, indent=2)

    # Calculate savings
    savings = encoder.estimate_token_savings(json_output, toon_output)

    # Print results
    print("=" * 70)
    print("TOON ENCODING DEMONSTRATION")
    print("=" * 70)
    print()
    print("JSON OUTPUT:")
    print("-" * 70)
    print(json_output)
    print()
    print("=" * 70)
    print("TOON OUTPUT:")
    print("-" * 70)
    print(toon_output)
    print()
    print("=" * 70)
    print("TOKEN SAVINGS:")
    print("-" * 70)
    print(f"JSON tokens: {savings['json_tokens']}")
    print(f"TOON tokens: {savings['toon_tokens']}")
    print(f"Tokens saved: {savings['tokens_saved']}")
    print(f"Savings: {savings['savings_percent']}%")
    print()
    print(f"JSON cost: ${savings['json_cost']}")
    print(f"TOON cost: ${savings['toon_cost']}")
    print(f"Cost savings: ${savings['cost_savings']} per audit")
    print("=" * 70)


if __name__ == '__main__':
    demo_encoding()
