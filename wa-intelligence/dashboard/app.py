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

    return templates.TemplateResponse('dashboard.html', {
        'request': request,
        'page': 'dashboard',
        'stats': stats,
        'funnel': json.dumps(funnel),
        'archetypes': json.dumps(archetypes),
        'recent_msgs': recent_msgs,
        'cost_total': cost_total,
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
    return templates.TemplateResponse('partials/_kpi_cards.html', {
        'request': request,
        'stats': stats,
        'cost_total': cost_total,
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
