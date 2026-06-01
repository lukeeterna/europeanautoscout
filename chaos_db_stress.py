#!/usr/bin/env python3
"""CHAOS 6: Concurrent DB + HTTP stress test"""

import sqlite3
import threading
import time
import urllib.request
import json
import sys
import os

db_path = '/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite'
api_url = 'http://localhost:9191/send'
api_key = os.environ['ARGOS_API_KEY']
errors = []
lock = threading.Lock()

def db_writer(n):
    """Perform 50 sequential DB updates"""
    try:
        con = sqlite3.connect(db_path, timeout=10)
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('PRAGMA busy_timeout=10000')
        for i in range(50):
            con.execute(
                'UPDATE conversations SET outbound_count = outbound_count WHERE dealer_id = ?',
                ('TEST_FOUNDER',)
            )
            con.commit()
        con.close()
        with lock:
            print(f"DB Writer {n}: OK (50 updates)")
    except Exception as e:
        with lock:
            errors.append(f'Writer-{n}: {e}')
            print(f"DB Writer {n}: FAIL - {e}")

def http_sender(n):
    """Make 10 sequential HTTP requests"""
    try:
        for j in range(10):
            data = json.dumps({
                'phone': '393314928901',
                'message': f'DB stress {n}-{j}',
                'dry_run': True
            }).encode()
            req = urllib.request.Request(api_url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            req.add_header('X-API-Key', api_key)
            response = urllib.request.urlopen(req, timeout=15)
            resp_data = json.loads(response.read().decode())
            if resp_data.get('status') != 'sent':
                raise ValueError(f"Bad status: {resp_data}")
        with lock:
            print(f"HTTP Sender {n}: OK (10 requests)")
    except Exception as e:
        with lock:
            errors.append(f'HTTP-{n}: {e}')
            print(f"HTTP Sender {n}: FAIL - {e}")

print("=== CHAOS 6: DB + HTTP Concurrent Stress ===")
print("Starting 5 DB writers + 5 HTTP senders...")

threads = []
start = time.time()

# Start DB writers
for i in range(5):
    t = threading.Thread(target=db_writer, args=(i,))
    threads.append(t)
    t.start()

# Start HTTP senders
for i in range(5):
    t = threading.Thread(target=http_sender, args=(i,))
    threads.append(t)
    t.start()

# Wait for all
for t in threads:
    t.join()

elapsed = time.time() - start

print(f"\nCHAOS 6 Results:")
print(f"  Duration: {elapsed:.2f}s")
print(f"  Errors: {len(errors)}")
if errors:
    for e in errors:
        print(f"    - {e}")
    print(f"CHAOS 6: FAIL")
    sys.exit(1)
else:
    print(f"CHAOS 6: PASS")
    sys.exit(0)
