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


@app.get("/", tags=["meta"])
def root():
    return {"app": "ARGUS API", "version": "3.0.0", "docs": "/docs"}
