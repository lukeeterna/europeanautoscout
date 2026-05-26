"""
app.py -- ARGOS Dashboard (FastAPI + HTMX + Tabler)
CoVe 2026 | Enterprise Grade

AVVIO:
  cd wa-intelligence && python3 run_dashboard.py

PM2:
  pm2 start run_dashboard.py --name argos-dashboard --interpreter python3
"""

import json
import logging
import os
import subprocess

# Load .env from wa-intelligence/ (same as ecosystem.config.js)
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv not installed — env vars must be set externally
import time
from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db
from .auth import verify_password, create_session_cookie, validate_session, clear_session

log = logging.getLogger('argos.dashboard')

# ── App ──────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
app = FastAPI(title='ARGOS Dashboard', docs_url=None, redoc_url=None)

db.ensure_tables()

app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
templates = Jinja2Templates(directory=BASE_DIR / 'templates')


# ── Helpers ──────────────────────────────────────────────

def is_htmx(request: Request) -> bool:
    return request.headers.get('HX-Request') == 'true'


def _auth_or_redirect(request: Request):
    if not validate_session(request):
        return RedirectResponse(url='/login', status_code=303)
    return None


def _require_auth_api(request: Request):
    """Returns JSONResponse 401 if not authenticated, else None."""
    if not validate_session(request):
        return JSONResponse({'error': 'unauthorized'}, status_code=401)
    return None


# ── Auth Routes ──────────────────────────────────────────

@app.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request, 'error': None})


@app.post('/login')
async def login_submit(request: Request, password: str = Form(...)):
    if verify_password(password):
        response = RedirectResponse(url='/', status_code=303)
        return create_session_cookie(response)
    return templates.TemplateResponse('login.html', {
        'request': request,
        'error': 'Password non valida',
    })


@app.get('/logout')
async def logout():
    response = RedirectResponse(url='/login', status_code=303)
    return clear_session(response)


# ── Dashboard ────────────────────────────────────────────

@app.get('/', response_class=HTMLResponse)
async def dashboard(request: Request):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    stats = db.get_pipeline_stats()
    funnel = db.get_funnel_data()
    archetypes = db.get_archetype_distribution()
    recent_msgs = db.get_all_recent_messages(10)
    cost_total = db.get_llm_cost_total()
    ops = db.get_operational_kpis()
    wa_status = {}
    try:
        import urllib.request as _ur
        req = _ur.Request('http://localhost:9191/status',
                          headers={'X-API-Key': os.environ.get('ARGOS_API_KEY', '')})
        wa_status = json.loads(_ur.urlopen(req, timeout=2).read())
    except Exception:
        pass

    return templates.TemplateResponse('dashboard.html', {
        'request': request,
        'page': 'dashboard',
        'stats': stats,
        'funnel': json.dumps(funnel),
        'archetypes': json.dumps(archetypes),
        'recent_msgs': recent_msgs,
        'cost_total': cost_total,
        'ops': ops,
        'wa': wa_status,
    })


# ── Pipeline ─────────────────────────────────────────────

@app.get('/pipeline', response_class=HTMLResponse)
async def pipeline(request: Request):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    dealers = db.get_dealers()

    if is_htmx(request):
        return templates.TemplateResponse('partials/_dealer_table.html', {
            'request': request,
            'dealers': dealers,
        })

    return templates.TemplateResponse('pipeline.html', {
        'request': request,
        'page': 'pipeline',
        'dealers': dealers,
    })


# ── Conversazioni ────────────────────────────────────────

@app.get('/conversations', response_class=HTMLResponse)
async def conversations(request: Request):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    dealers = db.get_dealers()
    pending = db.get_pending_replies()

    return templates.TemplateResponse('conversations.html', {
        'request': request,
        'page': 'conversations',
        'dealers': dealers,
        'pending': pending,
    })


@app.get('/conversations/{dealer_id}', response_class=HTMLResponse)
async def conversation_detail(request: Request, dealer_id: str):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    dealer = db.get_dealer(dealer_id)
    if not dealer:
        return RedirectResponse(url='/conversations', status_code=303)

    messages = db.get_messages(dealer_id)
    pending = db.get_pending_replies_for_dealer(dealer_id)

    return templates.TemplateResponse('conversation_detail.html', {
        'request': request,
        'page': 'conversations',
        'dealer': dealer,
        'messages': messages,
        'pending': pending,
    })


