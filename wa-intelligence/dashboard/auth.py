"""
auth.py -- ARGOS Dashboard Authentication (Single User)
CoVe 2026 | Enterprise Grade

Autenticazione minimale: password singola + cookie session firmato.
Per produzione con Cloudflare Access, questo diventa un fallback locale.
"""

import os
import secrets
from functools import wraps

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# Password dashboard (da .env, fallback per dev)
DASHBOARD_PASSWORD = os.environ.get('ARGOS_DASHBOARD_PASSWORD', 'argos2026')
SECRET_KEY = os.environ.get('ARGOS_SECRET_KEY', secrets.token_hex(32))
SESSION_MAX_AGE = 86400 * 7  # 7 giorni

_serializer = URLSafeTimedSerializer(SECRET_KEY)
COOKIE_NAME = 'argos_session'


def verify_password(password: str) -> bool:
    """Verifica password (confronto costante per evitare timing attack)."""
    return secrets.compare_digest(password, DASHBOARD_PASSWORD)


def create_session_cookie(response: Response) -> Response:
    """Imposta cookie di sessione firmato."""
    token = _serializer.dumps({'user': 'founder', 'auth': True})
    is_https = os.environ.get('ARGOS_HTTPS', '0') == '1'
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite='lax',
        secure=is_https,
    )
    return response


def validate_session(request: Request) -> bool:
    """Verifica se il cookie di sessione e' valido."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return False
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data.get('auth') is True
    except (BadSignature, SignatureExpired):
        return False


def clear_session(response: Response) -> Response:
    """Rimuove cookie di sessione."""
    response.delete_cookie(COOKIE_NAME)
    return response


def require_auth(func):
    """Decorator per proteggere endpoint."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if not validate_session(request):
            return RedirectResponse(url='/login', status_code=303)
        return await func(request, *args, **kwargs)
    return wrapper
