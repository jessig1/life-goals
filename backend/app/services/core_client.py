import os, httpx

CORE_BASE = os.getenv("CORE_BASE", "http://localhost:8080")
CORE_SECRET = os.getenv("CORE_SHARED_SECRET", "devsecret")

async def upsert_task_to_core(task: dict):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            f"{CORE_BASE}/internal/upsert/task",
            headers={"X-Core-Secret": CORE_SECRET, "Content-Type": "application/json"},
            json=task,
        )
        r.raise_for_status()
        return r.json()