from app.services.core_client import upsert_task_to_core

@router.post("/todoist/tasks")
async def create_task(...):
    ...
    created = await todoist.create_task(token, body)
    # normalize minimally; pass through is fine for now
    await upsert_task_to_core({
        "id": created["id"],
        "content": created["content"],
        "priority": created["priority"],
        "project_id": created["project_id"],
        "labels": created.get("labels", []),
        "due": created.get("due"),
    })
    return {"item": created}

@router.get("/todoist/tasks")
async def list_tasks(token: str = Depends(get_access_token)):
    data = await todoist.get_tasks(token, params=None)
    # fire-and-forget upserts (simple loop; you can make it concurrent later)
    for t in data:
        try:
            await upsert_task_to_core({
                "id": t["id"],
                "content": t["content"],
                "priority": t["priority"],
                "project_id": t["project_id"],
                "labels": t.get("labels", []),
                "due": t.get("due"),
            })
        except Exception:
            pass
    return {"items": data}
