"""Strict JSON interface for local tools; no shell or generated-code execution."""

from __future__ import annotations

import json

from .operations import OperationError, apply_operation

MAX_BATCH_BYTES = 1_048_576
MAX_BATCH_ITEMS = 100
MAX_JSON_DEPTH = 8


class BatchError(ValueError):
    """Invalid batch envelope or JSON input."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BatchError('duplicate JSON object key')
        result[key] = value
    return result


def _reject_constant(value):
    raise BatchError('non-finite JSON numbers are not allowed')


def parse_batch(raw: bytes) -> list:
    if len(raw) > MAX_BATCH_BYTES:
        raise BatchError(f'batch exceeds {MAX_BATCH_BYTES} bytes')
    # Bound nesting before parsing, independently of Python's recursion limit.
    depth = 0
    in_string = False
    escaped = False
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                in_string = False
        elif byte == 34:
            in_string = True
        elif byte in (91, 123):
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise BatchError(f'JSON nesting exceeds {MAX_JSON_DEPTH} levels')
        elif byte in (93, 125):
            depth -= 1
    try:
        requests = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                              parse_constant=_reject_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise BatchError('invalid UTF-8 JSON: ' + str(exc)[:160]) from None
    if not isinstance(requests, list) or not 1 <= len(requests) <= MAX_BATCH_ITEMS:
        raise BatchError(f'batch must be an array of 1 to {MAX_BATCH_ITEMS} requests')
    return requests


def run_batch(requests: list) -> dict:
    if not isinstance(requests, list) or not 1 <= len(requests) <= MAX_BATCH_ITEMS:
        raise BatchError(f'batch must be an array of 1 to {MAX_BATCH_ITEMS} requests')
    results = []
    for index, request in enumerate(requests):
        try:
            if not isinstance(request, dict) or set(request) - {'operation', 'inputs', 'width'}:
                raise OperationError('request must be an object with operation, inputs and optional width')
            if not isinstance(request.get('operation'), str):
                raise OperationError('operation must be a string')
            inputs = request.get('inputs')
            if not isinstance(inputs, list) or not 1 <= len(inputs) <= 2 or any(not isinstance(x, str) for x in inputs):
                raise OperationError('inputs must be an array of one or two strings')
            if 'width' in request and type(request['width']) is not int:
                raise OperationError('width must be an integer')
            result = apply_operation(request['operation'], *inputs, width=request.get('width'))
            results.append({'index': index, 'ok': True, 'result': result})
        except OperationError as exc:
            results.append({'index': index, 'ok': False, 'error': str(exc)})
    return {'ok': all(row['ok'] for row in results), 'results': results}
