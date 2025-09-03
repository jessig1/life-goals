import httpx

AUTH_URL = "https://todoist.com/oauth/authorize"
TOKEN_URL = "https://todoist.com/oauth/access_token"
TASKS_URL = "https://api.todoist.com/rest/v2/tasks"
PROJECTS_URL = "https://api.todoist.com/rest/v2/projects"
SECTIONS_URL = "https://api.todoist.com/rest/v2/sections"

async def exchange_code_for_token(client_id: str, client_secret: str, code: str, redirect_uri: str) -> str:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            TOKEN_URL,
            data=dict(client_id=client_id, client_secret=client_secret, code=code, redirect_uri=redirect_uri),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        return r.json()["access_token"]

async def create_task(token: str, body: dict):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(TASKS_URL, headers={"Authorization": f"Bearer {token}"}, json=body)
        r.raise_for_status()
        return r.json()

async def list_tasks(token: str, params: dict):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(TASKS_URL, headers={"Authorization": f"Bearer {token}"}, params=params)
        r.raise_for_status()
        return r.json()

async def list_projects(token: str):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(PROJECTS_URL, headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json()

async def list_sections(token: str, project_id: str | None = None):
    params = {"project_id": project_id} if project_id else None
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(SECTIONS_URL, headers={"Authorization": f"Bearer {token}"}, params=params)
        r.raise_for_status()
        return r.json()
