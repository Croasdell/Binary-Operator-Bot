"""Small, deterministic binary-string operation engine."""

from __future__ import annotations

OPERATORS = frozenset({"AND", "OR", "XOR", "NOT", "NAND", "NOR"})


class OperationError(ValueError):
    """Raised when Bob receives invalid input."""


def _normalise(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise OperationError("binary input must be a non-empty string")
    if any(bit not in "01" for bit in value):
        raise OperationError("binary input may contain only 0 and 1")
    return value


def apply_operation(operation: str, *inputs: str) -> str:
    """Apply a validated operation to binary strings."""
    name = operation.strip().upper() if isinstance(operation, str) else ""
    if name not in OPERATORS:
        raise OperationError(f"unsupported operation: {operation!r}")
    if name == "NOT":
        if len(inputs) != 1:
            raise OperationError("NOT requires exactly one input")
        return "".join("1" if bit == "0" else "0" for bit in _normalise(inputs[0]))
    if len(inputs) != 2:
        raise OperationError(f"{name} requires exactly two inputs")
    left, right = (_normalise(value) for value in inputs)
    if len(left) != len(right):
        raise OperationError("binary inputs must have equal lengths")
    pairs = zip(left, right)
    if name == "AND":
        return "".join("1" if a == b == "1" else "0" for a, b in pairs)
    if name == "OR":
        return "".join("1" if "1" in (a, b) else "0" for a, b in pairs)
    if name == "XOR":
        return "".join("1" if a != b else "0" for a, b in pairs)
    if name == "NAND":
        return "".join("0" if a == b == "1" else "1" for a, b in pairs)
    return "".join("0" if "1" in (a, b) else "1" for a, b in pairs)
