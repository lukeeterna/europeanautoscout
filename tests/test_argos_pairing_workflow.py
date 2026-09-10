"""Execute the actual workflow polling shell with mock SSH and no real devices."""
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PairingPollingTests(unittest.TestCase):
    def run_poll(self, statuses):
        workflow = (ROOT / '.github/workflows/argos-c10-local-pairing.yml').read_text()
        start = workflow.index("          status=''\n")
        end = workflow.index("          echo 'PAIRING_WWEBJS_READY=YES'", start)
        script = textwrap.dedent(workflow[start:end])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'statuses').write_text('\n'.join(statuses) + '\n')
            (root / 'ssh').write_text('''#!/usr/bin/env python3
import os, pathlib, sys
root=pathlib.Path(os.environ['MOCK_ROOT'])
args=' '.join(sys.argv)
if 'qr.txt' in args:
    (root/'qr-read').touch()
    sys.exit(42)
p=root/'statuses'; lines=p.read_text().splitlines()
print(lines[0] if lines else 'STARTING')
p.write_text('\\n'.join(lines[1:])+'\\n' if len(lines)>1 else p.read_text())
''')
            (root / 'sleep').write_text('#!/bin/sh\nexit 0\n')
            for name in ('ssh', 'sleep'):
                (root / name).chmod(0o700)
            env = {**os.environ, 'PATH': f'{tmp}:' + os.environ['PATH'], 'MOCK_ROOT': tmp}
            result = subprocess.run(['bash', '-c', 'set -euo pipefail\nSSH=(); TARGET=mock; REMOTE_STAGE=mock; html="$MOCK_ROOT/qr.html"\n' + script],
                                    env=env, text=True, capture_output=True, timeout=10)
            return result, (root / 'qr-read').exists()

    def test_authenticated_without_qr_waits_for_ready(self):
        for state in ('AUTHENTICATED', 'AUTHENTICATED_NO_QR', 'STOPPING'):
            with self.subTest(state=state):
                result, qr_read = self.run_poll([state, 'READY', 'READY'])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(qr_read)

    def test_destroy_failure_is_immediate_terminal_failure(self):
        result, qr_read = self.run_poll(['DESTROY_FAILED'])
        self.assertEqual(result.returncode, 21, result.stderr)
        self.assertFalse(qr_read)

    def test_no_progress_times_out_without_fetching_qr(self):
        result, qr_read = self.run_poll(['STARTING'])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(qr_read)