# ── CRM ─────────────────────────────────────────────

@app.get('/crm', response_class=HTMLResponse)
async def crm(request: Request):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    dealers = db.get_crm_dealers()
    stats = db.get_crm_pipeline_stats()

    return templates.TemplateResponse('crm.html', {
        'request': request,
        'page': 'crm',
        'dealers': dealers,
        'stats': stats,
    })


@app.get('/crm/{dealer_id}', response_class=HTMLResponse)
async def crm_detail(request: Request, dealer_id: str):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    dealer = db.get_crm_dealer(dealer_id)
    if not dealer:
        return RedirectResponse(url='/crm', status_code=303)

    interactions = db.get_crm_interactions(dealer_id)
    vehicles = db.get_crm_vehicles(dealer_id)

    return templates.TemplateResponse('crm_detail.html', {
        'request': request,
        'page': 'crm',
        'dealer': dealer,
        'interactions': interactions,
        'vehicles': vehicles,
    })


# ── Vehicle Pipeline ─────────────────────────────────────

@app.get('/vehicles', response_class=HTMLResponse)
async def vehicles(request: Request):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    pipeline_data = _get_vehicle_pipeline_data()

    return templates.TemplateResponse('vehicles.html', {
        'request': request,
        'page': 'vehicles',
        'summary': pipeline_data['summary'],
        'vehicles': pipeline_data['vehicles'],
        'log_recent': pipeline_data['log_recent'],
    })


@app.get('/api/vehicle-pipeline')
async def api_vehicle_pipeline(request: Request):
    err = _require_auth_api(request)
    if err:
        return err
    return _get_vehicle_pipeline_data()


@app.post('/api/actions/run-pipeline')
async def action_run_pipeline(request: Request):
    """Trigger a pipeline orchestrator dry-run."""
    err = _require_auth_api(request)
    if err:
        return err
    body = await request.json()
    dry_run = body.get('dry_run', True)
    try:
        cmd = ['python3', str(Path(__file__).parent.parent.parent / 'src' / 'cove' / 'pipeline_orchestrator.py')]
        if dry_run:
            cmd.append('--dry-run')
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                                env={**os.environ, 'ARGOS_DB_PATH': str(Path(__file__).parent.parent.parent / 'dealer_network.sqlite')})
        return {'ok': True, 'output': result.stdout[-3000:], 'stderr': result.stderr[-1000:] if result.stderr else ''}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': 'Pipeline timeout (120s)'}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


