import httpx

NOTION_SEARCH = "https://api.notion.com/v1/search"
NOTION_PAGES  = "https://api.notion.com/v1/pages"
NOTION_VER    = "2022-06-28"  # pick a stable version

def notion_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VER,
        "Content-Type": "application/json",
    }

async def search(token: str, query: str):
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(NOTION_SEARCH, headers=notion_headers(token), json={"query": query})
        r.raise_for_status()
        return r.json()

async def create_page(token: str, body: dict):
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(NOTION_PAGES, headers=notion_headers(token), json=body)
        r.raise_for_status()
        return r.json()
