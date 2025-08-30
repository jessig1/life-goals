from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import secrets

from app.core.config import settings
from app.services.todoist import AUTH_URL, exchange_code_for_token

router = APIRouter(prefix="/api", tags=["auth"])

@router.get("/login")
def login(request: Request):
    state = secrets.token_urlsafe(24)
    request.session["oauth_state"] = state
    scope = "data:read_write"  # read+write
    url = f"{AUTH_URL}?{urlencode({'client_id': settings.TODOIST_CLIENT_ID,'scope': scope,'state': state,'redirect_uri': settings.TODOIST_REDIRECT_URI})}"
    return RedirectResponse(url, status_code=302)

@router.get("/oauth/callback")
async def oauth_callback(request: Request, code: str | None = None, state: str | None = None):
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state")
    saved = request.session.get("oauth_state")
    if not saved or saved != state:
        raise HTTPException(status_code=400, detail="Invalid state")
    token = await exchange_code_for_token(
        settings.TODOIST_CLIENT_ID, settings.TODOIST_CLIENT_SECRET, code, settings.TODOIST_REDIRECT_URI
    )
    request.session["todoist_access_token"] = token
    request.session.pop("oauth_state", None)
    # Send user back to SPA
    return RedirectResponse(f"{settings.FRONTEND_BASE}/auth/complete", status_code=302)
