"""Hardware-free tests of protocol inspection and timing instrumentation."""
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from keycue.cli import main
from keycue.device import execute, TransferTiming
from keycue.diagnostics import render_report, summarize
from keycue.protocol import build_transaction


class TestAnalysis(unittest.TestCase):
    def test_report_matches_known_transaction(self):
        actions = build_transaction({'V': (255, 255, 255)})
        summary = summarize(actions)
        self.assertEqual((summary.writes, summary.reads), (22, 3))
        self.assertEqual(summary.bytes_written, 22 * 65)
        self.assertEqual(summary.paced_operations, 25)
        report = render_report(actions)
        self.assertIn('declare 18 effect pages (0x13)', report)
        self.assertIn('RGB data page 9/9', report)
        self.assertIn('Storage persistence: UNKNOWN', report)

    def test_analyze_does_not_open_usb(self):
        with patch('keycue.cli.discover', side_effect=AssertionError('USB discovery')), \
             patch('keycue.cli.execute', side_effect=AssertionError('USB transfer')), \
             redirect_stdout(StringIO()) as out:
            code = main(['analyze'])
        self.assertEqual(code, 0)
        self.assertIn('No keyboard discovery, USB access', out.getvalue())

    def test_trace_requires_apply(self):
        with patch('keycue.cli.discover', side_effect=AssertionError('USB discovery')), \
             patch('keycue.cli.execute', side_effect=AssertionError('USB transfer')), \
             redirect_stdout(StringIO()), redirect_stderr(StringIO()) as err:
            code = main(['off', '--trace-timing'])
        self.assertEqual(code, 2)
        self.assertIn('--trace-timing requires --apply', err.getvalue())

    def test_timing_instrumentation_does_not_add_hid_calls(self):
        actions = build_transaction({'V': (255, 255, 255)})
        samples: list[TransferTiming] = []
        with patch('keycue.device.os.open', return_value=3), \
             patch('keycue.device.os.close'), \
             patch('keycue.device.fcntl.ioctl') as ioctl, \
             patch('keycue.device.time.sleep') as sleep:
            writes, _ = execute(Path('/dev/fake'), actions, timings=samples)
        self.assertEqual(writes, 22)
        self.assertEqual(ioctl.call_count, 25)
        self.assertEqual(sleep.call_count, 25)
        self.assertEqual(len(samples), 25)
        self.assertEqual(sum(x.operation == 'write' for x in samples), 22)
        self.assertTrue(all(x.ioctl_ms >= 0 and x.pacing_ms >= 0 for x in samples))

    def test_default_execute_unchanged(self):
        actions = build_transaction({})
        with patch('keycue.device.os.open', return_value=3), \
             patch('keycue.device.os.close'), \
             patch('keycue.device.fcntl.ioctl') as ioctl, \
             patch('keycue.device.time.sleep'):
            writes, elapsed = execute(Path('/dev/fake'), actions)
        self.assertEqual(writes, 22)
        self.assertGreaterEqual(elapsed, 0)
        self.assertEqual(ioctl.call_count, 25)

if __name__ == '__main__':
    unittest.main()
