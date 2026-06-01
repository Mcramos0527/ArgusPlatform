# app/main.py
# ARGUS FastAPI application entry point.

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import files, process, runs
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-25s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(
    title="ARGUS API",
    description="Automated Reconciliation & General Unified System — Powered by McFlow",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to settings.frontend_url in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(process.router, prefix="/api/process", tags=["process"])
app.include_router(runs.router,    prefix="/api/runs",    tags=["runs"])
app.include_router(files.router,   prefix="/api/runs",    tags=["files"])


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "version": "3.0.0"}


@app.get("/debug/db", tags=["meta"])
def debug_db():
    """Temporary debug endpoint — tests Supabase insert."""
    import uuid, traceback
    from app.core.supabase import supabase
    run_id = str(uuid.uuid4())
    try:
        result = supabase.table("runs").insert({
            "id": run_id,
            "status": "debug_test",
        }).execute()
        supabase.table("runs").delete().eq("id", run_id).execute()
        return {"ok": True, "inserted": run_id}
    except Exception as e:
        return {"ok": False, "error": str(e), "traceback": traceback.format_exc()}


@app.get("/", tags=["meta"])
def root():
    return {"app": "ARGUS API", "version": "3.0.0", "docs": "/docs"}
