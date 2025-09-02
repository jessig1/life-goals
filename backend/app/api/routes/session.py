# app/api/routes/session.py

from fastapi import APIRouter, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from app.core.csrf import ensure_csrf, require_csrf

router = APIRouter(tags=["session"])

@router.get("/session")
def get_session(request: Request):
    csrf = ensure_csrf(request)
    return {"csrf": csrf, "authenticated": "todoist_access_token" in request.session}

@router.post("/logout")
def logout(request: Request, x_csrf_token: str | None = Header(None)):
    require_csrf(request, x_csrf_token)
    request.session.pop("todoist_access_token", None)
    request.session.pop("csrf", None)
    # optional: rotate session id by writing something new
    return JSONResponse({"ok": True})
