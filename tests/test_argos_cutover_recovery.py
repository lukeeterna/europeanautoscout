"""Run the workflow's remote promotion shell on a temporary filesystem.

Only process/PM2 commands are mocked. SQLite, copy, rename and error traps run.
Never SSH, WhatsApp, or the user's production home.
"""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
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


def cutover_remote_script():
    source = (ROOT / 'wa-intelligence/tools/argos_c10_wwebjs_cutover.sh').read_text()
    script = source.split("<<'REMOTE'\n", 1)[1].split('\nREMOTE\n', 1)[0]
    script = script.replace('PY313="/usr/local/bin/python3.13"', f'PY313="{sys.executable}"')
    return script.replace('/usr/sbin/lsof', 'lsof')


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


class FullCutoverRecoveryTests(unittest.TestCase):
    """Execute the actual cutover remote body with only external tools mocked."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / 'home'
        # The production body deliberately prepends this exact directory to
        # PATH, so mocks remain effective after its PATH hardening.
        self.bin = self.home / '.npm-global/bin'
        self.bin.mkdir(parents=True)
        self.old = self.home / 'old/wa-intelligence'
        self.old.mkdir(parents=True)
        (self.old / 'ecosystem.config.js').write_text('// old runtime')
        (self.old / '.env').write_text('ARGOS_API_KEY=fixture-not-a-secret\n')

        app = self.home / 'Documents/app-antigravity-auto'
        (app / 'comm-broker').mkdir(parents=True)
        (app / 'wa-sender/session-argos-business').mkdir(parents=True)
        (app / 'wa-sender/session-argos-business/credential').write_text('closed-profile')
        self.primary = app / 'dealer_network.sqlite'
        self.bridge = app / 'comm-broker/bridge.sqlite'
        with sqlite3.connect(self.primary) as conn:
            conn.executescript(
                "CREATE TABLE messages(direction); "
                "CREATE TABLE argos_runtime_state(key,value); "
                "INSERT INTO argos_runtime_state VALUES('agent_status','PAUSED');"
            )
            conn.executemany('INSERT INTO messages VALUES(?)', [('OUTBOUND',)] * 77)
        with sqlite3.connect(self.bridge) as conn:
            conn.execute('CREATE TABLE bridge_fixture(id INTEGER PRIMARY KEY)')

        short = SHA[:12]
        self.release = self.home / f'Documents/argos-c10-release-{short}'
        (self.release / '.git').mkdir(parents=True)
        (self.release / 'wa-intelligence').mkdir()
        smoke = self.release / 'tools/scripts/argos_c10_smoke.py'
        smoke.parent.mkdir(parents=True)
        smoke.write_text(textwrap.dedent('''
            import os, sys
            mode = sys.argv[sys.argv.index('--mode') + 1]
            requested = os.environ.get('MOCK_MODE', '')
            if requested == f'{mode}_fail':
                raise SystemExit(42)
            print(f'MOCK_SMOKE_{mode.upper()}=PASS')
        '''))

        chrome = self.home / ('.cache/puppeteer/chrome/mac-148.0.7778.97/'
                              'chrome-mac-x64/Google Chrome for Testing.app/'
                              'Contents/MacOS/Google Chrome for Testing')
        self.write_exec(chrome, '#!/bin/sh\nexit 0\n')
        self.write_exec(self.bin / 'sleep', '#!/bin/sh\nexit 0\n')
        self.write_exec(self.bin / 'npm', '#!/bin/sh\nexit 0\n')
        self.write_exec(self.bin / 'node', '#!/bin/sh\nexit 0\n')
        self.write_exec(self.bin / 'git', f'''#!/bin/sh
case "$*" in *"rev-parse HEAD"*) printf '%s\\n' '{SHA}';; esac
exit 0
''')
        self.write_exec(self.bin / 'lsof', '''#!/bin/sh
case "$*" in
  *"-d cwd"*) printf 'n%s\\n' "$MOCK_OLD" ;;
  *) printf '123\\n' ;;
esac
''')
        self.write_exec(self.bin / 'ps', '''#!/bin/sh
if [ "$MOCK_MODE" = browser_timeout ]; then
  printf '222 chrome %s\\n' "$MOCK_SESSION"
fi
if [ ! -f "$MOCK_ROOT/stopped" ]; then
  printf '123 node wa-daemon.js\\n'
fi
''')
        self.write_exec(self.bin / 'curl', '''#!/bin/sh
printf '%s\\n' '{"runtime":"argos-s292-single-writer","transport":"wwebjs","agent_status":"PAUSED","bridge_enabled":true,"connected":true}'
''')
        self.pm2 = self.home / '.npm-global/bin/pm2'
        self.write_exec(self.pm2, '''#!/bin/sh
printf '%s|%s\\n' "$PWD" "$*" >> "$MOCK_ROOT/pm2-actions"
case "$1" in
  stop|delete) touch "$MOCK_ROOT/stopped" ;;
  start)
    if [ "$MOCK_MODE" = start_fail ] && [ "$PWD" = "$MOCK_RELEASE/wa-intelligence" ]; then
      exit 44
    fi
    if [ "$MOCK_MODE" = rollback_start_fail ] && [ "$PWD" = "$MOCK_OLD" ]; then
      exit 46
    fi
    rm -f "$MOCK_ROOT/stopped"
    ;;
  save)
    case "$MOCK_MODE" in save_fail|rollback_start_fail) exit 45 ;; esac
    ;;
esac
''')

    def write_exec(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        path.chmod(0o700)

    def run_script(self, mode=''):
        env = {
            **os.environ,
            'HOME': str(self.home),
            'PATH': str(self.bin) + ':' + os.environ['PATH'],
            'MOCK_MODE': mode,
            'MOCK_ROOT': str(self.root),
            'MOCK_OLD': str(self.old),
            'MOCK_RELEASE': str(self.release),
            'MOCK_SESSION': str(self.home / 'Documents/app-antigravity-auto/wa-sender'),
        }
        return subprocess.run(
            ['bash', '-s', '--', SHA], input=cutover_remote_script(), env=env,
            text=True, capture_output=True, timeout=15,
        )

    def backup_files(self):
        root = self.home / 'Documents/argos-c10-backups'
        return sorted(root.glob('*/*.sqlite')) if root.exists() else []

    def test_success_runs_real_backup_and_zero_outbound_contract(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('CUTOVER=GREEN', result.stdout)
        self.assertIn('OUTBOUND_DELTA=0', result.stdout)
        backups = self.backup_files()
        self.assertEqual(len(backups), 2)
        for path in backups:
            with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as conn:
                self.assertEqual(conn.execute('PRAGMA quick_check').fetchone()[0], 'ok')
        self.assertIn('|save', (self.root / 'pm2-actions').read_text())

    def test_predeploy_failure_never_mutates_processes(self):
        result = self.run_script('predeploy_fail')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / 'pm2-actions').exists())
        self.assertEqual(len(self.backup_files()), 2)
        self.assertNotIn('ROLLBACK=BEGIN', result.stderr)

    def test_new_runtime_start_failure_restores_old_runtime(self):
        result = self.run_script('start_fail')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ROLLBACK=PASS', result.stderr)
        actions = (self.root / 'pm2-actions').read_text()
        self.assertIn(f'{self.release / "wa-intelligence"}|start ', actions)
        self.assertIn(f'{self.old}|start ', actions)
        self.assertFalse((self.root / 'stopped').exists())

    def test_postdeploy_failure_restores_old_runtime(self):
        result = self.run_script('postdeploy_fail')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ROLLBACK=PASS', result.stderr)
        self.assertFalse((self.root / 'stopped').exists())

    def test_pm2_save_failure_restores_old_runtime(self):
        result = self.run_script('save_fail')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ROLLBACK_WRITER_COUNT=1', result.stderr)
        self.assertIn('ROLLBACK=PASS', result.stderr)
        self.assertFalse((self.root / 'stopped').exists())

    def test_failed_old_runtime_restart_cannot_claim_rollback_pass(self):
        result = self.run_script('rollback_start_fail')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ROLLBACK_WRITER_COUNT=0', result.stderr)
        self.assertIn('ROLLBACK=DEGRADED', result.stderr)
        self.assertNotIn('ROLLBACK=PASS', result.stderr)
        self.assertTrue((self.root / 'stopped').exists())

    def test_browser_timeout_blocks_rollback_restart(self):
        result = self.run_script('browser_timeout')
        self.assertEqual(result.returncode, 30, result.stderr)
        self.assertIn('ROLLBACK=BLOCKED_BROWSER', result.stderr)
        actions = (self.root / 'pm2-actions').read_text()
        self.assertNotIn(f'{self.old}|start ', actions)
        self.assertTrue((self.root / 'stopped').exists())
