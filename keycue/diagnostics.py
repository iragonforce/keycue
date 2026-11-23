"""Offline inspection of the known K2 transaction; never opens USB devices."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from .protocol import FEATURE_REPORT_SIZE, Transfer


@dataclass(frozen=True)
class TransactionSummary:
    writes: int
    reads: int
    bytes_written: int
    paced_operations: int


def describe_step(index: int, action: Transfer) -> str:
    """Describe the fixed, 25-operation legacy K2 transaction."""
    labels = {
        0: 'enable customization (0x18)',
        1: 'read after customization',
        2: 'declare 18 effect pages (0x13)',
        3: 'read after effect-area declaration',
        21: 'select custom effect mode',
        22: 'end communication (0x02)',
        23: 'read after communication end',
        24: 'activate effect (0xF0)',
    }
    if index in labels:
        return labels[index]
    if 4 <= index < 9:
        return f'effect-definition page {index - 3}/5'
    if 9 <= index < 12:
        return f'blank effect page {index - 8}/3'
    if 12 <= index < 21:
        return f'RGB data page {index - 11}/9'
    return f'unknown {action.operation} operation'


def summarize(actions: Sequence[Transfer]) -> TransactionSummary:
    operations = Counter(action.operation for action in actions)
    if set(operations) - {'read', 'write'}:
        raise ValueError(f'Unexpected operations: {set(operations) - {"read", "write"}}')
    return TransactionSummary(
        writes=operations['write'],
        reads=operations['read'],
        bytes_written=sum(FEATURE_REPORT_SIZE for action in actions if action.operation == 'write'),
        paced_operations=len(actions),
    )


def render_report(actions: Sequence[Transfer]) -> str:
    summary = summarize(actions)
    lines = [
        '=== KEYCUE OFFLINE PROTOCOL ANALYSIS ===',
        'No keyboard discovery, USB access, or HID commands.',
        f'Transaction: {summary.writes} writes, {summary.reads} reads',
        f'Feature report bytes submitted: {summary.bytes_written}',
        f'Pacing operations: {summary.paced_operations} at 1 ms requested each',
        'Storage persistence: UNKNOWN; do not repeat or automate this transaction.',
        'Steps:',
    ]
    for i, action in enumerate(actions):
        lines.append(f'  {i + 1:2d}. {action.operation:5s} {describe_step(i, action)}')
    return '\n'.join(lines)
