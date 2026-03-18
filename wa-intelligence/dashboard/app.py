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

    # WA session status
    session_dir = Path.home() / 'Documents' / 'app-antigravity-auto' / 'wa-sender' / '.wwebjs_auth' / 'session-argos-business'
    wa_session_active = session_dir.exists() and any(session_dir.iterdir()) if session_dir.exists() else False
    wa_auth_running = _wa_auth_process is not None and _wa_auth_process.poll() is None

    return templates.TemplateResponse('system.html', {
        'request': request,
        'page': 'system',
        'pm2_status': pm2_status,
        'db_stats': db_stats,
        'audit': audit,
        'wa_session_active': wa_session_active,
        'wa_auth_running': wa_auth_running,
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


# ── WA Auth ──────────────────────────────────────────────

_wa_auth_process = None


@app.get('/api/wa-session-status')
async def wa_session_status(request: Request):
    """Check WA session status. Richiede auth."""
    err = _require_auth_api(request)
    if err:
        return err

    session_dir = Path.home() / 'Documents' / 'app-antigravity-auto' / 'wa-sender' / '.wwebjs_auth' / 'session-argos-business'
    session_exists = session_dir.exists() and any(session_dir.iterdir()) if session_dir.exists() else False

    global _wa_auth_process
    auth_running = _wa_auth_process is not None and _wa_auth_process.poll() is None

    return {
        'session_active': session_exists,
        'auth_running': auth_running,
    }


@app.post('/api/actions/wa-auth-start')
async def wa_auth_start(request: Request):
    """Avvia QR auth server su porta 8765."""
    err = _require_auth_api(request)
    if err:
        return err

    global _wa_auth_process

    if _wa_auth_process is not None and _wa_auth_process.poll() is None:
        return {'ok': True, 'message': 'Auth già in corso', 'port': 8765}

    # Kill any existing process on port 8765
    try:
        subprocess.run(['lsof', '-ti:8765'], capture_output=True, text=True, timeout=3)
        subprocess.run('lsof -ti:8765 | xargs kill -9', shell=True, timeout=3)
    except Exception:
        pass

    auth_script = Path.home() / 'Documents' / 'app-antigravity-auto' / 'wa-intelligence' / 'auth-qr-server.js'
    if not auth_script.exists():
        return JSONResponse({'error': 'auth-qr-server.js not found'}, status_code=404)

    # Kill stale Chromium sessions that block whatsapp-web.js
    session_lock = Path.home() / 'Documents' / 'app-antigravity-auto' / 'wa-sender' / 'session-argos-business' / 'SingletonLock'
    if session_lock.exists():
        session_lock.unlink(missing_ok=True)

    # Find node binary
    node_bin = '/usr/local/bin/node'
    if not Path(node_bin).exists():
        node_bin = 'node'

    try:
        _wa_auth_process = subprocess.Popen(
            [node_bin, str(auth_script)],
            stdout=open('/tmp/wa_qr_http.log', 'w'),
            stderr=subprocess.STDOUT,
            cwd=str(auth_script.parent),
        )
        db.write_audit('WA_AUTH_STARTED', None, '{"method": "dashboard"}')
        return {'ok': True, 'message': 'QR server avviato', 'port': 8765}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@app.post('/api/actions/wa-auth-stop')
async def wa_auth_stop(request: Request):
    """Ferma il QR auth server."""
    err = _require_auth_api(request)
    if err:
        return err

    global _wa_auth_process
    if _wa_auth_process is not None:
        _wa_auth_process.terminate()
        _wa_auth_process = None

    try:
        subprocess.run('lsof -ti:8765 | xargs kill -9', shell=True, timeout=3)
    except Exception:
        pass

    return {'ok': True}


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
