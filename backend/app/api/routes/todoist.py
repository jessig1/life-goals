from fastapi import APIRouter, Depends, HTTPException, Request, Header
from app.api.deps import get_access_token
from app.core.csrf import require_csrf
from app.services import todoist

router = APIRouter(tags=["todoist"])

@router.get("/todoist/tasks")
async def list_tasks(token: str = Depends(get_access_token)):
    try:
        data = await todoist.get_tasks(token, params=None)
        # normalize if you like; here we pass through
        return {"items": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/todoist/tasks")
async def create_task(request: Request, x_csrf_token: str | None = Header(None), token: str = Depends(get_access_token)):
    require_csrf(request, x_csrf_token)
    body = await request.json()
    if not body.get("content"):
        raise HTTPException(status_code=400, detail="`content` is required")
    try:
        created = await todoist.create_task(token, body)
        return {"item": created}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
