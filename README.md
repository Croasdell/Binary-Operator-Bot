# Binary Operator Bot

**Bob** is a deterministic Python calculator for unsigned binary strings.
It works as a command-line tool or an importable library. Its bounded JSON
interface lets local tools such as SIMBA request exact calculations without
executing generated code. Bob does not contain an AI model or memory system.

Requires **Python 3.11 or later**. No runtime dependencies.

## Quick start

```bash
python3 -m pip install .
bob XOR 1010 1100
# {"operation": "XOR", "inputs": ["1010", "1100"], "result": "0110"}

bob --plain XNOR 1010 1100
# 1001

bob --explain XOR 1010 1100
bob --plain SHL 1010 1
# 0100

bob --plain --width 8 DEC_TO_BIN 5
# 00000101
```

From the checkout, use `python3 -m bob` without installing. The original
`python3 -m bob.cli` entry point also works. `--version` prints the release
version; `--help` lists options. Operation names are case-insensitive.

JSON is the default single-operation output and retains the existing
`operation`, `inputs`, and `result` fields. `--plain` prints only the result;
`--explain` adds an explanation. Those two flags are mutually exclusive.
All results are strings, including decimal results and set-bit counts.

## Operations

| Operation | Inputs | Behaviour |
|---|---|---|
| AND, OR, XOR | Two binary strings | Bitwise operation; equal widths required |
| NAND, NOR, XNOR | Two binary strings | Inverse of AND, OR, XOR at the input width |
| NOT | One binary string | Flip every bit |
| COUNT | One binary string | Count set bits; return a decimal string |
| SHL, SHR | Binary string, decimal count | Logical shift, zero fill, discard overflow |
| ROL, ROR | Binary string, decimal count | Rotate within input width |
| BIN_TO_HEX | Binary string | Uppercase hex; one digit per four input bits, rounded up |
| BIN_TO_DEC | Binary string | Unsigned decimal |
| HEX_TO_BIN | Hex string | Four output bits per input digit by default |
| HEX_TO_DEC | Hex string | Unsigned decimal |
| DEC_TO_BIN | Decimal string | Minimum binary width by default; zero is `0` |
| DEC_TO_HEX | Decimal string | Minimum uppercase hex width |

Bitwise operations, shifts and rotations preserve the binary input width and
leading zeros. A shift by the width or more returns all zeros. Rotations reduce
the count modulo the width. Signed arithmetic and arithmetic right shift are
not supported.

`--width` applies **only** to HEX_TO_BIN and DEC_TO_BIN. It pads to the requested
width and rejects values that cannot fit; it never silently truncates.
Conversions to decimal drop leading zeros. Hex inputs are case-insensitive.
Inputs may not contain signs, `0b`/`0x` prefixes, spaces, separators or fractions.

## Bounded batch interface

Send one JSON array through stdin, then close stdin (EOF):

```bash
printf '%s' '[{"operation":"XOR","inputs":["1010","1100"]},{"operation":"DEC_TO_BIN","inputs":["5"],"width":8}]' | bob --batch
```

Response:

```json
{"ok": true, "results": [{"index": 0, "ok": true, "result": "0110"}, {"index": 1, "ok": true, "result": "00000101"}]}
```

Each request requires `operation` (string) and `inputs` (array of operand
strings). `width` is an optional integer for conversions to binary. Unknown
fields are rejected. Results correspond to zero-based request indices.
A bad request returns `{"index": 1, "ok": false, "error": "..."}` while other
requests still run. An invalid envelope returns `{"ok": false, "error": "..."}`.
Duplicate JSON keys, non-finite numbers and invalid UTF-8 are rejected.
Error text is for humans; integrations should use `ok`, `index`, and exit codes.

| Limit | Value |
|---|---|
| Binary operand / integer value | 4,096 bits |
| Hex input | 1,024 digits |
| Decimal input | 1,234 digits, also subject to the 4,096-bit value limit |
| Shift / rotation count | 0–1,000,000; at most seven decimal digits |
| Explicit binary output width | 1–4,096 |
| Batch requests | 1–100 |
| Batch input | 1 MiB (1,048,576 bytes), including whitespace |
| JSON nesting | At most eight levels |

`--batch` cannot be combined with positional operations, `--width`, `--plain`
or `--explain`. Batch output goes to stdout; argparse usage errors go to stderr.

Exit codes: **0** success; **1** a valid batch contains failed requests;
**2** invalid CLI arguments, unreadable stdin, or malformed/oversized batch.
Invalid single-operation requests produce no stdout and an error on stderr.

### Calling Bob from SIMBA or another Python tool

```python
import json
import subprocess
import sys

request = [{"operation": "XOR", "inputs": ["1010", "1100"]}]
completed = subprocess.run(
    [sys.executable, "-m", "bob", "--batch"],
    input=json.dumps(request), text=True, capture_output=True, timeout=10,
)
response = json.loads(completed.stdout)
if completed.returncode != 0 or not response["ok"]:
    raise RuntimeError(response)
print(response["results"][0]["result"])
```

Install Bob into the caller's Python environment first. Use argument lists,
not a shell command built from model output. This interface is ready for an
integration; it has not been installed or wired into the live SIMBA server.

## Python API

```python
from bob import OperationError, apply_operation

assert apply_operation("XOR", "1010", "1100") == "0110"
assert apply_operation("DEC_TO_BIN", "5", width=8) == "00000101"
```

Invalid operations, values, widths and operand counts raise `OperationError`.
`bob.batch.parse_batch` applies byte, nesting and envelope limits;
`bob.batch.run_batch` validates requests and calculates results. Call both
when accepting external JSON bytes.

## Development and release

```bash
python3 -m unittest discover -s tests -v
python3 -m pip install build twine
python3 -m build
python3 -m twine check dist/*
```

Tests include exhaustive small-width checks against independent integer
arithmetic, conversion round trips, limits, invalid inputs, and CLI contracts.
GitHub Actions runs tests on Python 3.11–3.14 and installs the built wheel into
a clean environment outside the checkout. See [CHANGELOG.md](CHANGELOG.md).

The calculation core is `bob/operations.py`, batch validation is `bob/batch.py`,
and the CLI is `bob/cli.py`. There are no file-processing, learning, network or
arbitrary-code execution features.

## Licence

No licence has been selected yet. All rights remain reserved pending the
owner's licence decision.
