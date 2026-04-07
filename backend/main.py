"""
FastAPI main application — Email Triage RL Environment Backend

Exposes all OpenEnv-compatible endpoints and serves the Next.js
frontend static files in production (Docker) mode.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routes.email_routes import router as email_router
from backend.routes.env_routes import router as env_router


# ─── App factory ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print("🚀 Email Triage RL Environment API starting...")
    yield
    print("🛑 API shutting down.")


app = FastAPI(
    title="Email Triage RL Environment",
    description=(
        "OpenEnv-compatible RL environment for email triage and customer support automation. "
        "Provides step(), reset(), and state() endpoints alongside a full email corpus."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ─── CORS ────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten in production as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Routes ──────────────────────────────────────────────────────────────

app.include_router(env_router, prefix="/api", tags=["Environment"])
app.include_router(email_router, prefix="/api", tags=["Emails"])


# ─── Health check ─────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["Meta"])
async def health():
    return {"status": "ok", "service": "email-triage-rl-env", "version": "1.0.0"}


# ─── Frontend static file serving (production / Docker) ──────────────────────

FRONTEND_BUILD_DIR = Path(__file__).parent.parent / "frontend" / "out"

if FRONTEND_BUILD_DIR.exists():
    # Serve Next.js static export
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_BUILD_DIR), html=True),
        name="frontend",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        index = FRONTEND_BUILD_DIR / "index.html"
        return FileResponse(str(index))
