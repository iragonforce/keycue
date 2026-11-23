"""CLI for one-shot Keychron K2 RGB pattern tests."""
from __future__ import annotations
import argparse
import sys
from collections.abc import Mapping
from .device import choose_device, discover, execute
from .keymap import KEY_INDICES, normalize_key, packet_position
from .protocol import build_transaction

PALETTE: dict[str, tuple[int, int, int]] = {
    'white':(255,255,255), 'black':(0,0,0),
    'red':(255,0,0), 'green':(0,255,0), 'blue':(0,0,255),
    'cyan':(0,255,255), 'magenta':(255,0,255),
    'yellow':(255,255,0), 'orange':(255,128,0),
}


def parse_rgb(value: str) -> tuple[int, int, int]:
    s = value.strip().lower()
    if s in PALETTE:
        return PALETTE[s]
    if s.startswith('#') and len(s) == 7:
        try:
            return tuple(bytes.fromhex(s[1:]))  # type: ignore[return-value]
        except ValueError:
            pass
    raise ValueError(f'Invalid colour {value!r}: use #RRGGBB or {", ".join(sorted(PALETTE))}')


def _split_keys(text: str) -> list[str]:
    parts = text.split(',')
    if any(not p.strip() for p in parts):
        raise ValueError('Key list contains an empty item')
    return [normalize_key(p) for p in parts]


def build_key_colours(keys: str | None, color: str | None, paints: list[str]) -> dict[str, tuple[int,int,int]]:
    result: dict[str, tuple[int,int,int]] = {}
    def add(names: list[str], rgb: tuple[int,int,int]) -> None:
        for key in names:
            if key in result:
                raise ValueError(f'Key {key} specified more than once')
            result[key] = rgb
    if keys is not None:
        add(_split_keys(keys), parse_rgb(color or 'white'))
    elif color is not None:
        raise ValueError('--color requires --keys')
    for item in paints:
        names, sep, col = item.partition('=')
        if not sep:
            raise ValueError(f'Expected --paint KEYS=COLOUR, received {item!r}')
        add(_split_keys(names), parse_rgb(col))
    if not result:
        raise ValueError('Supply --keys V,T,F or --paint V,T,F=white')
    return result


def _add_write_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--apply', action='store_true', help='Write to keyboard; default is a dry run')
    parser.add_argument('--acknowledge-persistence-risk', action='store_true',
                        help='Required with --apply: effect updates may write firmware flash')


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='keycue', description='Direct HID manual RGB tests for legacy K2 05ac:024f')
    subs = parser.add_subparsers(dest='command', required=True)
    subs.add_parser('identify', help='List candidate USB HID interfaces; never writes')
    subs.add_parser('keys', help='List known key names and packet positions; never writes')
    sc = subs.add_parser('set', help='All black except specified keys')
    sc.add_argument('--keys', help='Comma-separated names, e.g. V,T,F')
    sc.add_argument('--color', help='Named colour or #RRGGBB, default white')
    sc.add_argument('--paint', action='append', default=[], metavar='KEYS=COLOUR',
                    help='Additional coloured groups; may be repeated')
    _add_write_flags(sc)
    _add_write_flags(subs.add_parser('off', help='Black all 84 LEDs via full pattern write'))
    return parser


def _write_pattern(colours: Mapping[str, tuple[int,int,int]], apply: bool, acknowledge: bool) -> int:
    if acknowledge and not apply:
        raise ValueError('--acknowledge-persistence-risk requires --apply')
    actions = build_transaction(colours)
    print('=== KEYCUE PHASE-1 MANUAL TEST ===')
    print(f'Illuminated keys: {len(colours)} / 84; all others: black')
    for key, rgb in sorted(colours.items()):
        print(f'  {key:11s} RGB #{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}  packet position {packet_position(key)}')
    print(f'Protocol: {sum(a.operation == "write" for a in actions)} writes; '
          f'{sum(a.operation == "read" for a in actions)} reads')
    print('WARNING: Flash persistence is unknown. DO NOT automate or loop this command.')
    if not apply:
        print('DRY RUN: no device opened and no HID commands sent.')
        return 0
    if not acknowledge:
        raise ValueError('Refusing hardware write: review docs/SAFETY.md and add --acknowledge-persistence-risk')
    node = choose_device(discover())
    print(f'Device: {node}', flush=True)
    writes, elapsed = execute(node, actions)
    print(f'Sent {writes} HID writes in {elapsed:.1f} ms')
    print('Verify LEDs visually and check typing. HID success alone does not verify physical behaviour.')
    return 0


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.command == 'identify':
            candidates = discover()
            if not candidates:
                print('No Keychron 05ac:024f USB input0 HID device found')
                return 1
            for c in candidates:
                print(f'{c.device}: {c.physical_path}; read={c.readable}; write={c.writable}')
            print('VID:PID is shared by models; this does not independently confirm hardware revision.')
            return 0
        if args.command == 'keys':
            for key in sorted(KEY_INDICES):
                print(f'{key:12s} LED index {KEY_INDICES[key]:2d}  packet position {packet_position(key):3d}')
            return 0
        if args.command == 'off':
            return _write_pattern({}, args.apply, args.acknowledge_persistence_risk)
        if args.command == 'set':
            return _write_pattern(build_key_colours(args.keys, args.color, args.paint),
                                  args.apply, args.acknowledge_persistence_risk)
        raise RuntimeError(f'Unhandled command {args.command!r}')
    except (ValueError, RuntimeError, PermissionError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        if isinstance(exc, PermissionError):
            print('TIP: inspect hidraw permissions; for a one-shot test use sudo /usr/bin/python3 -m keycue ...',
                  file=sys.stderr)
        return 2
