import secrets
from fastapi import Request, HTTPException

CSRF_SESSION_KEY = "csrf"

def ensure_csrf(request: Request) -> str:
    token = request.session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(24)
        request.session[CSRF_SESSION_KEY] = token
    return token

def require_csrf(request: Request, header_value: str | None):
    expected = request.session.get(CSRF_SESSION_KEY)
    if not expected or not header_value or header_value != expected:
        raise HTTPException(status_code=403, detail="Bad CSRF token")
