"""Proven K2 V2 custom RGB feature-report transaction.

Derived from the OpenRGB and legacy-K2 Artemis controllers and verified
against a manually successful HID transaction. It issues an effect-area
write: persistence is unknown. DO NOT use in a real-time animation loop.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from .keymap import LED_SEQUENCE_POSITIONS, normalize_key, packet_position

FEATURE_DATA_SIZE = 64
COLOUR_BUFFER_SIZE = 576
FEATURE_REPORT_SIZE = 65  # 1 report ID + 64 data bytes

@dataclass(frozen=True)
class Transfer:
    operation: str  # 'write' or 'read'
    data: bytes = b''


def _command(operation: int, count: int = 0) -> bytes:
    report = bytearray(FEATURE_DATA_SIZE)
    report[0:2] = (0x04, operation)
    report[8] = count
    return bytes(report)


def _effect_pages() -> list[bytes]:
    # Exact page layout of the physical V/T/F proof-of-concept.
    values = list(range(1,20)) + [0x80]
    pages = []
    for block in range(5):
        page = bytearray(FEATURE_DATA_SIZE)
        for slot in range(4):
            mode = values[block * 4 + slot]
            effect = bytearray(16)
            effect[0] = mode
            if mode not in (2,6,8,0x80):
                effect[1:4] = b'\xff\xff\xff'
            effect[8] = int(mode in (6,8))
            effect[9] = 15
            effect[14:16] = b'\xaa\x55'
            page[slot*16:(slot+1)*16] = effect
        pages.append(bytes(page))
    return pages


def colour_buffer(key_colours: Mapping[str, tuple[int,int,int]]) -> bytes:
    buf = bytearray(COLOUR_BUFFER_SIZE)
    for pos in LED_SEQUENCE_POSITIONS:
        buf[pos*4] = 0x80
    used = set()
    for key, rgb in key_colours.items():
        canonical = normalize_key(key)
        if canonical in used:
            raise ValueError(f'Duplicate key {canonical}')
        used.add(canonical)
        if len(rgb) != 3 or any(type(x) is not int or not 0 <= x <= 255 for x in rgb):
            raise ValueError(f'Invalid RGB value for {canonical}: {rgb!r}')
        offset = packet_position(canonical)*4
        buf[offset+1:offset+4] = bytes(rgb)
    return bytes(buf)


def build_transaction(key_colours: Mapping[str, tuple[int,int,int]]) -> tuple[Transfer,...]:
    colours = colour_buffer(key_colours)
    actions = [
        Transfer('write', _command(0x18)),  # enable customization
        Transfer('read'),
        Transfer('write', _command(0x13, 0x12)), # effect pages
        Transfer('read'),
    ]
    actions.extend(Transfer('write', p) for p in _effect_pages())
    actions.extend(Transfer('write', bytes(64)) for _ in range(3))
    actions.extend(Transfer('write', colours[i*64:(i+1)*64]) for i in range(9))
    selected = bytearray(64)
    selected[0] = 0x80
    selected[9] = 15
    selected[14:16] = b'\xaa\x55'
    actions.extend((
        Transfer('write', bytes(selected)),
        Transfer('write', _command(0x02)),
        Transfer('read'),
        Transfer('write', _command(0xF0)),
    ))
    assert sum(a.operation == 'write' for a in actions) == 22
    assert sum(a.operation == 'read' for a in actions) == 3
    return tuple(actions)
