from fastapi import APIRouter, Depends, HTTPException, Request, Header
from app.api.deps import get_notion_token  # implement similar to get_access_token
from app.core.csrf import require_csrf
from app.services import notion

router = APIRouter(tags=["notion"])

@router.post("/notion/search")
async def notion_search(request: Request, token: str = Depends(get_notion_token)):
    q = (await request.json()).get("query","")
    try:
        return await notion.search(token, q)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/notion/pages")
async def notion_create_page(request: Request, x_csrf_token: str | None = Header(None), token: str = Depends(get_notion_token)):
    require_csrf(request, x_csrf_token)
    body = await request.json()
    try:
        return await notion.create_page(token, body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
