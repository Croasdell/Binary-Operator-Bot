"""Command-line entry point for Bob."""

from __future__ import annotations

import argparse
import json
import sys

from .operations import OPERATORS, OperationError, apply_operation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a validated Bob binary operation")
    parser.add_argument("operation", choices=sorted(OPERATORS), type=str.upper)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args(argv)
    try:
        result = apply_operation(args.operation, *args.inputs)
    except OperationError as exc:
        parser.error(str(exc))
    print(json.dumps({"operation": args.operation, "inputs": args.inputs, "result": result}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
