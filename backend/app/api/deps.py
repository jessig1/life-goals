from fastapi import Depends, HTTPException, Request

def get_access_token(request: Request) -> str:
    token = request.session.get("todoist_access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated with Todoist. Visit /login first.")
    return token
