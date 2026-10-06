# Changelog

## 0.2.0 — 2026-10-06

- Add XNOR, fixed-width logical shifts and rotations, set-bit counting, and
  unsigned binary/hexadecimal/decimal conversions.
- Bound operands to 4,096 bits, shifts to 1,000,000, and JSON batches to
  100 requests and 1 MiB.
- Add JSON batch input on stdin with per-request errors and explicit exit codes.
- Add `python -m bob`, `--version`, `--plain`, `--explain`, and conversion width.
- Preserve default single-operation JSON and the `bob.cli` entry point.
- Correct Python requirements and remove the unimplemented AI memory claim.
- Add independent arithmetic, invalid-input, batch and CLI regression coverage.
- Add GitHub Actions tests on Python 3.11–3.14 and clean wheel installation checks.

## 0.1.0

- Initial deterministic AND, OR, XOR, NOT, NAND and NOR operations and JSON CLI.
