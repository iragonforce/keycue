"""Hardware-free virtual shortcut layer tests."""
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from keycue.cli import main
from keycue.layers import load_profile, parse_modifiers, normalize_modifiers

DEMO = Path(__file__).resolve().parent.parent / 'profiles/demo.toml'


class TestVirtualLayers(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(DEMO)

    def test_super_vtf_white(self):
        frame = self.profile.resolve(parse_modifiers('SUPER'))
        self.assertEqual(set(frame.keys), {'V', 'T', 'F'})
        self.assertEqual({cue.hex_colour for cue in frame.keys.values()}, {'#FFFFFF'})
        self.assertEqual({key: cue['packet_position'] for key, cue in frame.to_dict()['keys'].items()},
                         {'F': 54, 'T': 39, 'V': 70})
        self.assertEqual(frame.to_dict()['off_keys'], 81)

    def test_modifier_set_is_exact_not_subset(self):
        frame = self.profile.resolve(parse_modifiers('SHIFT+SUPER'))
        self.assertEqual(set(frame.keys), {'R', 'M', 'P'})
        self.assertEqual({cue.hex_colour for cue in frame.keys.values()}, {'#0088FF'})
        self.assertFalse(set(frame.keys) & {'V', 'T', 'F'})
        self.assertEqual(self.profile.resolve(parse_modifiers('SUPER+ALT')).keys, {})

    def test_empty_base_layer_is_off(self):
        frame = self.profile.resolve(parse_modifiers('none'))
        self.assertIsNone(frame.matched_scope)
        self.assertEqual(frame.to_dict()['off_keys'], 84)

    def test_app_specific_and_global_fallback(self):
        ghostty = self.profile.resolve(parse_modifiers('CTRL+SHIFT'), 'GhOsTtY')
        self.assertEqual(ghostty.matched_scope, 'app:ghostty')
        self.assertEqual(set(ghostty.keys), {'T'})
        fallback = self.profile.resolve(parse_modifiers('SUPER'), 'ghostty')
        self.assertEqual(fallback.matched_scope, 'global')
        self.assertEqual(set(fallback.keys), {'V', 'T', 'F'})

    def test_modifier_aliases_and_errors(self):
        self.assertEqual(parse_modifiers('Win+control'), frozenset({'SUPER','CTRL'}))
        for invalid in ('SUPER+mod4', 'SUPER+', 'SUPER+FN'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_modifiers(invalid)
        with self.assertRaises(ValueError):
            normalize_modifiers('SUPER')  # type: ignore[arg-type]

    def test_profile_validation(self):
        base = '''version = 1
[[layers]]
scope = "global"
modifiers = ["SUPER"]
[layers.keys]
V = { color = "#FFFFFF", action = "Demo" }
'''
        invalids = [
            base.replace('version = 1', 'version = 2'),
            base.replace('V = {', 'BLAH = {'),
            base.replace('#FFFFFF', '#GGGGGG'),
            base.replace('#FFFFFF', '#ff ff '),
            base.replace('action = "Demo"', 'action = ""'),
            base + '''[[layers]]
scope = "global"
modifiers = ["SUPER"]
[layers.keys]
T = { color = "#FFFFFF", action = "Duplicate layer" }
''',
            base + '''CMD = { color = "#FFFFFF", action = "Different key" }
'''.replace('CMD', 'V'),
            base.replace('scope = "global"', 'scope = "unknown"'),
        ]
        with TemporaryDirectory() as temp:
            f = Path(temp) / 'profile.toml'
            for index, invalid in enumerate(invalids):
                with self.subTest(index=index):
                    f.write_text(invalid)
                    with self.assertRaises(ValueError):
                        load_profile(f)

    def test_duplicate_key_alias_rejected(self):
        text = '''version = 1
[[layers]]
scope = "global"
modifiers = ["SUPER"]
[layers.keys]
SUPER = { color = "#FFFFFF", action = "One" }
LSUPER = { color = "#FF0000", action = "Two" }
'''
        with TemporaryDirectory() as d:
            file = Path(d)/'dup.toml'
            file.write_text(text)
            with self.assertRaises(ValueError):
                load_profile(file)

    def test_preview_never_discovers_or_writes_usb(self):
        with patch('keycue.cli.discover', side_effect=AssertionError('discovery!')), \
             patch('keycue.cli.execute', side_effect=AssertionError('HID write!')), \
             redirect_stdout(StringIO()) as stdout:
            exit_code = main(['preview', '--modifiers', 'SUPER'])
        self.assertEqual(exit_code, 0)
        self.assertIn('No USB access', stdout.getvalue())

    def test_json_is_machine_readable(self):
        with redirect_stdout(StringIO()) as stdout:
            code = main(['preview', '--modifiers', 'SUPER+SHIFT', '--format', 'json'])
        self.assertEqual(code, 0)
        frame = json.loads(stdout.getvalue())
        self.assertEqual(frame['mode'], 'virtual-preview')
        self.assertEqual(frame['modifiers'], ['SUPER','SHIFT'])
        self.assertEqual(frame['total_keys'], 84)
        self.assertEqual(frame['keys']['R']['color'], '#0088FF')

    def test_preview_invalid_inputs_do_not_discover(self):
        with patch('keycue.cli.discover', side_effect=AssertionError('discovery!')), \
             redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(main(['preview', '--modifiers', 'SUPER+FN']), 2)


if __name__ == '__main__':
    unittest.main()
