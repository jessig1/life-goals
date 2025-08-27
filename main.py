import os
import secrets
from typing import Optional, List

from fastapi import FastAPI, Request, Response, Depends, HTTPException, Header, Query
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import httpx
from dotenv import load_dotenv



load_dotenv()

CLIENT_ID = os.getenv("TODOIST_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("TODOIST_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("TODOIST_REDIRECT_URI", "http://localhost:8000/oauth/callback")
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_hex(32))

TODOIST_AUTH_URL = "https://todoist.com/oauth/authorize"
TODOIST_TOKEN_URL = "https://todoist.com/oauth/access_token"
TODOIST_TASKS_URL = "https://api.todoist.com/rest/v2/tasks"

app = FastAPI(title="Todoist + FastAPI Demo")

# CORS (adjust for your frontend if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cookie-based sessions (kept simple for the demo)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, same_site="lax", https_only=False)


def get_access_token(request: Request) -> str:
    token = request.session.get("todoist_access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated with Todoist. Visit /login first.")
    return token


@app.get("/")
def index(request: Request):
    authed = "todoist_access_token" in request.session
    return {"ok": True, "authenticated": authed}


@app.get("/login")
def login(request: Request):
    state = secrets.token_urlsafe(24)
    request.session["oauth_state"] = state

    # Also set a non-HttpOnly cookie with the same state as a fallback
    # (HttpOnly=False so you could read it on the client if ever needed,
    # but you can set it True if you only compare server-side.)
    resp = RedirectResponse(
        url=(
            f"{TODOIST_AUTH_URL}"
            f"?client_id={CLIENT_ID}"
            f"&scope=task:add"
            f"&state={state}"
            f"&redirect_uri={REDIRECT_URI}"
        ),
        status_code=302,
    )
    resp.set_cookie(
        key="oauth_state",
        value=state,
        max_age=600,
        secure=False,      # True in prod over HTTPS
        httponly=True,     # fine to make True since we only read server-side
        samesite="lax",
        path="/"
    )
    return resp

@app.get("/oauth/callback")
async def oauth_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None):
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state")

    # Verify state
    saved_state = request.session.get("oauth_state")
    if not saved_state or saved_state != state:
        raise HTTPException(status_code=400, detail="Invalid state")

    # Exchange code -> access_token
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            TODOIST_TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Token exchange failed: {resp.text}")

    data = resp.json()
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access_token in response")

    # Save token in session and clear state
    request.session["todoist_access_token"] = access_token
    request.session.pop("oauth_state", None)

    return RedirectResponse("http://localhost:5173/auth/complete", status_code=302)


@app.post("/create_task")
async def create_task(
    request: Request,
    x_csrf_token: str | None = Header(None),
):
    # CSRF check
    expected = request.session.get("csrf")
    if not expected or not x_csrf_token or x_csrf_token != expected:
        raise HTTPException(status_code=403, detail="Bad CSRF token")

    # existing auth check
    token = request.session.get("todoist_access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated with Todoist. Visit /login first.")

    payload = await request.json()
    if "content" not in payload or not payload["content"]:
        raise HTTPException(status_code=400, detail="`content` is required")

    allowed = {"content","description","project_id","section_id","parent_id",
               "order","labels","priority","due_string","due_date","due_datetime",
               "assignee_id"}
    body = {k: v for k, v in payload.items() if k in allowed}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            TODOIST_TASKS_URL,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=body,
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return JSONResponse(resp.json(), status_code=resp.status_code)

def ensure_csrf_token(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(24)
        request.session["csrf"] = token
    return token

@app.get("/session")
def get_session(request: Request):
    """
    Returns a CSRF token (and indicates auth state).
    This sets/refreshes the CSRF token in the server-side session.
    """
    csrf = ensure_csrf_token(request)
    authed = "todoist_access_token" in request.session
    return {"csrf": csrf, "authenticated": authed}

@app.get("/tasks")
async def list_tasks(
    request: Request,
    filter: Optional[str] = None,
    project_id: Optional[str] = None,
    section_id: Optional[str] = None,
    label: Optional[str] = None,
    ids: Optional[List[str]] = Query(default=None),
    lang: Optional[str] = None,
):
    token = request.session.get("todoist_access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated with Todoist. Visit /login first.")

    params = {}
    if filter: params["filter"] = filter
    if project_id: params["project_id"] = project_id
    if section_id: params["section_id"] = section_id
    if label: params["label"] = label
    if ids: params["ids"] = ",".join(ids)  # Todoist accepts comma-separated ids
    if lang: params["lang"] = lang

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            TODOIST_TASKS_URL,
            headers={"Authorization": f"Bearer {token}"},
            params=params
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    # Return the full task objects (array)
    return JSONResponse(resp.json())