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
