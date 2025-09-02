from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.api.routes import auth, session, tasks

app = FastAPI(title="Life Goals API")

# Session cookie
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    same_site="none" if settings.SAME_SITE_NONE else "lax",
    https_only=False,  # set True in prod with HTTPS
)

# CORS (if you are NOT using Vite proxy; with proxy this can be relaxed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["Content-Type","X-CSRF-Token"],
)

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")

# Health
@app.get("/api/health")
def health():
    return {"ok": True}