def _get_vehicle_pipeline_data() -> dict:
    """Get vehicle pipeline data from DuckDB."""
    try:
        import duckdb
        db_path = str(Path(__file__).parent.parent.parent / 'src' / 'cove' / 'data' / 'cove_tracker.duckdb')
        con = duckdb.connect(db_path, read_only=True)

        # Summary by state
        summary_rows = con.execute("""
            SELECT pipeline_state, COUNT(*) as cnt
            FROM vehicle_listings
            GROUP BY pipeline_state
            ORDER BY cnt DESC
        """).fetchall()
        summary = {r[0]: r[1] for r in summary_rows}

        # Vehicles with details (non-terminal, most recent first)
        vehicles = con.execute("""
            SELECT vl.listing_id, vl.make, vl.model, vl.year, vl.mileage, vl.price_eu,
                   vl.pipeline_state, vl.state_updated_at, vl.matched_dealer, vl.dossier_path,
                   vl.seller_email, vl.seller_followup_count, vl.image_count,
                   cr.confidence, cr.fraud_overall, cr.market_price, cr.recommendation
            FROM vehicle_listings vl
            LEFT JOIN cove_results cr ON vl.listing_id = cr.listing_id
            WHERE vl.pipeline_state NOT IN ('REJECTED')
            ORDER BY
                CASE vl.pipeline_state
                    WHEN 'DOSSIER_READY' THEN 1
                    WHEN 'DATA_COMPLETE' THEN 2
                    WHEN 'SELLER_CONTACTED' THEN 3
                    WHEN 'ENRICHED' THEN 4
                    WHEN 'SCORED' THEN 5
                    WHEN 'DISCOVERED' THEN 6
                    ELSE 7
                END,
                vl.state_updated_at DESC NULLS LAST
            LIMIT 100
        """).fetchall()

        vehicle_list = []
        for v in vehicles:
            margin = 0
            if v[15] and v[5]:  # market_price and price_eu
                margin = float(v[15]) - float(v[5]) - 1200 - 430 - 900
            vehicle_list.append({
                'listing_id': v[0], 'make': v[1], 'model': v[2], 'year': v[3],
                'km': f"{v[4]:,}" if v[4] else '?',
                'price_eu': f"{int(v[5]):,}" if v[5] else '?',
                'state': v[6], 'updated': str(v[7])[:16] if v[7] else '',
                'dealer': v[8] or '', 'dossier': v[9] or '',
                'seller_email': v[10] or '', 'followups': v[11] or 0,
                'photos': v[12] or 0,
                'confidence': f"{v[13]:.0%}" if v[13] else '?',
                'fraud': v[14] or '?',
                'market_it': f"{int(v[15]):,}" if v[15] else '?',
                'margin': f"{int(margin):,}" if margin else '?',
                'recommendation': v[16] or '?',
            })

        # Recent log
        log_recent = []
        try:
            log_rows = con.execute("""
                SELECT listing_id, from_state, to_state, action, created_at
                FROM pipeline_log
                ORDER BY created_at DESC
                LIMIT 20
            """).fetchall()
            for lr in log_rows:
                log_recent.append({
                    'listing_id': lr[0], 'from': lr[1] or '-', 'to': lr[2],
                    'action': lr[3], 'time': str(lr[4])[:16] if lr[4] else '',
                })
        except Exception:
            pass

        con.close()
        return {'summary': summary, 'vehicles': vehicle_list, 'log_recent': log_recent}
    except Exception as e:
        return {'summary': {}, 'vehicles': [], 'log_recent': [], 'error': str(e)}


# ── Vehicle Dossier (view/generate PDF) ──────────────────

@app.get('/vehicles/{listing_id}/dossier')
async def vehicle_dossier(request: Request, listing_id: str):
    """Serve existing PDF or generate on-the-fly."""
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    from fastapi.responses import FileResponse

    dossier_dir = Path(__file__).parent.parent.parent / 'dossiers'

    # Check if PDF already exists in DB path or by pattern
    import duckdb
    db_path = str(Path(__file__).parent.parent.parent / 'src' / 'cove' / 'data' / 'cove_tracker.duckdb')

    existing_pdf = None
    try:
        con = duckdb.connect(db_path, read_only=True)
        row = con.execute("SELECT dossier_path FROM vehicle_listings WHERE listing_id = ?", [listing_id]).fetchone()
        if row and row[0] and os.path.exists(row[0]):
            existing_pdf = row[0]
        con.close()
    except Exception:
        pass

    # Fallback: search by pattern in dossiers/
    if not existing_pdf:
        for f in dossier_dir.glob(f"*{listing_id[:12]}*.pdf"):
            existing_pdf = str(f)
            break
        # Also check with make/model pattern
        if not existing_pdf:
            try:
                con = duckdb.connect(db_path, read_only=True)
                vrow = con.execute("SELECT make, model, year FROM cove_results WHERE listing_id = ?", [listing_id]).fetchone()
                con.close()
                if vrow:
                    for f in dossier_dir.glob(f"ARGOS_{vrow[0]}_{vrow[1]}_{vrow[2]}_*.pdf"):
                        existing_pdf = str(f)
                        break
            except Exception:
                pass

    if existing_pdf and os.path.exists(existing_pdf):
        return FileResponse(existing_pdf, media_type='application/pdf',
                            filename=os.path.basename(existing_pdf))

    # PDF doesn't exist — generate it now
    try:
        import sys as _sys
        scripts_dir = str(Path(__file__).parent.parent.parent / 'tools' / 'scripts')
        if scripts_dir not in _sys.path:
            _sys.path.insert(0, scripts_dir)
        repo_root = str(Path(__file__).parent.parent.parent)
        if repo_root not in _sys.path:
            _sys.path.insert(0, repo_root)
        from pdf_generator_enterprise import generate_dossier_from_db

        output_dir = str(dossier_dir)
        pdf_path = generate_dossier_from_db(listing_id, "ARGOS Preview", output_dir, db_path)

        if pdf_path and os.path.exists(pdf_path):
            # Store path in DB
            try:
                con = duckdb.connect(db_path)
                con.execute("UPDATE vehicle_listings SET dossier_path = ? WHERE listing_id = ?", [pdf_path, listing_id])
                con.close()
            except Exception:
                pass
            return FileResponse(pdf_path, media_type='application/pdf',
                                filename=os.path.basename(pdf_path))
        else:
            return JSONResponse({'error': 'PDF generation failed'}, status_code=500)
    except Exception as e:
        return JSONResponse({'error': f'PDF generation error: {str(e)}'}, status_code=500)


