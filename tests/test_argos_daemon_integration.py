"""Real entrypoint/HTTP/SQLite/Python pipeline; WhatsApp is an in-process mock.

All data is synthetic and all sockets bind localhost. No browser, credentials,
real profiles or external recipient. No production config is loaded.
"""
from pathlib import Path
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
WA = ROOT / 'wa-intelligence'
sys.path.insert(0, str(WA))
from state_machine import ensure_state_columns
from whatsapp_consent import grant_consent, ensure_consent_columns
from templates import fill_template


class DaemonIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / 'primary.sqlite'
        self.bridge = self.root / 'bridge.sqlite'
        self.auth = self.root / 'auth'
        self.auth.mkdir()
        with sqlite3.connect(self.db) as c:
            c.executescript("""CREATE TABLE conversations (
                dealer_id TEXT PRIMARY KEY, dealer_name TEXT, phone_number TEXT,
                source TEXT, current_step TEXT, conversation_state TEXT,
                outbound_count INTEGER DEFAULT 0, inbound_count INTEGER DEFAULT 0,
                outreach_authorized INTEGER DEFAULT 1, handoff_source TEXT DEFAULT 'cold');
                INSERT INTO conversations(dealer_id,dealer_name,phone_number,source,current_step,conversation_state)
                VALUES('fixture','Fixture','390000000001','test consent','COLD','COLD');""")
        ensure_state_columns(str(self.db))
        ensure_consent_columns(str(self.db))
        grant_consent(db_path=str(self.db), dealer_id='fixture', source='offline_fixture', evidence_id='synthetic-consent')
        self.preload = self.root / 'mock.cjs'
        self.preload.write_text("""
const Module=require('module'), fs=require('fs'), path=require('path');
const original=Module._load;
Module._load=function(name,parent,...rest){
  if(name==='./transport' && parent.filename.endsWith('/wa-daemon.js')){
    const {TransportError}=original.call(this,path.join(path.dirname(parent.filename),'transport/errors.js'),parent,...rest);
    return {TransportError,createTransport:({callbacks})=>({
      isConnected:()=>true,
      initialize:async()=>{callbacks.onReady();const timer=setInterval(()=>{
        const p=path.join(process.env.ARGOS_MOCK_ROOT,'inbound');
        if(fs.existsSync(p)){fs.unlinkSync(p);const msg={from:'390000000001@c.us',body:'Mi interessa, come funziona?',id:{_serialized:'mock-inbound'}};callbacks.onMessage(msg);callbacks.onMessage(msg);}
      },50);timer.unref();return {};},
      sendText:async()=>{fs.appendFileSync(path.join(process.env.ARGOS_MOCK_ROOT,'sends'),'1\\n');return {wa_msg_id:'mock-outbound'};},
      sendDocument:async()=>{throw new Error('not allowed in this fixture');},
      shutdown:async()=>{}
    })};
  }
  if(name==='whatsapp-web.js')throw new Error('REAL WHATSAPP FORBIDDEN');
  return original.call(this,name,parent,...rest);
};
""")
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); self.port = sock.getsockname()[1]
        self.env = {**os.environ, 'ARGOS_DB_PATH': str(self.db), 'BRIDGE_DB_PATH': str(self.bridge),
                    'ARGOS_API_KEY': 'offline-fixture-only', 'ARGOS_WA_TRANSPORT': 'wwebjs',
                    'ARGOS_WA_SESSION_DIR': str(self.auth), 'ARGOS_WA_CLIENT_ID': 'argos-business',
                    'ARGOS_WA_PORT': str(self.port), 'ARGOS_BIND_HOST': '127.0.0.1',
                    'ARGOS_PYTHON': sys.executable, 'ARGOS_AUTOMATION_ENABLED': '0',
                    'ARGOS_BUSINESS_START_HOUR': '0', 'ARGOS_BUSINESS_END_HOUR': '24',
                    'ARGOS_BUSINESS_DAYS': '0,1,2,3,4,5,6', 'ARGOS_BRIDGE_POLL_MS': '5000',
                    'ARGOS_INBOUND_DEBOUNCE_MS': '1000', 'ARGOS_MOCK_ROOT': str(self.root),
                    'NODE_OPTIONS': f'--require={self.preload}'}
        self.log = (self.root / 'daemon.log').open('w+')
        self.addCleanup(self.log.close)
        self.process = subprocess.Popen([sys.executable, str(WA / 'runtime_entrypoint.py')], env=self.env,
                                        stdout=self.log, stderr=self.log, cwd=ROOT)
        self.addCleanup(self.stop)
        self.wait(lambda: self.http('/health')[0] == 200)

    def stop(self):
        if self.process.poll() is None:
            self.process.terminate()
            try: self.process.wait(timeout=5)
            except subprocess.TimeoutExpired: self.process.kill(); self.process.wait(timeout=5)

    def wait(self, predicate):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                if predicate(): return
            except (OSError, sqlite3.Error): pass
            if self.process.poll() is not None:
                self.log.seek(0); self.fail('mock daemon exited: ' + self.log.read())
            time.sleep(0.05)
        self.fail('mock pipeline did not reach expected state within 15s')

    def http(self, route, payload=None):
        req = urllib.request.Request(f'http://127.0.0.1:{self.port}{route}',
          data=json.dumps(payload).encode() if payload is not None else None,
          headers={'x-api-key':'offline-fixture-only','Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=5) as r: return r.status,json.load(r)
        except urllib.error.HTTPError as e: return e.code,json.load(e)

    def scalar(self, query, bridge=False):
        with sqlite3.connect(self.bridge if bridge else self.db) as c: return c.execute(query).fetchone()[0]

    def payload(self):
        return {'dealer_id':'fixture','phone':'390000000001','template_id':'DAY1_PREMIUM',
          'message':fill_template('DAY1_PREMIUM',{'source':'contatto di test autorizzato','brand_focus':'BMW'}),
          'idempotency_key':'synthetic-c11'}

    def test_http_single_send_persistence_inbound_analyzer_and_duplicate(self):
        self.assertEqual(self.http('/health')[1]['agent_status'], 'PAUSED')
        self.assertNotEqual(self.http('/send', self.payload())[0], 200)
        self.assertFalse((self.root/'sends').exists())
        self.assertEqual(self.http('/resume', {})[0], 200)
        status, result = self.http('/send', self.payload())
        self.assertEqual(status, 200, result)
        self.assertEqual(result['wa_msg_id'], 'mock-outbound')
        self.assertEqual(self.http('/send', self.payload())[0], 200)
        self.assertEqual((self.root/'sends').read_text().splitlines(), ['1'])
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM messages WHERE direction='OUTBOUND'"), 1)
        self.assertEqual(self.scalar('SELECT status FROM argos_send_intents'), 'SENT')
        self.assertEqual(self.scalar("SELECT outbound_count FROM conversations WHERE dealer_id='fixture'"), 1)
        self.http('/pause', {})
        (self.root/'inbound').touch()
        self.wait(lambda: self.scalar("SELECT COUNT(*) FROM audit_log WHERE event_type='ANALYZER_EXIT'") == 1)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM messages WHERE direction='INBOUND'"), 1)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM bridge_inbound', bridge=True), 1)
        self.assertEqual(self.scalar("SELECT processed FROM messages WHERE direction='INBOUND'"), 1)
        self.assertEqual(self.scalar("SELECT conversation_state FROM conversations WHERE dealer_id='fixture'"), 'ENGAGED')
        self.assertEqual((self.root/'sends').read_text().splitlines(), ['1'])

    def test_bridge_sent_marker_recovery_does_not_send_twice(self):
        payload = self.payload()
        with sqlite3.connect(self.bridge) as c:
            c.execute("""INSERT INTO bridge_outbound
                (id,deal_id,target_role,target_phone,template_phase,template_id,body,created_ts,approved_ts)
                VALUES('mock-row','fixture','dealer',?,'day1','DAY1_PREMIUM',?,1,1)""",
                (payload['phone'], payload['message']))
        self.http('/resume', {})
        self.wait(lambda: self.scalar("SELECT sent_status FROM bridge_outbound WHERE id='mock-row'", bridge=True) == 'SENT')
        with sqlite3.connect(self.bridge) as c:
            c.execute("UPDATE bridge_outbound SET sent_status=NULL,sent_ts=NULL,processing_ts=NULL WHERE id='mock-row'")
        self.wait(lambda: self.scalar("SELECT sent_status FROM bridge_outbound WHERE id='mock-row'", bridge=True) == 'SENT')
        self.assertEqual((self.root/'sends').read_text().splitlines(), ['1'])
        self.assertEqual(self.scalar("SELECT wa_msg_id FROM bridge_outbound WHERE id='mock-row'", bridge=True), 'mock-outbound')
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM messages WHERE direction='OUTBOUND'"), 1)

    def test_second_entrypoint_with_different_port_is_blocked(self):
        env = {**self.env, 'ARGOS_WA_PORT': '0'}
        second = subprocess.run([sys.executable, str(WA/'runtime_entrypoint.py')], env=env,
                                cwd=ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(second.returncode, 2)
        self.assertIn('writer lock is unavailable', second.stderr)
        self.assertEqual(self.http('/health')[1]['agent_status'], 'PAUSED')
        self.assertFalse((self.root/'sends').exists())
