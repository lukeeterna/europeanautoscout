#!/usr/bin/env python3
"""
test_e2e_full.py — Test E2E completo del sistema ARGOS
Simula l'intero ciclo: Day1 → risposta dealer → auto-reply → verifica

Esegue TUTTO autonomamente sul numero test 393314928901.
Nessun intervento umano richiesto.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import subprocess

WA_DAEMON = "http://192.168.1.2:9191"
TEST_PHONE = "393314928901"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYZER_SCRIPT = os.path.join(PROJECT_ROOT, "wa-intelligence", "response-analyzer.py")
DB_PATH_IMAC = "/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite"

# Load API key from .env
def _load_api_key():
    for env_file in [os.path.join(PROJECT_ROOT, '.env'),
                     os.path.expanduser('~/Documents/app-antigravity-auto/wa-intelligence/.env')]:
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, _, v = line.partition('=')
                        v = v.strip().strip('"').strip("'")
                        if k.strip() in ('ARGOS_API_KEY', 'WA_API_KEY') and v:
                            return v
    return os.environ.get('ARGOS_API_KEY', os.environ.get('WA_API_KEY', ''))

WA_API_KEY = _load_api_key()

PASS = 0
FAIL = 0
RESULTS = []


def log(status, msg):
    global PASS, FAIL
    icon = "✅" if status == "PASS" else "❌"
    if status == "PASS":
        PASS += 1
    else:
        FAIL += 1
    print(f"  {icon} {msg}")
    RESULTS.append((status, msg))


def log_info(msg):
    print(f"  ℹ️  {msg}")


def api_call(endpoint, payload=None):
    """Call WA daemon API with auth."""
    url = f"{WA_DAEMON}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    if WA_API_KEY:
        headers["X-API-Key"] = WA_API_KEY
    if payload:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": str(e), "code": e.code}
    except Exception as e:
        return {"error": str(e)}


def ssh_cmd(cmd, timeout=30):
    """Run command on iMac via SSH."""
    try:
        result = subprocess.run(
            ["ssh", "gianlucadistasi@192.168.1.2", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except Exception as e:
        return f"SSH_ERROR: {e}"


def run_analyzer_remote(msg_body, dealer_id="TEST_FOUNDER", dealer_name="Test Concessionaria", persona="NARCISO", step="CONTACTED"):
    """Run response-analyzer.py on iMac directly, return output."""
    # Escape quotes in message
    safe_body = msg_body.replace('"', '\\"').replace("'", "\\'")
    cmd = (
        f"cd /Users/gianlucadistasi/Documents/app-antigravity-auto/wa-intelligence && "
        f"source .env 2>/dev/null; "
        f"export $(grep -v '^#' .env | xargs) 2>/dev/null; "
        f"python3 response-analyzer.py "
        f"--msg-id test_e2e_{int(time.time())} "
        f"--msg-body \"{safe_body}\" "
        f"--dealer-id {dealer_id} "
        f"--dealer-name \"{dealer_name}\" "
        f"--persona {persona} "
        f"--step {step} "
        f"--db-path {DB_PATH_IMAC} "
        f"2>&1"
    )
    return ssh_cmd(cmd, timeout=180)


# ════════════════════════════════════════════════════════════
# TEST SUITE
# ════════════════════════════════════════════════════════════

def test_1_daemon_status():
    print("\n[TEST 1] WA Daemon Status")
    result = api_call("status")

    if result.get("status") == "OK":
        log("PASS", "Daemon raggiungibile")
    else:
        log("FAIL", f"Daemon non raggiungibile: {result}")
        return False

    if result.get("wa_status") == "connected":
        log("PASS", "WhatsApp connesso")
    else:
        log("FAIL", f"WhatsApp non connesso: {result.get('wa_status')}")
        return False

    remaining = result.get("daily_remaining", 0)
    if remaining >= 3:
        log("PASS", f"Messaggi disponibili: {remaining}")
    else:
        log("FAIL", f"Solo {remaining} messaggi disponibili, servono almeno 3")
        return False

    return True


def test_2_dealer_in_pipeline():
    print("\n[TEST 2] Dealer test in pipeline")
    result = ssh_cmd(
        f"sqlite3 {DB_PATH_IMAC} \"SELECT dealer_id, dealer_name, phone_number, persona_type, current_step FROM conversations WHERE phone_number='393314928901'\""
    )

    if "TEST_FOUNDER" in result:
        log("PASS", f"Dealer test trovato: {result}")
    else:
        log("FAIL", f"Dealer test NON in pipeline: {result}")
        return False

    return True


def test_3_send_message():
    print("\n[TEST 3] Invio messaggio WA")
    result = api_call("send", {
        "phone": TEST_PHONE,
        "message": "[TEST E2E] Messaggio di test automatico ARGOS"
    })

    if result.get("status") == "sent":
        log("PASS", f"Messaggio inviato: {result.get('msg_id')}")
    else:
        log("FAIL", f"Invio fallito: {result}")
        return False

    return True


def test_4_send_pdf():
    print("\n[TEST 4] Invio PDF dossier")
    pdf_path = os.path.join(PROJECT_ROOT, "dossiers/ARGOS_BMW_X3_2022_Stile_Car_ee60eed0.pdf")

    if not os.path.exists(pdf_path):
        log("FAIL", f"PDF non trovato: {pdf_path}")
        return False

    log_info(f"PDF size: {os.path.getsize(pdf_path) // 1024}KB")

    result = api_call("send", {
        "phone": TEST_PHONE,
        "message": "[TEST E2E] Dossier esempio BMW X3",
        "pdf": pdf_path
    })

    if result.get("status") == "sent":
        log("PASS", f"PDF inviato: {result.get('msg_id')}")
    else:
        log("FAIL", f"Invio PDF fallito: {result}")
        return False

    return True


def test_5_analyzer_curiosity():
    print("\n[TEST 5] Analyzer — risposta CURIOSITY (\"chi sei?\")")
    output = run_analyzer_remote(
        "Lei chi e, chi le ha dato il mio numero?",
        step="CONTACTED"
    )

    if "CURIOSITY" in output:
        log("PASS", "Classificazione CURIOSITY corretta")
    else:
        log("FAIL", f"Classificazione errata: {output[:200]}")

    if "qwen" in output.lower() or "gemini" in output.lower() or "LLM OK" in output:
        log("PASS", "LLM ha generato risposta")
    elif "FALLBACK" in output and "All LLM" in output:
        log("FAIL", "LLM fallito — solo template fallback")
    else:
        log_info(f"Output LLM: {output[-300:]}")
        # Check if response was sent
        if "MULTI-INVIATO" in output or "send-multi" in output or "reply_" in output:
            log("PASS", "Risposta generata e schedulata")
        else:
            log("FAIL", "Nessuna risposta generata")

    # Verifica contenuto risposta
    if "Luca" in output or "Ferretti" in output or "luca" in output:
        log("PASS", "Risposta firmata come Luca Ferretti")

    log_info(f"Output completo:\n{output[-500:]}")
    return True


def test_6_analyzer_vehicle_request():
    print("\n[TEST 6] Analyzer — risposta VEHICLE_REQUEST (\"cerco BMW X3\")")
    output = run_analyzer_remote(
        "Si mi interessa, cerco un BMW X3 2022, budget 35mila euro",
        step="CONTACTED"
    )

    if "VEHICLE_REQUEST" in output:
        log("PASS", "Classificazione VEHICLE_REQUEST corretta")
    else:
        log("FAIL", f"Classificazione errata (atteso VEHICLE_REQUEST): {output[:300]}")

    if "qwen" in output.lower() or "gemini" in output.lower() or "LLM OK" in output:
        log("PASS", "LLM ha generato risposta")
    elif "FALLBACK" in output:
        log("FAIL", "LLM fallito — solo template fallback")

    if "BMW" in output or "X3" in output or "35" in output:
        log("PASS", "Parametri veicolo estratti")

    log_info(f"Output completo:\n{output[-500:]}")
    return True


def test_7_analyzer_objection():
    print("\n[TEST 7] Analyzer — risposta OBJECTION (\"non mi interessa\")")
    output = run_analyzer_remote(
        "No guardi non mi interessa, ho gia i miei canali in Germania",
        step="CONTACTED"
    )

    has_classification = any(t in output for t in ["OBJECTION", "NEGATIVE", "REJECTION"])
    if has_classification:
        log("PASS", "Classificazione negativa corretta")
    else:
        log("FAIL", f"Classificazione errata: {output[:300]}")

    if "qwen" in output.lower() or "gemini" in output.lower() or "LLM OK" in output:
        log("PASS", "LLM ha generato risposta calibrata")

    log_info(f"Output completo:\n{output[-500:]}")
    return True


def test_8_analyzer_interest():
    print("\n[TEST 8] Analyzer — risposta INTEREST (\"mi dica di piu\")")
    output = run_analyzer_remote(
        "Interessante, mi dica di piu. Come funziona il servizio?",
        step="CONTACTED"
    )

    has_classification = any(t in output for t in ["INTEREST", "CURIOSITY", "INFO_REQUEST", "POSITIVE"])
    if has_classification:
        log("PASS", f"Classificazione corretta")
    else:
        log("FAIL", f"Classificazione: {output[:300]}")

    if "qwen" in output.lower() or "gemini" in output.lower() or "LLM OK" in output:
        log("PASS", "LLM ha generato risposta")

    log_info(f"Output completo:\n{output[-500:]}")
    return True


def test_9_full_conversation_flow():
    print("\n[TEST 9] Flow conversazione completo via WA (invio reale)")

    # Step 1: Manda Day 1
    log_info("Step 1: Invio Day 1...")
    result = api_call("send", {
        "phone": TEST_PHONE,
        "message": "Buongiorno, sono Luca Ferretti. Cerco auto premium in Germania per concessionari selezionati del Sud. Ho visto il suo posizionamento — le capita di cercare Porsche o BMW M dalla Germania?\n\nLuca"
    })
    if result.get("status") == "sent":
        log("PASS", "Day 1 inviato")
    else:
        log("FAIL", f"Day 1 fallito: {result}")
        return False

    time.sleep(3)

    # Step 2: Simula risposta dealer (via analyzer diretto)
    log_info("Step 2: Simulo risposta dealer 'chi sei?'...")
    output = run_analyzer_remote(
        "Ma lei chi e? Come ha avuto il mio numero?",
        step="CONTACTED"
    )

    if "reply_" in output:
        log("PASS", "Analyzer ha generato reply")
    else:
        log("FAIL", f"Analyzer non ha generato reply: {output[-300:]}")

    time.sleep(5)

    # Step 3: Simula secondo messaggio dealer
    log_info("Step 3: Simulo risposta dealer 'mi interessa BMW X3'...")
    output2 = run_analyzer_remote(
        "Ok ho capito. Si, cerco un BMW X3 xDrive20d 2022, budget massimo 35 mila",
        step="RESPONSE_RECEIVED"
    )

    if "VEHICLE_REQUEST" in output2:
        log("PASS", "VEHICLE_REQUEST riconosciuto")
    else:
        log("FAIL", f"VEHICLE_REQUEST non riconosciuto: {output2[:300]}")

    if "reply_" in output2:
        log("PASS", "Reply generata per vehicle request")

    return True


def test_10_pipeline_scrape_cove_pdf():
    print("\n[TEST 10] Pipeline scrape → CoVe → PDF (E2E)")
    log_info("Questo test richiede ~5 minuti. Lancio on_demand_runner...")

    cmd = (
        f"cd {PROJECT_ROOT} && timeout 360 python3 tools/on_demand_runner.py "
        f"--marca BMW --modello X3 --budget 40000 --dealer 'Test E2E' 2>&1 | tail -20"
    )
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=380
        )
        output = result.stdout
    except subprocess.TimeoutExpired:
        log("FAIL", "Pipeline timeout (>6 min)")
        return False

    if "PROCEED" in output:
        log("PASS", "CoVe ha trovato veicoli PROCEED")
    else:
        log("FAIL", f"Nessun PROCEED: {output[-300:]}")

    if "PDF" in output.upper() or ".pdf" in output:
        log("PASS", "PDF generato")
    else:
        log("FAIL", f"PDF non generato: {output[-300:]}")

    log_info(f"Output pipeline:\n{output[-400:]}")
    return True


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  ARGOS E2E TEST SUITE")
    print("  Target: 393314928901 (numero test founder)")
    print("  Modalita: AUTONOMA — nessun intervento umano")
    print("=" * 70)

    skip_slow = "--fast" in sys.argv

    # Tests sequenziali (ogni test dipende dal precedente)
    if not test_1_daemon_status():
        print("\n❌ ABORT: Daemon non funzionante")
        return

    if not test_2_dealer_in_pipeline():
        print("\n❌ ABORT: Dealer non in pipeline")
        return

    test_3_send_message()
    time.sleep(3)

    test_4_send_pdf()
    time.sleep(3)

    test_5_analyzer_curiosity()
    time.sleep(5)

    test_6_analyzer_vehicle_request()
    time.sleep(5)

    test_7_analyzer_objection()
    time.sleep(5)

    test_8_analyzer_interest()
    time.sleep(5)

    test_9_full_conversation_flow()

    if not skip_slow:
        test_10_pipeline_scrape_cove_pdf()
    else:
        print("\n[TEST 10] Pipeline scrape → CoVe → PDF — SKIPPED (--fast)")

    # ── REPORT ──
    print("\n" + "=" * 70)
    print(f"  RISULTATO: {PASS} PASS / {FAIL} FAIL")
    print("=" * 70)

    for status, msg in RESULTS:
        icon = "✅" if status == "PASS" else "❌"
        print(f"  {icon} {msg}")

    print()
    if FAIL == 0:
        print("  🟢 SISTEMA PRONTO PER DEALER REALI")
    elif FAIL <= 2:
        print("  🟡 SISTEMA PARZIALMENTE FUNZIONANTE — fix necessari")
    else:
        print("  🔴 SISTEMA NON PRONTO — troppi errori")

    print()
    return FAIL == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
