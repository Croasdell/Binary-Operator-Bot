# Binary Operator Bot

Binary Operator Bot—**Bob**—is a small, deterministic Python command-line tool
for applying bitwise operations to validated binary strings.

Despite the name, the current project is not an AI system. Its purpose is to
provide a dependable calculation core that can later be used by other tools
without allowing generated code or model output to replace deterministic
arithmetic.

## Supported operations

- `AND`
- `OR`
- `XOR`
- `NOT`

Binary inputs must contain only `0` and `1`. Two-input operations require equal
lengths, and invalid input fails with a clear error.

## Quick start

Requirements: Python 3.10 or later.

Run directly from the repository:

```bash
python3 -m bob.cli AND 1010 1100
python3 -m bob.cli NOT 1010
```

Or install it in editable mode:

```bash
python3 -m pip install -e .
bob XOR 1010 1100
```

## Python API

```python
from bob.operations import apply_operation

result = apply_operation("XOR", "1010", "1100")
print(result)  # 0110
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Project structure

```text
bob/operations.py      validation and bitwise operations
bob/cli.py             command-line interface
tests/test_operations.py
pyproject.toml         package metadata and console command
```

## Scope

Bob currently operates on in-memory strings; it does not yet stream large
files, generate visualizations, learn from feedback, or integrate with external
data sources. Those capabilities should only be documented after they exist and
have tests.

An optional semantic-search layer may be explored later for documentation and
examples. It must remain separate from the calculation engine.

## Safety principles

- Never execute arbitrary generated code.
- Validate every operation and operand before calculation.
- Keep deterministic operations independently testable.
- Add explicit input-size limits before accepting untrusted large files.

## License

No licence file is currently included. Until one is added, normal copyright
restrictions apply.