# ── Finance ──────────────────────────────────────────────

@app.get('/finance', response_class=HTMLResponse)
async def finance(request: Request):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    costs = db.get_llm_costs(30)
    cost_total = db.get_llm_cost_total()
    dealers = db.get_dealers()

    return templates.TemplateResponse('finance.html', {
        'request': request,
        'page': 'finance',
        'costs': json.dumps(costs),
        'cost_total': cost_total,
        'dealer_count': len(dealers),
    })


# ── Contracts (S152) ─────────────────────────────────────
# Proxy admin a argos-proxy Worker. Bonifico bancario manuale:
#   AWAITING_DELIVERY → "Invia IBAN" → IBAN_SENT
#   IBAN_SENT         → "Mark PAID"  → PAID

ARGOS_PROXY_URL    = os.environ.get('ARGOS_PROXY_URL', '')
ARGOS_ADMIN_SECRET = os.environ.get('ARGOS_ADMIN_SECRET', '')


def _proxy_request(path: str, method: str = 'GET', body: dict | None = None,
                   timeout: int = 10) -> tuple[int, dict | None, str | None]:
    """Call argos-proxy with admin Bearer. Returns (status, json|None, error|None)."""
    import urllib.request
    import urllib.error
    if not ARGOS_PROXY_URL or not ARGOS_ADMIN_SECRET:
        return 0, None, 'ARGOS_PROXY_URL or ARGOS_ADMIN_SECRET not configured'
    url = f'{ARGOS_PROXY_URL.rstrip("/")}{path}'
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {ARGOS_ADMIN_SECRET}',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8')), None
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode('utf-8'))
            return e.code, payload, payload.get('error', f'HTTP {e.code}')
        except Exception:
            return e.code, None, f'HTTP {e.code}'
    except Exception as e:
        return 0, None, f'request failed: {e}'


@app.get('/contracts', response_class=HTMLResponse)
async def contracts_list(request: Request):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    status, payload, err = _proxy_request('/api/v1/admin/contracts?limit=50')
    contracts = []
    proxy_error = None
    if err:
        proxy_error = err
    elif payload:
        contracts = payload.get('contracts', [])

    return templates.TemplateResponse('contracts.html', {
        'request': request,
        'page': 'contracts',
        'contracts': contracts,
        'proxy_error': proxy_error,
        'action_result': None,
    })


@app.post('/contracts/{contract_id}/send-iban')
async def contracts_send_iban(request: Request, contract_id: str):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    status, payload, err = _proxy_request(
        f'/api/v1/contract/{contract_id}/send-iban',
        method='POST',
        body={},
    )
    if err:
        log.warning(f'send-iban {contract_id} failed: {err} payload={payload}')
    else:
        log.info(f'send-iban {contract_id} ok: {payload}')
    return RedirectResponse(url='/contracts', status_code=303)


@app.post('/contracts/{contract_id}/mark-paid')
async def contracts_mark_paid(
    request: Request,
    contract_id: str,
    paid_amount_eur: float = Form(...),
    payment_bank: str = Form(...),
    payment_reference: str = Form(...),
):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    paid_cents = int(round(paid_amount_eur * 100))
    status, payload, err = _proxy_request(
        f'/api/v1/contract/{contract_id}/mark-paid',
        method='POST',
        body={
            'paid_amount_cents': paid_cents,
            'payment_bank': payment_bank,
            'payment_reference': payment_reference,
        },
    )
    if err:
        log.warning(f'mark-paid {contract_id} failed: {err} payload={payload}')
    else:
        log.info(f'mark-paid {contract_id} ok: {payload}')
    return RedirectResponse(url='/contracts', status_code=303)


