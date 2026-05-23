# app/api/routes/runs.py
# History and detail endpoints for ARGUS runs.

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db import queries

logger = logging.getLogger("argus.routes.runs")
router = APIRouter()


@router.get("")
def list_runs(limit: int = Query(default=50, ge=1, le=200)):
    """
    Return the most recent runs.
    Fields: id, created_at, status, sheets_processed,
            transactions_total, steps_completed.
    """
    runs = queries.get_runs(limit=limit)
    return {"runs": runs, "count": len(runs)}


@router.get("/{run_id}")
def get_run(run_id: str):
    """Return the full record for a single run."""
    run = queries.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return run


@router.get("/{run_id}/transactions")
def get_transactions(
    run_id: str,
    page:  int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=500),
):
    """
    Return paginated transactions for a run.
    Response: { data, total, page, limit, pages }
    """
    run = queries.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    return queries.get_transactions(run_id, page=page, limit=limit)


@router.get("/{run_id}/reconciliation")
def get_reconciliation(run_id: str):
    """Return all reconciliation lines for a run."""
    run = queries.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    lines = queries.get_reconciliation(run_id)
    return {"run_id": run_id, "lines": lines, "count": len(lines)}


@router.delete("/{run_id}", status_code=204)
def delete_run(run_id: str):
    """
    Delete a run and all its associated records.
    Supabase cascade deletes handle child tables if FK constraints are configured.
    """
    run = queries.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    from app.core.supabase import supabase

    # Delete child tables explicitly in case cascade is not set
    for table in ("transactions", "reconciliation_lines", "caja_entries",
                  "bank_summaries", "output_files"):
        supabase.table(table).delete().eq("run_id", run_id).execute()

    supabase.table("runs").delete().eq("id", run_id).execute()
    logger.info(f"Run deleted: {run_id}")
    return None
