import unittest

from bob.operations import OperationError, apply_operation


class OperationTests(unittest.TestCase):
    def test_basic_operations(self):
        self.assertEqual(apply_operation("AND", "1010", "1100"), "1000")
        self.assertEqual(apply_operation("OR", "1010", "1100"), "1110")
        self.assertEqual(apply_operation("XOR", "1010", "1100"), "0110")
        self.assertEqual(apply_operation("NAND", "1010", "1100"), "0111")
        self.assertEqual(apply_operation("NOR", "1010", "1100"), "0001")

    def test_not(self):
        self.assertEqual(apply_operation("NOT", "1010"), "0101")

    def test_invalid_input_and_lengths(self):
        with self.assertRaises(OperationError):
            apply_operation("AND", "1020", "1100")
        with self.assertRaises(OperationError):
            apply_operation("AND", "1", "10")
        with self.assertRaises(OperationError):
            apply_operation("NOT", "1", "0")


class OperationContractTests(unittest.TestCase):
    def test_exhaustive_integer_reference(self):
        # Independent integer oracle exercises every operand pair at widths 1–6.
        for width in range(1, 7):
            mask = (1 << width) - 1
            for a in range(1 << width):
                left = format(a, f'0{width}b')
                self.assertEqual(apply_operation('NOT', left),
                                 format(mask ^ a, f'0{width}b'))
                for b in range(1 << width):
                    right = format(b, f'0{width}b')
                    expected = {'AND': a & b, 'OR': a | b, 'XOR': a ^ b,
                                'NAND': mask ^ (a & b), 'NOR': mask ^ (a | b)}
                    for op, answer in expected.items():
                        self.assertEqual(apply_operation(op, left, right),
                                         format(answer, f'0{width}b'), (op, left, right))

    def test_operation_normalisation(self):
        self.assertEqual(apply_operation(' xor ', '001', '100'), '101')

    def test_invalid_types_and_characters(self):
        for value in ('', ' ', '01\n', '0b01', '１２', '10x', None, 10, b'01'):
            for op, operands in [('NOT', [value]), ('AND', [value, '01']),
                                 ('OR', ['01', value])]:
                with self.subTest(op=op, value=value):
                    with self.assertRaises(OperationError):
                        apply_operation(op, *operands)

    def test_unknown_operations(self):
        for op in ('', 'ADD', None, 1):
            with self.subTest(op=op):
                with self.assertRaises(OperationError):
                    apply_operation(op, '1', '0')

    def test_operand_counts(self):
        for op in ('AND', 'OR', 'XOR', 'NAND', 'NOR', 'NOT'):
            expected = 1 if op == 'NOT' else 2
            for count in range(4):
                if count != expected:
                    with self.subTest(op=op, count=count):
                        with self.assertRaises(OperationError):
                            apply_operation(op, *(['1'] * count))

    def test_mismatched_widths(self):
        for op in ('AND', 'OR', 'XOR', 'NAND', 'NOR'):
            with self.subTest(op=op):
                with self.assertRaises(OperationError):
                    apply_operation(op, '01', '1')
