from fastapi import APIRouter, Request
from app.core.csrf import ensure_csrf

router = APIRouter(prefix="/api", tags=["session"])

@router.get("/session")
def get_session(request: Request):
    csrf = ensure_csrf(request)
    return {"csrf": csrf, "authenticated": "todoist_access_token" in request.session}

@router.get("/debug/session")
def debug_session(request: Request):
    return {"has_access_token": "todoist_access_token" in request.session,
            "csrf": request.session.get("csrf")}
