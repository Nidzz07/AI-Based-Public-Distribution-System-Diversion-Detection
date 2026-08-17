"""FastAPI application entrypoint.

App, CORS, /health, and the three routers. Every route lives under /api; the
prefix is applied here rather than repeated in each router so the contract in
PROJECT-BRIEF.md has exactly one place it can drift from.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (import registers tables on Base.metadata)
from .db import Base, engine
from .routers import audit, cases, rulebook

app = FastAPI(
    title="LEAKPROOF",
    description="Diversion detection for India's Public Distribution System.",
    version="0.1.0",
)

# Vite dev server only. No wildcard: the demo runs on one known origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Safe on an already-seeded file: create_all only creates what is missing.
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    """Liveness probe. Returns ok as soon as the app is importable."""
    return {"status": "ok", "service": "leakproof", "version": app.version}


app.include_router(cases.router, prefix="/api")
app.include_router(rulebook.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
