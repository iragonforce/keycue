import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from unittest.mock import patch
from pathlib import Path
from keycue.cli import build_key_colours, main, parse_rgb
from keycue.device import Candidate, choose_device

class TestCLI(unittest.TestCase):
    def test_colours(self):
        self.assertEqual(parse_rgb('white'), (255,255,255))
        self.assertEqual(parse_rgb('#0000ff'), (0,0,255))
        for bad in ('#ff', 'rgb(0,0,0)', 'test'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_rgb(bad)

    def test_groups(self):
        actual = build_key_colours('V,T,F', 'white', ['R,M,P=blue'])
        self.assertEqual(actual, {
            'V':(255,255,255), 'T':(255,255,255), 'F':(255,255,255),
            'R':(0,0,255), 'M':(0,0,255), 'P':(0,0,255),
        })

    def test_alias_duplicate(self):
        with self.assertRaises(ValueError):
            build_key_colours('LSUPER', None, ['cmd=white'])

    def test_dry_run_never_touches_hardware(self):
        with patch('keycue.cli.discover', side_effect=AssertionError('hardware discovery called')), \
             patch('keycue.cli.execute', side_effect=AssertionError('HID write called')), \
             redirect_stdout(StringIO()) as output:
            code = main(['set', '--keys', 'V,T,F', '--color', 'white'])
        self.assertEqual(code, 0)
        self.assertIn('DRY RUN', output.getvalue())

    def test_write_requires_acknowledgment_before_discovery(self):
        with patch('keycue.cli.discover', side_effect=AssertionError('hardware discovery called')), \
             redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            code = main(['off', '--apply'])
        self.assertEqual(code, 2)

    def test_ambiguous_hardware_blocked(self):
        with self.assertRaises(RuntimeError):
            choose_device([])
        with self.assertRaises(RuntimeError):
            choose_device([
                Candidate(Path('/dev/hidraw1'),'x',True,True),
                Candidate(Path('/dev/hidraw9'),'y',True,True),
            ])

if __name__ == '__main__':
    unittest.main()
