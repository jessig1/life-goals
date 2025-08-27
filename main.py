import os
import secrets
from typing import Optional

from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import httpx
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse


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
    # CSRF protection with a state value stored in session
    state = secrets.token_urlsafe(24)
    request.session["oauth_state"] = state

    # Request only what we need; `task:add` is sufficient to create tasks.
    scope = "task:add"
    params = {
        "client_id": CLIENT_ID,
        "scope": scope,
        "state": state,
        "redirect_uri": REDIRECT_URI,
    }

    # Build the auth URL manually to avoid extra deps
    from urllib.parse import urlencode
    auth_url = f"{TODOIST_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(auth_url, status_code=302)


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

    return JSONResponse({"ok": True, "message": "Todoist connected! You can now POST /create_task"})


@app.post("/create_task")
async def create_task(
    request: Request,
    token: str = Depends(get_access_token),
):
    """
    Body (JSON):
    {
      "content": "it works!",
      "due_string": "today at 10:05",
      "priority": 2,
      "project_id": "optional",
      "section_id": "optional"
    }
    """
    payload = await request.json()
    if "content" not in payload or not payload["content"]:
        raise HTTPException(status_code=400, detail="`content` is required")

    # Only pass supported fields to Todoist
    allowed = {"content", "description", "project_id", "section_id", "parent_id",
               "order", "labels", "priority", "due_string", "due_date", "due_datetime",
               "assignee_id"}
    body = {k: v for k, v in payload.items() if k in allowed}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            TODOIST_TASKS_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=body,
        )

    if resp.status_code not in (200, 201):
        # Surface Todoist's error to the client for easier debugging
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return JSONResponse(resp.json(), status_code=resp.status_code)

@app.get("/demo", response_class=HTMLResponse)
def demo():
    return """
<!doctype html>
<html>
  <body>
    <button id="make">Create Task</button>
    <pre id="out"></pre>
    <script>
      document.getElementById('make').onclick = async () => {
        const res = await fetch('/create_task', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          credentials: 'include', // send session cookie
          body: JSON.stringify({ content: 'Task from demo page', priority: 3 })
        });
        document.getElementById('out').textContent =
          (res.status + ' ' + res.statusText + '\\n') + await res.text();
      };
    </script>
  </body>
</html>
"""