# ── System Health ────────────────────────────────────────

@app.get('/system', response_class=HTMLResponse)
async def system(request: Request):
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    pm2_status = []
    try:
        raw = subprocess.run(
            ['pm2', 'jlist'],
            capture_output=True, text=True, timeout=5
        )
        if raw.returncode == 0:
            for proc in json.loads(raw.stdout):
                pm2_status.append({
                    'name': proc.get('name', '?'),
                    'status': proc.get('pm2_env', {}).get('status', '?'),
                    'memory': round(proc.get('monit', {}).get('memory', 0) / 1024 / 1024, 1),
                    'uptime': proc.get('pm2_env', {}).get('pm_uptime', 0),
                    'restarts': proc.get('pm2_env', {}).get('restart_time', 0),
                })
    except Exception:
        pass

    db_stats = db.get_db_stats()
    audit = db.get_recent_audit(20)

    # WA session status — dal daemon direttamente
    health = _daemon_status()
    wa_status = health.get('wa_status', 'offline')
    wa_session_active = wa_status == 'connected'
    qr_state = _daemon_qr()
    wa_auth_running = qr_state.get('status') == 'waiting_scan'

    return templates.TemplateResponse('system.html', {
        'request': request,
        'page': 'system',
        'pm2_status': pm2_status,
        'db_stats': db_stats,
        'audit': audit,
        'wa_session_active': wa_session_active,
        'wa_auth_running': wa_auth_running,
        'wa_status': wa_status,
    })


# ── HTMX Partials (auto-refresh) ────────────────────────

@app.get('/partials/kpi', response_class=HTMLResponse)
async def partial_kpi(request: Request):
    if not validate_session(request):
        return HTMLResponse('')
    stats = db.get_pipeline_stats()
    cost_total = db.get_llm_cost_total()
    ops = db.get_operational_kpis()
    # WA daemon status (best-effort)
    wa_status = {}
    try:
        import urllib.request as _ur
        req = _ur.Request('http://localhost:9191/status',
                          headers={'X-API-Key': os.environ.get('ARGOS_API_KEY', '')})
        import json as _json
        wa_status = _json.loads(_ur.urlopen(req, timeout=2).read())
    except Exception:
        pass
    return templates.TemplateResponse('partials/_kpi_cards.html', {
        'request': request,
        'stats': stats,
        'cost_total': cost_total,
        'ops': ops,
        'wa': wa_status,
    })


@app.get('/partials/messages', response_class=HTMLResponse)
async def partial_messages(request: Request):
    if not validate_session(request):
        return HTMLResponse('')
    recent_msgs = db.get_all_recent_messages(10)
    return templates.TemplateResponse('partials/_message_feed.html', {
        'request': request,
        'recent_msgs': recent_msgs,
    })


# ── JSON API (read-only) ────────────────────────────────

@app.get('/api/pipeline')
async def api_pipeline(request: Request):
    err = _require_auth_api(request)
    if err:
        return err
    return db.get_dealers()


@app.get('/api/stats')
async def api_stats(request: Request):
    err = _require_auth_api(request)
    if err:
        return err
    return {
        'pipeline': db.get_pipeline_stats(),
        'funnel': db.get_funnel_data(),
        'archetypes': db.get_archetype_distribution(),
        'costs': db.get_llm_cost_total(),
        'db': db.get_db_stats(),
    }


# ── F5: Action Endpoints ────────────────────────────────

@app.post('/api/actions/approve-reply')
async def action_approve_reply(request: Request):
    err = _require_auth_api(request)
    if err:
        return err
    body = await request.json()
    reply_id = body.get('reply_id')
    if not reply_id:
        return JSONResponse({'error': 'reply_id required'}, status_code=400)
    ok = db.approve_reply(int(reply_id))
    if ok:
        log.info(f'Reply {reply_id} approved from dashboard')
    return {'ok': ok}


