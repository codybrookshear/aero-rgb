import importlib.machinery
import importlib.util
import io
import pwd
import unittest
from pathlib import Path
from unittest.mock import patch


loader = importlib.machinery.SourceFileLoader(
    'hotkeys', str(Path(__file__).with_name('aero-rgb-hotkeys')),
)
spec = importlib.util.spec_from_loader(loader.name, loader)
hotkeys = importlib.util.module_from_spec(spec)
loader.exec_module(hotkeys)


class HotkeyTests(unittest.TestCase):
    def test_all_captured_brightness_steps_toggle(self):
        for level in (0, 24, 32, 50):
            self.assertTrue(hotkeys.is_fn_space(bytes((4, 1, level, 0))))

    def test_brightness_payload_does_not_determine_key_identity(self):
        for level in range(256):
            self.assertTrue(hotkeys.is_fn_space(bytes((4, 1, level, 0))))

    def test_fn_space_and_other_reports_do_not_toggle(self):
        for report in (
            b'', b'\x00\x00\x6f\x00\x00\x00\x00\x00',  # Fn alone
            b'\x00\x00\x2c\x00\x00\x00\x00\x00',  # Space alone
            b'\x03\x01\x20\x00', b'\x04\x02\x20\x00',
            b'\x04\x01\x20\x01',
            b'\x04\x01\x20', b'\x04\x01\x20\x00\x00',
        ):
            self.assertFalse(hotkeys.is_fn_space(report), report)

    def test_listener_dispatches_once_per_vendor_report(self):
        reports = [b'\x00\x00\x6f\x00\x00\x00\x00\x00',
                   b'\x04\x01\x20\x00', b'\x04\x01\x32\x00',
                   b'\x00' * 8, b'\x04\x01\x00\x00', b'']
        with patch('builtins.open') as source, patch('sys.stdout', new_callable=io.StringIO), \
                patch.object(hotkeys, 'toggle_as_user', return_value=0) as toggle:
            source.return_value.__enter__.return_value.read.side_effect = reports
            with self.assertRaisesRegex(OSError, 'disconnected'):
                hotkeys.listen('/dev/test', toggle)
            self.assertEqual(toggle.call_count, 3)

    def test_toggle_drops_privileges_and_uses_users_state(self):
        user = pwd.struct_passwd(('example', 'x', 1234, 1235, '', '/home/example', '/bin/sh'))
        with patch.object(hotkeys.os, 'getgrouplist', return_value=[1235, 1236]), \
                patch.object(hotkeys.subprocess, 'run') as run:
            run.return_value.returncode = 0
            self.assertEqual(hotkeys.toggle_as_user(user, Path('/opt/aero-rgb')), 0)
            args, kwargs = run.call_args
            self.assertEqual(args[0], ['/opt/aero-rgb', 'toggle'])
            self.assertEqual(kwargs['user'], 1234)
            self.assertEqual(kwargs['group'], 1235)
            self.assertEqual(kwargs['extra_groups'], [1235, 1236])
            self.assertEqual(kwargs['env']['HOME'], '/home/example')
            self.assertNotIn('XDG_STATE_HOME', kwargs['env'])

    def test_unexpected_flags_are_diagnosable_without_logging_keys(self):
        reports = [b'\x05\x00\x2c\x00', b'\x04\x01\x10\x01', b'']
        with patch('builtins.open') as source, \
                patch('sys.stdout', new_callable=io.StringIO) as output, \
                patch.object(hotkeys, 'toggle_as_user') as toggle:
            source.return_value.__enter__.return_value.read.side_effect = reports
            with self.assertRaisesRegex(OSError, 'disconnected'):
                hotkeys.listen('/dev/test', toggle)
            toggle.assert_not_called()
            self.assertEqual(output.getvalue().splitlines(), [
                'Listening for Fn+Space on /dev/test',
                'Ignored vendor brightness notification: level=16 flags=1',
            ])

    def test_success_success_miss_capture_now_dispatches_three_toggles(self):
        # The third report was previously dropped because 24 was not in the
        # initial sample of firmware brightness levels.
        reports = [b'\x04\x01\x32\x00', b'\x04\x01\x00\x00',
                   b'\x04\x01\x18\x00', b'']
        with patch('builtins.open') as source, patch('sys.stdout', new_callable=io.StringIO), \
                patch.object(hotkeys, 'toggle_as_user', return_value=0) as toggle:
            source.return_value.__enter__.return_value.read.side_effect = reports
            with self.assertRaisesRegex(OSError, 'disconnected'):
                hotkeys.listen('/dev/test', toggle)
            self.assertEqual(toggle.call_count, 3)


if __name__ == '__main__':
    unittest.main()
