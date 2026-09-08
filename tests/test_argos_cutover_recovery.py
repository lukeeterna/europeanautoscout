"""Run the workflow's remote promotion shell on a temporary filesystem.

Only process/PM2 commands are mocked. SQLite, copy, rename and error traps run.
Never SSH, WhatsApp, or the user's production home.
"""
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHA = 'a' * 40


def remote_script(step_name):
    source = (ROOT / '.github/workflows/argos-c10-wwebjs-cutover.yml').read_text()
    block = source.split('      - name: ' + step_name, 1)[1].split('\n      - name:', 1)[0]
    script = block.split("<<'REMOTE'\n", 1)[1].split('\n          REMOTE', 1)[0]
    return textwrap.dedent(script).replace('/usr/sbin/lsof', 'lsof')


class ProfileRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / 'home'
        self.canonical = self.home / 'Documents/app-antigravity-auto/wa-sender/session-argos-business'
        self.canonical.mkdir(parents=True)
        (self.canonical / 'credential').write_text('before-shutdown')
        self.ready = self.home / f'Documents/argos-c10-pairing-ready/{SHA}'
        (self.ready / 'auth/session-argos-business').mkdir(parents=True)
        (self.ready / 'auth/session-argos-business/credential').write_text('paired')
        (self.ready / 'MANIFEST').write_text(f'pairing_source_sha={SHA}\nclient_id=argos-business\n')
        self.promo = self.home / f'Documents/argos-c10-pairing-promotions/{SHA}-123'
        self.old = self.home / 'old/wa-intelligence'
        self.old.mkdir(parents=True)
        (self.old / 'ecosystem.config.js').write_text('// mock')
        db = self.home / 'Documents/app-antigravity-auto/dealer_network.sqlite'
        with sqlite3.connect(db) as conn:
            conn.executescript("CREATE TABLE messages(direction); CREATE TABLE argos_runtime_state(key,value); INSERT INTO argos_runtime_state VALUES('agent_status','PAUSED');")
            conn.executemany('INSERT INTO messages VALUES(?)', [('OUTBOUND',)] * 77)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.write_exec(self.bin / 'sleep', '#!/bin/sh\nexit 0\n')
        self.write_exec(self.bin / 'lsof', '#!/bin/sh\nprintf "n%s\\n" "$MOCK_OLD"\n')
        self.write_exec(self.bin / 'ps', '''#!/bin/sh
if [ "$MOCK_MODE" = browser ]; then printf 'chrome %s\\n' "$MOCK_SESSION"; fi
if [ ! -f "$MOCK_ROOT/stopped" ]; then echo '123 node wa-daemon.js'; fi
''')
        self.write_exec(self.bin / 'mv', """#!/bin/sh
case "$1" in
  */new-session) [ "$MOCK_MODE" != renamefail ] || exit 45 ;;
esac
exec /bin/mv "$@"
""")
        self.write_exec(self.bin / 'cp', '''#!/bin/sh
case "$*" in
  *argos-c10-pairing-ready*) [ "$MOCK_MODE" != copyfail ] || exit 42 ;;
esac
exec /bin/cp "$@"
''')
        self.write_exec(self.home / '.npm-global/bin/pm2', '''#!/bin/sh
case "$1" in
  stop|delete)
    touch "$MOCK_ROOT/stopped"
    if [ -f "$MOCK_SESSION/session-argos-business/credential" ]; then
      printf 'after-shutdown' > "$MOCK_SESSION/session-argos-business/credential"
    fi
    ;;
  start)
    if [ "$MOCK_MODE" = startfail ] && [ ! -f "$MOCK_ROOT/failed-once" ]; then touch "$MOCK_ROOT/failed-once"; exit 44; fi
    rm -f "$MOCK_ROOT/stopped" ;;
esac
''')

    def write_exec(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        path.chmod(0o700)

    def run_script(self, mode='', external=False):
        step = ('Restore pre-pairing LocalAuth and old runtime on any cutover proof failure' if external
                else 'Promote staged READY LocalAuth with rollback boundary')
        env = {**os.environ, 'HOME': str(self.home), 'PATH': str(self.bin) + ':' + os.environ['PATH'],
               'MOCK_MODE': mode, 'MOCK_ROOT': str(self.root), 'MOCK_OLD': str(self.old),
               'MOCK_SESSION': str(self.canonical.parent)}
        return subprocess.run(['bash', '-s', '--', SHA, '123'], input=remote_script(step),
                              env=env, text=True, capture_output=True, timeout=10)

    def test_backup_captures_closed_profile(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.promo / 'original-session/credential').read_text(), 'after-shutdown')
        self.assertEqual((self.canonical / 'credential').read_text(), 'paired')

    def test_browser_timeout_preserves_profile_and_blocks_restart(self):
        result = self.run_script('browser')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.canonical / 'credential').read_text(), 'after-shutdown')
        self.assertTrue((self.root / 'stopped').exists())

    def test_copy_failure_restores_closed_original(self):
        result = self.run_script('copyfail')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.canonical / 'credential').read_text(), 'after-shutdown')

    def test_restart_failure_restores_closed_original(self):
        result = self.run_script('startfail')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.canonical / 'credential').read_text(), 'after-shutdown')

    def test_wrong_client_manifest_blocks_before_mutation(self):
        (self.ready / 'MANIFEST').write_text(f'pairing_source_sha={SHA}\nclient_id=wrong\n')
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.canonical / 'credential').read_text(), 'before-shutdown')

    def test_external_rollback_restores_original(self):
        self.assertEqual(self.run_script().returncode, 0)
        result = self.run_script(external=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.canonical / 'credential').read_text(), 'after-shutdown')

    def test_failed_promotion_rename_recovers_original(self):
        result = self.run_script('renamefail')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.canonical / 'credential').read_text(), 'after-shutdown')
        self.assertTrue((self.promo / 'original-session/credential').is_file())

    def test_empty_exact_profile_blocks_before_mutation(self):
        (self.ready / 'auth/session-argos-business/credential').unlink()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.canonical / 'credential').read_text(), 'before-shutdown')

    def test_external_rollback_blocks_with_live_browser(self):
        self.assertEqual(self.run_script().returncode, 0)
        result = self.run_script('browser', external=True)
        self.assertEqual(result.returncode, 30, result.stderr)
        self.assertTrue((self.promo / 'original-session/credential').is_file())
        self.assertTrue((self.root / 'stopped').exists())
