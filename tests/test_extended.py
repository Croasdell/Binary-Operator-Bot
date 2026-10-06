import json
import subprocess
import sys
import unittest

from bob import OperationError, apply_operation
from bob.batch import BatchError, MAX_BATCH_BYTES, parse_batch, run_batch
from bob.operations import MAX_BITS, MAX_SHIFT


class ExtendedTests(unittest.TestCase):
    def test_xnor_shifts_rotations_integer_oracle(self):
        for width in range(1, 7):
            mask = (1 << width) - 1
            for value in range(1 << width):
                bits = format(value, f'0{width}b')
                self.assertEqual(apply_operation('COUNT', bits), str(value.bit_count()))
                for other in range(1 << width):
                    self.assertEqual(apply_operation('XNOR', bits, format(other, f'0{width}b')),
                                     format(mask ^ (value ^ other), f'0{width}b'))
                for count in range(2 * width + 1):
                    k = count % width
                    expected = {'SHL': (value << count) & mask, 'SHR': value >> count,
                                'ROL': ((value << k) | (value >> (width-k))) & mask,
                                'ROR': ((value >> k) | (value << (width-k))) & mask}
                    for op, result in expected.items():
                        self.assertEqual(apply_operation(op, bits, str(count)),
                                         format(result, f'0{width}b'), (op, bits, count))

    def test_conversion_reference_and_round_trip(self):
        for value in range(1024):
            binary, hex_value, decimal = format(value, '010b'), format(value, 'X'), str(value)
            self.assertEqual(apply_operation('BIN_TO_HEX', binary), format(value, '03X'))
            self.assertEqual(apply_operation('BIN_TO_DEC', binary), decimal)
            self.assertEqual(apply_operation('DEC_TO_HEX', decimal), hex_value)
            self.assertEqual(apply_operation('HEX_TO_DEC', hex_value), decimal)
            self.assertEqual(apply_operation('DEC_TO_BIN', decimal, width=10), binary)
            self.assertEqual(apply_operation('HEX_TO_BIN', hex_value, width=10), binary)
        self.assertEqual(apply_operation('HEX_TO_BIN', '00a'), '000000001010')
        self.assertEqual(apply_operation('DEC_TO_BIN', '0'), '0')
        self.assertEqual(apply_operation('DEC_TO_BIN', '00005'), '101')

    def test_boundaries(self):
        bits = '1' * MAX_BITS
        self.assertEqual(apply_operation('NOT', bits), '0' * MAX_BITS)
        decimal = str((1 << MAX_BITS) - 1)
        self.assertEqual(apply_operation('BIN_TO_DEC', bits), decimal)
        self.assertEqual(apply_operation('DEC_TO_BIN', decimal), bits)
        self.assertEqual(apply_operation('HEX_TO_BIN', 'F' * (MAX_BITS // 4)), bits)
        for op in ('SHL', 'SHR'):
            self.assertEqual(apply_operation(op, '101', str(MAX_SHIFT)), '000')
        self.assertEqual(apply_operation('ROL', '101', str(MAX_SHIFT)), '011')
        self.assertEqual(apply_operation('DEC_TO_BIN', '0', width=MAX_BITS), '0' * MAX_BITS)

    def test_invalid_values(self):
        cases = [('NOT', ['1' * (MAX_BITS+1)], {}),
                 ('DEC_TO_BIN', [str(1 << MAX_BITS)], {}),
                 ('HEX_TO_BIN', ['F' * (MAX_BITS // 4+1)], {}),
                 ('DEC_TO_BIN', ['8'], {'width': 3}),
                 ('HEX_TO_BIN', ['F'], {'width': 3}),
                 ('AND', ['1', '1'], {'width': 1})]
        for width in (0, -1, MAX_BITS+1, True, 1.5, '8'):
            cases.append(('DEC_TO_BIN', ['1'], {'width': width}))
        for value in ('-1', '+1', '0xA', 'a b', '', '１２', None):
            cases.append(('HEX_TO_BIN', [value], {}))
        for value in ('-1', '+1', '1.5', '1e3', '', '１２', None):
            cases.append(('DEC_TO_BIN', [value], {}))
        for value in ('-1', '1.5', str(MAX_SHIFT+1), '0'*8, True):
            cases.append(('SHL', ['10', value], {}))
        for op, operands, kwargs in cases:
            with self.subTest(op=op, operands=str(operands)[:50], kwargs=kwargs):
                with self.assertRaises(OperationError):
                    apply_operation(op, *operands, **kwargs)


class BatchTests(unittest.TestCase):
    def test_mixed_batch(self):
        requests = [{'operation': 'xor', 'inputs': ['1010', '1100']},
                    {'operation': 'NOT', 'inputs': ['2']},
                    {'operation': 'DEC_TO_BIN', 'inputs': ['5'], 'width': 8}]
        result = run_batch(parse_batch(json.dumps(requests).encode()))
        self.assertFalse(result['ok'])
        self.assertEqual(result['results'][0], {'index': 0, 'ok': True, 'result': '0110'})
        self.assertFalse(result['results'][1]['ok'])
        self.assertEqual(result['results'][2]['result'], '00000101')

    def test_reject_envelopes_and_json(self):
        for raw in (b'{}', b'[]', b'null', b'bad', b'\xff', b'[NaN]',
                    b'[{"operation":"NOT","operation":"OR"}]',
                    b'[' * 2000 + b']' * 2000,
                    json.dumps([{}] * 101).encode(), b' ' * (MAX_BATCH_BYTES + 1)):
            with self.subTest(raw=raw[:40]):
                with self.assertRaises(BatchError):
                    parse_batch(raw)
        # Whitespace counts toward the byte cap, but exactly the cap is accepted.
        self.assertEqual(parse_batch(b'[{}]' + b' ' * (MAX_BATCH_BYTES - 4)), [{}])
        self.assertEqual(len(run_batch([{'operation': 'NOT', 'inputs': ['0']}] * 100)['results']), 100)

    def test_strict_request_schema(self):
        requests = [None, [], {}, {'operation': 1, 'inputs': ['0']},
                    {'operation': 'NOT', 'inputs': '0'},
                    {'operation': 'NOT', 'inputs': [0]},
                    {'operation': 'NOT', 'inputs': ['0'], 'command': 'anything'},
                    {'operation': 'DEC_TO_BIN', 'inputs': ['0'], 'width': None},
                    {'operation': 'DEC_TO_BIN', 'inputs': ['0'], 'width': True}]
        result = run_batch(requests)
        self.assertTrue(all(not row['ok'] for row in result['results']))

    def test_cli_batch_exit_contract(self):
        for raw, code in [('[{"operation":"NOT","inputs":["0"]}]', 0),
                          ('[{"operation":"NOT","inputs":["2"]}]', 1),
                          ('not json', 2)]:
            result = subprocess.run([sys.executable, '-m', 'bob', '--batch'],
                                    input=raw, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, code, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertEqual(json.loads(result.stdout)['ok'], code == 0)

    def test_cli_batch_rejects_conflicting_flags(self):
        for args in (['--plain'], ['--explain'], ['--width', '8'], ['NOT', '0']):
            result = subprocess.run([sys.executable, '-m', 'bob', '--batch', *args],
                                    input='[]', capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')

    def test_cli_oversized_batch(self):
        result = subprocess.run([sys.executable, '-m', 'bob', '--batch'],
                                input=b' ' * (MAX_BATCH_BYTES + 1), capture_output=True,
                                timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stdout)['ok'])
        self.assertIn('exceeds', json.loads(result.stdout)['error'])

    def test_json_brackets_inside_strings(self):
        request = [{'operation': 'NOT', 'inputs': ['[' * 20 + '\\"' + ']' * 20]}]
        self.assertEqual(parse_batch(json.dumps(request).encode()), request)
        self.assertFalse(run_batch(request)['ok'])

    def test_cli_conversion_width(self):
        result = subprocess.run([sys.executable, '-m', 'bob', '--plain', '--width', '8',
                                 'DEC_TO_BIN', '5'], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '00000101\n')