@app.post('/api/actions/skip-reply')
async def action_skip_reply(request: Request):
    err = _require_auth_api(request)
    if err:
        return err
    body = await request.json()
    reply_id = body.get('reply_id')
    if not reply_id:
        return JSONResponse({'error': 'reply_id required'}, status_code=400)
    ok = db.skip_reply(int(reply_id))
    if ok:
        log.info(f'Reply {reply_id} skipped from dashboard')
    return {'ok': ok}


@app.post('/api/actions/add-note')
async def action_add_note(request: Request):
    err = _require_auth_api(request)
    if err:
        return err
    body = await request.json()
    dealer_id = body.get('dealer_id')
    note = body.get('note', '').strip()
    if not dealer_id or not note:
        return JSONResponse({'error': 'dealer_id and note required'}, status_code=400)
    ok = db.update_dealer_note(dealer_id, note)
    return {'ok': ok}


@app.post('/api/actions/send-day1')
async def action_send_day1(request: Request):
    """Segna dealer come DAY1_SENT. L'invio effettivo avviene via wa-daemon."""
    err = _require_auth_api(request)
    if err:
        return err
    body = await request.json()
    dealer_id = body.get('dealer_id')
    if not dealer_id:
        return JSONResponse({'error': 'dealer_id required'}, status_code=400)
    dealer = db.get_dealer(dealer_id)
    if not dealer:
        return JSONResponse({'error': 'dealer not found'}, status_code=404)
    if dealer.get('current_step', '') != 'PENDING':
        return JSONResponse({'error': f'dealer step is {dealer.get("current_step")}, not PENDING'}, status_code=409)
    ok = db.update_dealer_step(dealer_id, 'DAY1_SENT')
    if ok:
        log.info(f'Day 1 triggered for {dealer_id} from dashboard')
    return {'ok': ok, 'dealer_id': dealer_id}


# ── WA Auth (proxy al daemon :9191) ──────────────────────

DAEMON_URL = 'http://127.0.0.1:9191'


def _daemon_status():
    """Ottieni stato dal daemon WA (health + qr)."""
    import urllib.request
    try:
        req = urllib.request.Request(f'{DAEMON_URL}/', headers={'Accept': 'application/json'})
        resp = urllib.request.urlopen(req, timeout=3)
        return json.loads(resp.read())
    except Exception:
        return {'status': 'offline', 'wa_status': 'offline'}


def _daemon_qr():
    """Ottieni QR state dal daemon."""
    import urllib.request
    try:
        req = urllib.request.Request(f'{DAEMON_URL}/qr', headers={'Accept': 'application/json'})
        resp = urllib.request.urlopen(req, timeout=3)
        return json.loads(resp.read())
    except Exception:
        return {'status': 'offline', 'qr': None}


@app.get('/api/wa-session-status')
async def wa_session_status(request: Request):
    """Check WA session status via daemon :9191."""
    err = _require_auth_api(request)
    if err:
        return err

    health = _daemon_status()
    qr_state = _daemon_qr()

    return {
        'daemon_online': health.get('status') == 'OK',
        'wa_status': health.get('wa_status', 'unknown'),
        'session_active': health.get('wa_status') == 'connected',
        'qr_available': qr_state.get('status') == 'waiting_scan',
        'auth_running': qr_state.get('status') == 'waiting_scan',
    }


@app.get('/wa-qr', response_class=HTMLResponse)
async def wa_qr_page(request: Request):
    """Pagina QR auth — proxy dal daemon :9191/qr."""
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect

    import urllib.request
    try:
        resp = urllib.request.urlopen(f'{DAEMON_URL}/qr', timeout=5)
        html = resp.read().decode('utf-8')
        return HTMLResponse(html)
    except Exception as e:
        return HTMLResponse(f'<html><body style="background:#1a1a2e;color:#ff4444;font-family:monospace;padding:40px">'
                          f'<h2>Daemon WA offline</h2><p>{e}</p>'
                          f'<p>Verifica che wa-daemon sia attivo: pm2 status argos-wa-daemon</p></body></html>')


