from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Header, Query, Depends

from app.api.deps import get_access_token
from app.core.csrf import require_csrf
from app.services.todoist import create_task, list_tasks

router = APIRouter(prefix="/api", tags=["tasks"])

@router.get("/tasks")
async def get_tasks(
    request: Request,
    token: str = Depends(get_access_token),
    filter: Optional[str] = None,
    project_id: Optional[str] = None,
    section_id: Optional[str] = None,
    label: Optional[str] = None,
    ids: Optional[List[str]] = Query(default=None),
    lang: Optional[str] = None,
):
    params = {}
    if filter: params["filter"] = filter
    if project_id: params["project_id"] = project_id
    if section_id: params["section_id"] = section_id
    if label: params["label"] = label
    if ids: params["ids"] = ",".join(ids)
    if lang: params["lang"] = lang

    try:
        return await list_tasks(token, params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create_task")
async def post_task(
    request: Request,
    x_csrf_token: str | None = Header(None),
    token: str = Depends(get_access_token),
):
    require_csrf(request, x_csrf_token)

    payload = await request.json()
    if not payload.get("content"):
        raise HTTPException(status_code=400, detail="`content` is required")

    allowed = {"content","description","project_id","section_id","parent_id",
               "order","labels","priority","due_string","due_date","due_datetime",
               "assignee_id"}
    body = {k: v for k, v in payload.items() if k in allowed}

    try:
        return await create_task(token, body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
