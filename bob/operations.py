"""Bounded, deterministic operations on unsigned binary strings."""

from __future__ import annotations

MAX_BITS = 4096
MAX_SHIFT = 1_000_000
BINARY_OPERATORS = frozenset({'AND', 'OR', 'XOR', 'NAND', 'NOR', 'XNOR'})
SHIFT_OPERATORS = frozenset({'SHL', 'SHR', 'ROL', 'ROR'})
CONVERSIONS = frozenset({'BIN_TO_HEX', 'BIN_TO_DEC', 'HEX_TO_BIN',
                         'HEX_TO_DEC', 'DEC_TO_BIN', 'DEC_TO_HEX'})
OPERATORS = BINARY_OPERATORS | SHIFT_OPERATORS | CONVERSIONS | {'NOT', 'COUNT'}


class OperationError(ValueError):
    """Raised when Bob receives invalid input."""


def _normalise(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise OperationError('binary input must be a non-empty string')
    if len(value) > MAX_BITS:
        raise OperationError(f'binary input exceeds {MAX_BITS} bits')
    if any(bit not in '01' for bit in value):
        raise OperationError('binary input may contain only 0 and 1')
    return value


def _unsigned(value: str, base: int) -> int:
    digits = '0123456789abcdef' if base == 16 else '0123456789'
    limit = MAX_BITS // 4 if base == 16 else 1234
    if not isinstance(value, str) or not value or len(value) > limit:
        raise OperationError(f'base-{base} input must contain 1 to {limit} digits')
    if any(c not in digits for c in value.lower()):
        raise OperationError(f'invalid unsigned base-{base} input (no sign, prefix or spaces)')
    result = int(value, base)
    if result.bit_length() > MAX_BITS:
        raise OperationError(f'value exceeds {MAX_BITS} bits')
    return result


def _shift_count(value: str) -> int:
    if (not isinstance(value, str) or not value or len(value) > 7
            or any(c not in '0123456789' for c in value)):
        raise OperationError(f'shift count must be decimal digits from 0 to {MAX_SHIFT}')
    result = int(value)
    if result > MAX_SHIFT:
        raise OperationError(f'shift count exceeds {MAX_SHIFT}')
    return result


def apply_operation(operation: str, *inputs: str, width: int | None = None) -> str:
    """Return a string result; width is only supported for conversions to binary."""
    name = operation.strip().upper() if isinstance(operation, str) else ''
    if name not in OPERATORS:
        raise OperationError('unsupported operation')
    if width is not None:
        if name not in {'HEX_TO_BIN', 'DEC_TO_BIN'}:
            raise OperationError('width is only valid for HEX_TO_BIN and DEC_TO_BIN')
        if type(width) is not int or not 1 <= width <= MAX_BITS:
            raise OperationError(f'width must be an integer from 1 to {MAX_BITS}')
    expected = 2 if name in BINARY_OPERATORS | SHIFT_OPERATORS else 1
    if len(inputs) != expected:
        raise OperationError(f'{name} requires exactly {"one input" if expected == 1 else "two inputs"}')

    if name in CONVERSIONS:
        source, target = name.split('_TO_')
        value = inputs[0]
        if source == 'BIN':
            number = int(_normalise(value), 2)
        else:
            number = _unsigned(value, 16 if source == 'HEX' else 10)
        if target == 'BIN':
            bits = width if width is not None else (len(value) * 4 if source == 'HEX' else max(1, number.bit_length()))
            if number.bit_length() > bits:
                raise OperationError('value does not fit the requested width')
            return format(number, f'0{bits}b')
        if target == 'DEC':
            return str(number)
        digits = (len(value) + 3) // 4 if source == 'BIN' else 1
        return format(number, f'0{digits}X')

    left = _normalise(inputs[0])
    if name == 'COUNT':
        return str(left.count('1'))
    if name == 'NOT':
        return left.translate(str.maketrans('01', '10'))
    if name in SHIFT_OPERATORS:
        count = _shift_count(inputs[1])
        size = len(left)
        if name in {'SHL', 'SHR'}:
            count = min(count, size)
            if count == 0:
                return left
            return left[count:] + '0' * count if name == 'SHL' else '0' * count + left[:size-count]
        count %= size
        if count == 0:
            return left
        return left[count:] + left[:count] if name == 'ROL' else left[-count:] + left[:-count]

    right = _normalise(inputs[1])
    if len(left) != len(right):
        raise OperationError('binary inputs must have equal lengths')
    a, b = int(left, 2), int(right, 2)
    if name in {'AND', 'NAND'}:
        result = a & b
    elif name in {'OR', 'NOR'}:
        result = a | b
    else:
        result = a ^ b
    if name in {'NAND', 'NOR', 'XNOR'}:
        result ^= (1 << len(left)) - 1
    return format(result, f'0{len(left)}b')