@app.post('/api/actions/wa-auth-start')
async def wa_auth_start(request: Request):
    """Redirect al QR del daemon — nessun processo separato."""
    err = _require_auth_api(request)
    if err:
        return err

    health = _daemon_status()
    if health.get('status') != 'OK':
        return JSONResponse({'error': 'Daemon WA offline. Avvia con: pm2 start argos-wa-daemon'}, status_code=503)

    db.write_audit('WA_AUTH_STARTED', None, '{"method": "daemon-qr"}')
    return {'ok': True, 'message': 'QR disponibile dal daemon', 'redirect': '/wa-qr'}


@app.post('/api/actions/wa-auth-stop')
async def wa_auth_stop(request: Request):
    """Non serve più — il daemon gestisce tutto."""
    err = _require_auth_api(request)
    if err:
        return err
    return {'ok': True, 'message': 'Il daemon gestisce la sessione autonomamente'}


# ── Health & Monitoring (NO AUTH) ────────────────────────

_START_TIME = time.time()


@app.get('/health')
async def health():
    """Health check — no auth. Per PM2, Uptime Robot, cron."""
    try:
        stats = db.get_pipeline_stats()
        db_ok = True
    except Exception:
        stats = {}
        db_ok = False

    pm2_ok = False
    try:
        r = subprocess.run(['pm2', 'ping'], capture_output=True, timeout=3)
        pm2_ok = r.returncode == 0
    except Exception:
        pass

    uptime_s = int(time.time() - _START_TIME)
    return {
        'status': 'healthy' if db_ok else 'degraded',
        'uptime_seconds': uptime_s,
        'db': db_ok,
        'pm2': pm2_ok,
        'dealers': stats.get('total_dealers', 0),
        'messages': stats.get('total_messages', 0),
        'pending': stats.get('pending_replies', 0),
    }


@app.get('/api/logs')
async def api_logs(request: Request):
    """Ultimi log PM2 per ogni processo. Richiede auth."""
    err = _require_auth_api(request)
    if err:
        return err

    result = {}
    for name in ['argos-dashboard', 'argos-tg-bot', 'argos-wa-daemon']:
        try:
            r = subprocess.run(
                ['pm2', 'logs', name, '--nostream', '--lines', '30'],
                capture_output=True, text=True, timeout=5
            )
            result[name] = r.stdout[-2000:] if r.stdout else r.stderr[-2000:]
        except Exception as e:
            result[name] = f'Error: {e}'

    return result


@app.get('/api/audit')
async def api_audit(request: Request):
    """Ultimi 50 eventi audit log. Richiede auth."""
    err = _require_auth_api(request)
    if err:
        return err
    return db.get_recent_audit(50)


# ── HITL Dossier Approval (S189 + S190 fix code-review MED-3/MED-4) ──

_APPROVALS_LOG = Path.home() / 'Documents/app-antigravity-auto/logs/approvals.jsonl'
# Confinement directory per /dossier/{id}/preview — anti path-traversal
_DOSSIERS_BASE = (Path.home() / 'Documents/app-antigravity-auto/dossiers').resolve()


def _write_approval_audit(action: str, dossier_id: int, **extra) -> None:
    """Scrive entry audit su file JSONL per dossier approve/reject.
    Flush + fsync per durability su power-loss/OOM (fix code-review MED-4).
    """
    _APPROVALS_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {'ts': int(time.time()), 'action': action, 'dossier_id': dossier_id, **extra}
    with open(_APPROVALS_LOG, 'a') as fh:
        fh.write(json.dumps(entry) + '\n')
        fh.flush()
        os.fsync(fh.fileno())


def _get_pending_dossiers() -> list[dict]:
    """Lista dossier PENDING dalla tabella dossiers."""
    return db.query(
        "SELECT id, dealer_id, file_path, created_ts "
        "FROM dossiers WHERE approval_status = 'PENDING' ORDER BY created_ts ASC LIMIT 50"
    )


def _get_dossier_by_id(dossier_id: int) -> dict | None:
    """Singolo dossier per id."""
    return db.query_one("SELECT * FROM dossiers WHERE id = ?", (dossier_id,))


