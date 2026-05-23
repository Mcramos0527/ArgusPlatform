# app/api/routes/files.py
# Output file listing and download endpoints.

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.core.supabase import supabase
from app.db import queries

logger = logging.getLogger("argus.routes.files")
router = APIRouter()

STORAGE_BUCKET = "argus-files"
SIGNED_URL_TTL = 3600  # seconds


@router.get("/{run_id}/files")
def list_output_files(run_id: str):
    """
    List all output Excel files recorded for a run.
    Each item has: id, run_id, step, filename, storage_path, created_at.
    """
    run = queries.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    files = queries.get_output_files(run_id)
    return {"run_id": run_id, "files": files}


@router.get("/{run_id}/files/{step}")
def download_output_file(run_id: str, step: int):
    """
    Redirect to a short-lived Supabase Storage signed URL for the output
    Excel of the requested step (1, 2, or 3).
    """
    files = queries.get_output_files(run_id)
    match = next((f for f in files if f["step"] == step), None)

    if not match:
        raise HTTPException(
            status_code=404,
            detail=f"No output file found for run '{run_id}', step {step}",
        )

    storage_path = match["storage_path"]
    try:
        result = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(
            storage_path, SIGNED_URL_TTL
        )
        signed_url = result.get("signedURL") or result.get("signed_url")
        if not signed_url:
            raise ValueError("Signed URL not returned by Supabase")
    except Exception as exc:
        logger.error(f"Failed to create signed URL for {storage_path}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not generate download URL: {exc}",
        )

    return RedirectResponse(url=signed_url)
