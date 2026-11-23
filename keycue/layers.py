"""Offline shortcut-to-LED-frame resolver. No HID, keyboard or window access.

Profiles are *examples or explicitly supplied data*, never discovered keybinds.
An app-specific exact modifier layer takes precedence over global; a missing
app-specific layer falls back to global. No partial modifier matching occurs.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping
import tomllib

from .keymap import KEY_INDICES, normalize_key, packet_position

MODIFIER_ALIASES: dict[str, str] = {
    'SUPER': 'SUPER', 'WIN': 'SUPER', 'META': 'SUPER', 'CMD': 'SUPER', 'MOD4': 'SUPER',
    'SHIFT': 'SHIFT',
    'CTRL': 'CTRL', 'CONTROL': 'CTRL',
    'ALT': 'ALT', 'MOD1': 'ALT',
}
MODIFIER_ORDER = ('SUPER', 'SHIFT', 'CTRL', 'ALT')


def normalize_modifiers(items: list[str] | tuple[str, ...]) -> frozenset[str]:
    if not isinstance(items, (list, tuple)) or any(not isinstance(x, str) for x in items):
        raise ValueError('modifiers must be a list of strings')
    result = []
    for item in items:
        name = MODIFIER_ALIASES.get(item.strip().upper())
        if name is None:
            raise ValueError(f'Unknown modifier {item!r}; use SUPER, SHIFT, CTRL, ALT')
        if name in result:
            raise ValueError(f'Duplicate modifier {item!r}')
        result.append(name)
    return frozenset(result)


def parse_modifiers(value: str) -> frozenset[str]:
    if not value.strip() or value.strip().lower() in ('none', 'base'):
        return frozenset()
    return normalize_modifiers(value.split('+'))


def modifiers_label(modifiers: frozenset[str]) -> str:
    return '+'.join(m for m in MODIFIER_ORDER if m in modifiers) or 'NONE'


def normalize_scope(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError('scope must be a string')
    scope = value.strip().casefold()
    if scope == 'global':
        return scope
    if scope.startswith('app:') and scope[4:] and scope[4:] == scope[4:].strip():
        return scope
    raise ValueError(f'Invalid scope {value!r}; expected global or app:<name>')


def parse_colour(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or re.fullmatch(r'#[0-9A-Fa-f]{6}', value) is None:
        raise ValueError(f'Invalid colour {value!r}; expected #RRGGBB')
    return tuple(bytes.fromhex(value[1:]))  # type: ignore[return-value]


@dataclass(frozen=True)
class Cue:
    colour: tuple[int, int, int]
    action: str

    @property
    def hex_colour(self) -> str:
        return '#%02X%02X%02X' % self.colour


@dataclass(frozen=True)
class Layer:
    scope: str
    modifiers: frozenset[str]
    keys: Mapping[str, Cue]


@dataclass(frozen=True)
class Profile:
    layers: Mapping[tuple[str, frozenset[str]], Layer]

    def resolve(self, modifiers: frozenset[str], app: str | None = None) -> 'Frame':
        if not isinstance(modifiers, frozenset) or not modifiers.issubset(set(MODIFIER_ORDER)):
            raise ValueError('Invalid canonical modifiers')
        scope = normalize_scope(f'app:{app}') if app is not None else 'global'
        layer = self.layers.get((scope, modifiers))
        if layer is None and scope != 'global':
            layer = self.layers.get(('global', modifiers))
        keys = layer.keys if layer else MappingProxyType({})
        return Frame(modifiers, scope, layer.scope if layer else None, keys)


@dataclass(frozen=True)
class Frame:
    modifiers: frozenset[str]
    requested_scope: str
    matched_scope: str | None
    keys: Mapping[str, Cue]

    def to_dict(self) -> dict:
        return {
            'mode': 'virtual-preview',
            'requested_scope': self.requested_scope,
            'modifiers': [m for m in MODIFIER_ORDER if m in self.modifiers],
            'matched_scope': self.matched_scope,
            'background': '#000000',
            'total_keys': len(KEY_INDICES),
            'off_keys': len(KEY_INDICES) - len(self.keys),
            'keys': {
                name: {
                    'color': cue.hex_colour,
                    'action': cue.action,
                    'packet_position': packet_position(name),
                }
                for name, cue in sorted(self.keys.items())
            },
        }


def load_profile(path: Path) -> Profile:
    """Validate a versioned TOML profile without opening any device."""
    try:
        data = tomllib.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f'Cannot read profile {path}: {exc}') from exc
    if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('Profile requires version = 1')
    if set(data) != {'version', 'layers'}:
        raise ValueError('Profile must contain only version and layers')
    if not isinstance(data['layers'], list):
        raise ValueError('layers must be a TOML array of tables')
    layers: dict[tuple[str, frozenset[str]], Layer] = {}
    for index, item in enumerate(data['layers'], start=1):
        if not isinstance(item, dict) or set(item) != {'scope', 'modifiers', 'keys'}:
            raise ValueError(f'Layer {index}: requires scope, modifiers, keys')
        scope = normalize_scope(item['scope'])
        modifiers = normalize_modifiers(item['modifiers'])
        if not isinstance(item['keys'], dict):
            raise ValueError(f'Layer {index}: keys must be a TOML table')
        keys: dict[str, Cue] = {}
        for raw_key, value in item['keys'].items():
            key = normalize_key(raw_key)
            if key in keys:
                raise ValueError(f'Layer {index}: duplicate key after alias normalization: {key}')
            if not isinstance(value, dict) or set(value) != {'color', 'action'}:
                raise ValueError(f'Layer {index}, {key}: requires color and action')
            action = value['action']
            if not isinstance(action, str) or not action.strip():
                raise ValueError(f'Layer {index}, {key}: action must be nonempty text')
            keys[key] = Cue(parse_colour(value['color']), action.strip())
        identity = (scope, modifiers)
        if identity in layers:
            raise ValueError(f'Duplicate layer: {scope} / {modifiers_label(modifiers)}')
        layers[identity] = Layer(scope, modifiers, MappingProxyType(keys))
    return Profile(MappingProxyType(layers))