def _update_dossier_status(
    dossier_id: int,
    status: str,
    reject_reason: str | None = None,
) -> int:
    """Aggiorna approval_status dossier. Ritorna rowcount."""
    con = db._connect()
    try:
        ts = int(time.time())
        if reject_reason is not None:
            cur = con.execute(
                "UPDATE dossiers SET approval_status=?, approval_ts=?, reject_reason=? "
                "WHERE id=? AND approval_status='PENDING'",
                (status, ts, reject_reason, dossier_id),
            )
        else:
            cur = con.execute(
                "UPDATE dossiers SET approval_status=?, approval_ts=? "
                "WHERE id=? AND approval_status='PENDING'",
                (status, ts, dossier_id),
            )
        con.commit()
        return cur.rowcount
    finally:
        con.close()


@app.get('/pending-dossiers', response_class=HTMLResponse)
async def pending_dossiers(request: Request):
    """Pagina HITL: lista dossier PDF in attesa di approvazione Luke."""
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect
    dossiers = _get_pending_dossiers()
    return templates.TemplateResponse('pending_dossiers.html', {
        'request': request,
        'page': 'pending_dossiers',
        'dossiers': dossiers,
    })


@app.get('/dossier/{dossier_id}/preview')
async def dossier_preview(dossier_id: int, request: Request):
    """Serve PDF dossier come inline per iframe preview.
    Path traversal defense (fix code-review MED-3): file_path must resolve
    inside _DOSSIERS_BASE — even though DB-stored, originating /send-doc caller
    could register arbitrary paths.
    """
    redirect = _auth_or_redirect(request)
    if redirect:
        return redirect
    from fastapi.responses import FileResponse
    row = _get_dossier_by_id(dossier_id)
    if not row:
        return JSONResponse({'error': 'dossier not found'}, status_code=404)
    file_path = row.get('file_path', '')
    if not file_path:
        return JSONResponse({'error': 'file_path missing'}, status_code=404)
    try:
        resolved = Path(file_path).resolve(strict=True)
    except (OSError, RuntimeError):
        return JSONResponse({'error': 'file not found on disk'}, status_code=404)
    # is_relative_to is Python 3.9+ — confine inside _DOSSIERS_BASE
    try:
        resolved.relative_to(_DOSSIERS_BASE)
    except ValueError:
        log.warning(f'Path traversal blocked: dossier {dossier_id} file_path={file_path!r}')
        return JSONResponse({'error': 'path outside allowed directory'}, status_code=403)
    return FileResponse(str(resolved), media_type='application/pdf')


@app.post('/api/dossier/{dossier_id}/approve')
async def approve_dossier(dossier_id: int, request: Request):
    """HITL approve: imposta APPROVED + scrive audit."""
    err = _require_auth_api(request)
    if err:
        return err
    rowcount = _update_dossier_status(dossier_id, 'APPROVED')
    if rowcount == 0:
        return JSONResponse({'error': 'already actioned or not found'}, status_code=409)
    _write_approval_audit('approve', dossier_id)
    db.write_audit('DOSSIER_APPROVED', None, json.dumps({'dossier_id': dossier_id}))
    log.info(f'Dossier {dossier_id} APPROVED from HITL dashboard')
    return JSONResponse({'status': 'approved', 'dossier_id': dossier_id})


@app.post('/api/dossier/{dossier_id}/reject')
async def reject_dossier(dossier_id: int, request: Request):
    """HITL reject: richiede reason, imposta REJECTED + scrive audit."""
    err = _require_auth_api(request)
    if err:
        return err
    body = await request.json()
    reason = body.get('reason', '').strip()[:500]
    if not reason:
        return JSONResponse({'error': 'reason required'}, status_code=400)
    rowcount = _update_dossier_status(dossier_id, 'REJECTED', reject_reason=reason)
    if rowcount == 0:
        return JSONResponse({'error': 'already actioned or not found'}, status_code=409)
    _write_approval_audit('reject', dossier_id, reason=reason)
    db.write_audit('DOSSIER_REJECTED', None, json.dumps({'dossier_id': dossier_id, 'reason': reason}))
    log.info(f'Dossier {dossier_id} REJECTED from HITL dashboard: {reason}')
    return JSONResponse({'status': 'rejected', 'dossier_id': dossier_id})
