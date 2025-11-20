"""
Unit tests for TOON encoder

Tests the Token-Oriented Object Notation encoder for security reports.
"""

import pytest
from src.utils.toon_encoder import TOONEncoder


class TestTOONEncoder:
    """Test suite for TOON encoder"""

    def setup_method(self):
        """Setup test fixtures"""
        self.encoder = TOONEncoder()

    def test_encode_primitive(self):
        """Test encoding primitive values"""
        assert self.encoder._encode_primitive(None) == ''
        assert self.encoder._encode_primitive(True) == 'true'
        assert self.encoder._encode_primitive(False) == 'false'
        assert self.encoder._encode_primitive(42) == '42'
        assert self.encoder._encode_primitive(3.14) == '3.14'
        assert self.encoder._encode_primitive('hello') == 'hello'

    def test_escape_string(self):
        """Test string escaping"""
        assert self.encoder._escape_string('hello,world') == 'hello\\,world'
        assert self.encoder._escape_string('line1\nline2') == 'line1\\nline2'

    def test_encode_inline_array(self):
        """Test encoding primitive arrays"""
        result = self.encoder._encode_inline_array([1, 2, 3])
        assert result == '[3]: 1,2,3'

        result = self.encoder._encode_inline_array(['a', 'b', 'c'])
        assert result == '[3]: a,b,c'

        result = self.encoder._encode_inline_array([])
        assert result == '[0]: '

    def test_encode_uniform_array(self):
        """Test encoding uniform object arrays (tabular format)"""
        data = [
            {'id': 1, 'name': 'Alice', 'score': 95},
            {'id': 2, 'name': 'Bob', 'score': 87},
            {'id': 3, 'name': 'Carol', 'score': 92},
        ]

        result = self.encoder._encode_uniform_array(data, 0)

        # Check header
        assert '[3]{id,name,score}:' in result

        # Check data rows
        assert '  1,Alice,95' in result
        assert '  2,Bob,87' in result
        assert '  3,Carol,92' in result

    def test_encode_vulnerabilities(self):
        """Test encoding vulnerability arrays"""
        vulns = [
            {
                'id': 'vuln-001',
                'type': 'reentrancy',
                'severity': 'CRITICAL',
                'title': 'Reentrancy in withdraw',
                'location': {
                    'file': 'Bank.sol',
                    'line': 42,
                    'function': 'withdraw',
                },
                'detected_by': 'slither',
                'confidence': 0.95,
            },
            {
                'id': 'vuln-002',
                'type': 'oracle_manipulation',
                'severity': 'HIGH',
                'title': 'Oracle manipulation',
                'location': {
                    'file': 'Oracle.sol',
                    'line': 15,
                    'function': 'getPrice',
                },
                'detected_by': 'adversarial_agent',
                'confidence': 0.92,
            },
        ]

        result = self.encoder.encode_vulnerabilities(vulns)

        # Check array declaration
        assert 'vulnerabilities[2]' in result

        # Check fields are present
        assert 'id' in result
        assert 'severity' in result
        assert 'file' in result  # Flattened from location

        # Check data
        assert 'vuln-001' in result
        assert 'CRITICAL' in result
        assert 'Bank.sol' in result

    def test_encode_report(self):
        """Test encoding complete audit report"""
        report = {
            'project_name': 'Test Project',
            'chain': 'ethereum',
            'audit_date': '2025-01-20T10:00:00',
            'audit_mode': 'standard',
            'duration_seconds': 123.45,
            'statistics': {
                'critical': 1,
                'high': 2,
                'medium': 3,
                'low': 4,
                'info': 5,
            },
            'tools_executed': ['slither', 'mythril'],
            'vulnerabilities': [
                {
                    'id': 'vuln-001',
                    'type': 'reentrancy',
                    'severity': 'CRITICAL',
                    'title': 'Test vulnerability',
                    'location': {
                        'file': 'Test.sol',
                        'line': 1,
                        'function': 'test',
                    },
                    'detected_by': 'slither',
                    'confidence': 0.9,
                },
            ],
        }

        result = self.encoder.encode_report(report)

        # Check metadata
        assert 'project_name: Test Project' in result
        assert 'chain: ethereum' in result

        # Check statistics
        assert 'statistics{critical,high,medium,low,info}:' in result
        assert '  1,2,3,4,5' in result

        # Check tools
        assert 'tools_executed[2]: slither,mythril' in result

        # Check vulnerabilities
        assert 'vulnerabilities[1]' in result
        assert 'vuln-001' in result

    def test_empty_vulnerabilities(self):
        """Test encoding empty vulnerability array"""
        result = self.encoder.encode_vulnerabilities([])
        assert result == 'vulnerabilities[0]:'

    def test_token_savings_estimation(self):
        """Test token savings calculation"""
        json_str = '{"test": "data"}' * 100  # ~1600 chars
        toon_str = 'test: data\n' * 50  # ~550 chars

        savings = self.encoder.estimate_token_savings(json_str, toon_str)

        assert savings['json_tokens'] > 0
        assert savings['toon_tokens'] > 0
        assert savings['tokens_saved'] > 0
        assert 0 <= savings['savings_percent'] <= 100
        assert savings['json_cost'] > savings['toon_cost']

    def test_nested_objects(self):
        """Test encoding nested objects"""
        data = {
            'outer': {
                'inner': {
                    'value': 42
                }
            }
        }

        result = self.encoder.encode(data)

        # Should preserve nesting with indentation
        assert 'outer:' in result
        assert '  inner:' in result
        assert '    value: 42' in result

    def test_mixed_array(self):
        """Test encoding non-uniform arrays (should fall back to inline)"""
        data = [
            {'id': 1},
            {'id': 2, 'extra': 'field'},  # Different schema
        ]

        # Should not use tabular format due to non-uniformity
        # (This tests the fallback behavior)
        result = self.encoder.encode(data)
        assert result  # Should produce some output

    def test_format_value_with_dict(self):
        """Test formatting nested dictionaries"""
        value = {'nested': 'object'}
        result = self.encoder._format_value(value)

        # Should fall back to JSON
        assert 'nested' in result
        assert 'object' in result

    def test_format_value_with_datetime(self):
        """Test formatting datetime objects"""
        from datetime import datetime

        dt = datetime(2025, 1, 20, 10, 30, 0)
        result = self.encoder._format_value(dt)

        # Should be ISO format
        assert '2025-01-20T10:30:00' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
