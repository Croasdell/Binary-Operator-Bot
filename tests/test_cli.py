import json
from pathlib import Path
import subprocess
import sys
import tomllib
import unittest

from bob import __version__

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args, module='bob'):
        return subprocess.run([sys.executable, '-m', module, *args], cwd=ROOT,
                              capture_output=True, text=True, timeout=10)

    def test_json_and_legacy_entry_point(self):
        for module in ('bob', 'bob.cli'):
            with self.subTest(module=module):
                result = self.run_cli('xor', '1010', '1100', module=module)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
                self.assertEqual(json.loads(result.stdout), {
                    'operation': 'XOR', 'inputs': ['1010', '1100'], 'result': '0110'})

    def test_plain_preserves_width(self):
        result = self.run_cli('--plain', 'AND', '0010', '0100')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '0000\n')

    def test_explanations(self):
        expected = {'AND': '1000', 'OR': '1110', 'XOR': '0110',
                    'NAND': '0111', 'NOR': '0001', 'NOT': '0101'}
        for operation, answer in expected.items():
            operands = ['1010'] if operation == 'NOT' else ['1010', '1100']
            with self.subTest(operation=operation):
                result = self.run_cli('--explain', operation, *operands)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(answer, result.stdout)
                self.assertIn(operation, result.stdout)
                self.assertNotIn('{', result.stdout)

    def test_invalid_requests(self):
        cases = [(), ('AND', '1'), ('NOT', '1', '0'), ('OR', '10', '1'),
                 ('XOR', '102', '111'), ('AND', '', '1'), ('BOGUS', '1'),
                 ('--plain', '--explain', 'NOT', '1')]
        for args in cases:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertIn('error:', result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_help_and_version(self):
        result = self.run_cli('--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('--explain', result.stdout)
        result = self.run_cli('--version')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), f'bob {__version__}')
        with (ROOT / 'pyproject.toml').open('rb') as source:
            self.assertEqual(tomllib.load(source)['project']['version'], __version__)
