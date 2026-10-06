"""Command-line entry point for Bob."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .operations import OPERATORS, OperationError, apply_operation
from .batch import BatchError, MAX_BATCH_BYTES, parse_batch, run_batch

EXPLANATIONS = {
    "AND": "AND returns 1 only where both bits are 1.",
    "OR": "OR returns 1 where at least one bit is 1.",
    "XOR": "XOR returns 1 where the two bits differ.",
    "NAND": "NAND returns 0 only where both bits are 1.",
    "NOR": "NOR returns 1 only where both bits are 0.",
    "XNOR": "XNOR returns 1 where the two bits are equal.",
    "SHL": "SHL shifts left, discards overflow and fills with zeros at the input width.",
    "SHR": "SHR shifts right, discards low bits and fills with zeros at the input width.",
    "ROL": "ROL rotates left within the input width; the count wraps modulo that width.",
    "ROR": "ROR rotates right within the input width; the count wraps modulo that width.",
    "COUNT": "COUNT returns the number of set (1) bits in decimal.",
    "BIN_TO_HEX": "Convert binary to uppercase hexadecimal, preserving leading zero nibbles.",
    "BIN_TO_DEC": "Convert unsigned binary to decimal.",
    "HEX_TO_BIN": "Convert hexadecimal to binary; default width is four bits per hex digit.",
    "HEX_TO_DEC": "Convert unsigned hexadecimal to decimal.",
    "DEC_TO_BIN": "Convert unsigned decimal to binary; an optional width pads with zeros.",
    "DEC_TO_HEX": "Convert unsigned decimal to uppercase hexadecimal.",
    "NOT": "NOT flips each bit: 0 becomes 1 and 1 becomes 0.",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a validated Bob binary operation")
    parser.add_argument("--version", action="version", version=f"bob {__version__}")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--plain", action="store_true", help="print only the resulting binary string")
    output.add_argument("--explain", action="store_true", help="show aligned operands and explain the operation")
    parser.add_argument("--batch", action="store_true", help="read a bounded JSON array from stdin")
    parser.add_argument("--width", type=int, help="output bits for conversions to binary")
    parser.add_argument("operation", nargs="?", choices=sorted(OPERATORS), type=str.upper)
    parser.add_argument("inputs", nargs="*")
    args = parser.parse_args(argv)
    if args.batch:
        if args.operation or args.inputs or args.plain or args.explain or args.width is not None:
            parser.error("--batch cannot be combined with operation, inputs or output options")
        try:
            raw = sys.stdin.buffer.read(MAX_BATCH_BYTES + 1)
            response = run_batch(parse_batch(raw))
        except (BatchError, OSError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 2
        print(json.dumps(response))
        return 0 if response['ok'] else 1
    if args.operation is None:
        parser.error("operation is required unless --batch is used")
    try:
        result = apply_operation(args.operation, *args.inputs, width=args.width)
    except OperationError as exc:
        parser.error(str(exc))
    if args.plain:
        print(result)
    elif args.explain:
        if args.operation in {"AND", "OR", "XOR", "NAND", "NOR", "XNOR", "NOT"}:
            prefix = len(args.operation) + 1
            if len(args.inputs) == 2:
                print(" " * prefix + args.inputs[0])
            print(f"{args.operation} {args.inputs[-1]}")
            print("-" * (prefix + len(result)))
            print(" " * prefix + result)
        else:
            print(f"{args.operation} {' '.join(args.inputs)} -> {result}")
        print()
        print(EXPLANATIONS[args.operation])
    else:
        print(json.dumps({"operation": args.operation, "inputs": args.inputs, "result": result}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
