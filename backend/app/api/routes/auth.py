from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import secrets, httpx

from app.core.config import settings
from app.services.todoist import AUTH_URL, exchange_code_for_token

router = APIRouter(tags=["auth"])

# Todoist login
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

# Notion OAuth endpoints
NOTION_CLIENT_ID = "your_notion_client_id"
NOTION_CLIENT_SECRET = "your_notion_client_secret"
NOTION_REDIRECT_URI = f"{settings.FRONTEND_BASE}/api/notion/callback"
NOTION_AUTH_URL = "https://api.notion.com/v1/oauth/authorize"
NOTION_TOKEN_URL = "https://api.notion.com/v1/oauth/token"

@router.get("/notion/connect")
def connect_notion(request: Request):
    state = secrets.token_urlsafe(24)
    request.session["notion_oauth_state"] = state
    url = f"{NOTION_AUTH_URL}?{urlencode({'client_id': NOTION_CLIENT_ID, 'response_type': 'code', 'owner': 'user', 'redirect_uri': NOTION_REDIRECT_URI, 'state': state})}"
    return RedirectResponse(url)

@router.get("/notion/callback")
async def notion_callback(request: Request, code: str = None, state: str = None):
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state")
    saved = request.session.get("notion_oauth_state")
    if not saved or saved != state:
        raise HTTPException(status_code=400, detail="Invalid state")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            NOTION_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": NOTION_REDIRECT_URI,
                "client_id": NOTION_CLIENT_ID,
                "client_secret": NOTION_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
    request.session["notion_access_token"] = token
    request.session.pop("notion_oauth_state", None)
    return RedirectResponse(f"{settings.FRONTEND_BASE}/auth/complete")
