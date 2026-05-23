# app/api/routes/process.py
# SSE-streaming pipeline endpoints for the 3-step ARGUS process.
#
# Each endpoint:
#   1. Receives uploaded Excel file(s)
#   2. Saves input(s) to Supabase Storage under inputs/{run_id}/
#   3. Runs the pipeline step in a thread pool
#   4. Streams progress as Server-Sent Events (JSON lines)
#   5. Saves results + output Excel to Supabase DB / Storage
#   6. Emits a final "done" event with run_id and file_url

import asyncio
import json
import logging
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

from app.core.supabase import supabase
from app.db import queries
from app.services.processor import Processor

logger = logging.getLogger("argus.routes.process")
router = APIRouter()

# One global thread-pool executor — keeps worker threads alive between requests.
_executor = ThreadPoolExecutor(max_workers=4)

# In-memory map: run_id → Processor instance.
# The Processor carries inter-step state (transactions from Step 1 are needed in
# Step 2 and 3).  On a single-dyno deployment this is safe.  For multi-replica
# deployments the Processor state would need to be serialised to a shared store.
_processors: dict[str, Processor] = {}

STORAGE_BUCKET = "argus-files"


# ── Storage helpers ───────────────────────────────────────────────────────────

def _upload_to_storage(local_path: str, storage_path: str) -> None:
    """Upload a local file to Supabase Storage."""
    with open(local_path, "rb") as f:
        supabase.storage.from_(STORAGE_BUCKET).upload(
            storage_path,
            f.read(),
            {"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        )


def _get_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """Return a short-lived signed URL for a file in Supabase Storage."""
    result = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(
        storage_path, expires_in
    )
    return result.get("signedURL", "")


async def _save_upload(upload: UploadFile, dest_path: str) -> None:
    """Write an uploaded file to a local temp path (async)."""
    content = await upload.read()
    with open(dest_path, "wb") as f:
        f.write(content)


# ── SSE event builder ─────────────────────────────────────────────────────────

def _log_event(msg: str) -> str:
    return json.dumps({
        "type": "log",
        "msg":  msg,
        "ts":   datetime.now().strftime("%H:%M:%S"),
    })


def _progress_event(pct: int) -> str:
    return json.dumps({"type": "progress", "pct": pct})


def _done_event(run_id: str, file_url: str) -> str:
    return json.dumps({"type": "done", "run_id": run_id, "file_url": file_url})


def _error_event(msg: str) -> str:
    return json.dumps({"type": "error", "msg": msg})


# ── Paso 1: Movimientos Bancarios ─────────────────────────────────────────────

@router.post("/paso1")
async def proceso_paso1(
    movimientos: UploadFile = File(..., description="Movimientos.xlsx"),
):
    """
    Step 1 — Normalize bank transactions.
    Creates a new run and streams progress as SSE.
    """
    run_id = str(uuid.uuid4())

    # Save uploaded file to a temp directory
    tmp_dir = tempfile.mkdtemp(prefix=f"argus_{run_id}_")
    input_path = str(Path(tmp_dir) / "movimientos.xlsx")
    output_folder = str(Path(tmp_dir) / "output")
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    await _save_upload(movimientos, input_path)

    # Upload input to Supabase Storage
    storage_input_path = f"inputs/{run_id}/movimientos.xlsx"
    try:
        _upload_to_storage(input_path, storage_input_path)
    except Exception as e:
        logger.warning(f"Storage upload failed (non-fatal): {e}")

    # Create run record in DB
    queries.create_run({
        "id":                 run_id,
        "status":             "running",
        "steps_completed":    0,
        "sheets_processed":   0,
        "transactions_total": 0,
    })

    processor = Processor()
    _processors[run_id] = processor

    async def event_generator() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def on_progress(msg: str) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, ("log", msg))

        def run_pipeline():
            return processor.run_paso1(
                path_movimientos=input_path,
                output_folder=output_folder,
                on_progress=on_progress,
            )

        # Kick off pipeline in thread pool
        future = loop.run_in_executor(_executor, run_pipeline)

        yield _log_event(f"⚡ Run {run_id} iniciado — procesando Movimientos.xlsx")
        yield _progress_event(5)

        # Drain log queue while pipeline runs
        while not future.done():
            try:
                kind, payload = await asyncio.wait_for(queue.get(), timeout=0.1)
                if kind == "log":
                    yield _log_event(payload)
            except asyncio.TimeoutError:
                pass

        # Drain any remaining messages
        while not queue.empty():
            kind, payload = queue.get_nowait()
            if kind == "log":
                yield _log_event(payload)

        # Collect result
        try:
            result = await future
        except Exception as exc:
            logger.exception("Paso 1 pipeline error")
            queries.update_run(run_id, {"status": "error"})
            yield _error_event(f"Error en pipeline: {exc}")
            return

        if result.errors:
            queries.update_run(run_id, {"status": "error"})
            yield _error_event(" | ".join(result.errors))
            return

        yield _progress_event(70)
        yield _log_event("💾 Guardando transacciones en base de datos...")

        # Save transactions to DB
        queries.save_transactions(run_id, result.transactions)

        yield _progress_event(85)
        yield _log_event("📤 Subiendo archivo de salida a Supabase Storage...")

        # Find output Excel and upload it
        output_files = list(Path(output_folder).glob("argus_movimientos_*.xlsx"))
        file_url = ""
        if output_files:
            out_local = str(output_files[0])
            out_filename = output_files[0].name
            storage_out_path = f"outputs/{run_id}/step1_{out_filename}"
            try:
                _upload_to_storage(out_local, storage_out_path)
                queries.save_output_file(run_id, 1, out_filename, storage_out_path)
                file_url = f"/api/runs/{run_id}/files/1"
                yield _log_event(f"  ✓ {out_filename}")
            except Exception as e:
                logger.warning(f"Output upload failed: {e}")
                yield _log_event(f"  ⚠ Storage upload failed: {e}")

        # Update run record
        queries.update_run(run_id, {
            "status":             "step1_complete",
            "steps_completed":    1,
            "sheets_processed":   result.sheets_processed,
            "transactions_total": result.transactions_total,
        })

        yield _progress_event(100)
        yield _done_event(run_id, file_url)

    return EventSourceResponse(event_generator())


# ── Paso 2: ERP Reconciliation ────────────────────────────────────────────────

@router.post("/paso2/{run_id}")
async def proceso_paso2(
    run_id: str,
    cobros: UploadFile = File(..., description="COBROS.xlsx"),
    pagos:  UploadFile = File(..., description="PAGOS.xlsx"),
):
    """
    Step 2 — Reconcile bank transactions against ERP Coliseo.
    Requires a run that completed Step 1.
    """
    processor = _processors.get(run_id)
    if processor is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found or Step 1 not completed in this session.",
        )

    tmp_dir = tempfile.mkdtemp(prefix=f"argus_{run_id}_p2_")
    cobros_path  = str(Path(tmp_dir) / "cobros.xlsx")
    pagos_path   = str(Path(tmp_dir) / "pagos.xlsx")
    output_folder = str(Path(tmp_dir) / "output")
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    await _save_upload(cobros, cobros_path)
    await _save_upload(pagos, pagos_path)

    # Upload inputs
    for local, name in [(cobros_path, "cobros.xlsx"), (pagos_path, "pagos.xlsx")]:
        try:
            _upload_to_storage(local, f"inputs/{run_id}/{name}")
        except Exception as e:
            logger.warning(f"Storage input upload failed ({name}): {e}")

    queries.update_run(run_id, {"status": "running_step2"})

    async def event_generator() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def on_progress(msg: str) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, ("log", msg))

        def run_pipeline():
            return processor.run_paso2(
                path_cobros=cobros_path,
                path_pagos=pagos_path,
                output_folder=output_folder,
                on_progress=on_progress,
            )

        future = loop.run_in_executor(_executor, run_pipeline)

        yield _log_event("⚡ Paso 2 iniciado — cargando COBROS y PAGOS del ERP")
        yield _progress_event(5)

        while not future.done():
            try:
                kind, payload = await asyncio.wait_for(queue.get(), timeout=0.1)
                if kind == "log":
                    yield _log_event(payload)
            except asyncio.TimeoutError:
                pass

        while not queue.empty():
            kind, payload = queue.get_nowait()
            if kind == "log":
                yield _log_event(payload)

        try:
            result = await future
        except Exception as exc:
            logger.exception("Paso 2 pipeline error")
            queries.update_run(run_id, {"status": "error"})
            yield _error_event(f"Error en pipeline: {exc}")
            return

        if result.errors:
            queries.update_run(run_id, {"status": "error"})
            yield _error_event(" | ".join(result.errors))
            return

        yield _progress_event(70)
        yield _log_event("💾 Guardando líneas de conciliación...")

        if hasattr(result, "recon_lines") and result.recon_lines:
            queries.save_reconciliation(run_id, result.recon_lines)

        yield _progress_event(85)
        yield _log_event("📤 Subiendo reporte de conciliación...")

        output_files = list(Path(output_folder).glob("argus_conciliacion_*.xlsx"))
        file_url = ""
        if output_files:
            out_local = str(output_files[0])
            out_filename = output_files[0].name
            storage_out_path = f"outputs/{run_id}/step2_{out_filename}"
            try:
                _upload_to_storage(out_local, storage_out_path)
                queries.save_output_file(run_id, 2, out_filename, storage_out_path)
                file_url = f"/api/runs/{run_id}/files/2"
                yield _log_event(f"  ✓ {out_filename}")
            except Exception as e:
                logger.warning(f"Output upload failed: {e}")
                yield _log_event(f"  ⚠ Storage upload failed: {e}")

        queries.update_run(run_id, {
            "status":          "step2_complete",
            "steps_completed": 2,
        })

        yield _progress_event(100)
        yield _done_event(run_id, file_url)

    return EventSourceResponse(event_generator())


# ── Paso 3: Caja Fábrica Digital ─────────────────────────────────────────────

@router.post("/paso3/{run_id}")
async def proceso_paso3(
    run_id: str,
    caja: UploadFile = File(..., description="Caja.xlsx"),
):
    """
    Step 3 — Generate Caja Fábrica Digital export.
    Requires a run that completed Step 1.
    """
    processor = _processors.get(run_id)
    if processor is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found or Step 1 not completed in this session.",
        )

    tmp_dir = tempfile.mkdtemp(prefix=f"argus_{run_id}_p3_")
    caja_path     = str(Path(tmp_dir) / "caja.xlsx")
    output_folder = str(Path(tmp_dir) / "output")
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    await _save_upload(caja, caja_path)

    try:
        _upload_to_storage(caja_path, f"inputs/{run_id}/caja.xlsx")
    except Exception as e:
        logger.warning(f"Storage input upload failed (caja.xlsx): {e}")

    queries.update_run(run_id, {"status": "running_step3"})

    async def event_generator() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def on_progress(msg: str) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, ("log", msg))

        def run_pipeline():
            return processor.run_paso3(
                path_caja=caja_path,
                output_folder=output_folder,
                on_progress=on_progress,
            )

        future = loop.run_in_executor(_executor, run_pipeline)

        yield _log_event("⚡ Paso 3 iniciado — generando export Caja Fábrica Digital")
        yield _progress_event(5)

        while not future.done():
            try:
                kind, payload = await asyncio.wait_for(queue.get(), timeout=0.1)
                if kind == "log":
                    yield _log_event(payload)
            except asyncio.TimeoutError:
                pass

        while not queue.empty():
            kind, payload = queue.get_nowait()
            if kind == "log":
                yield _log_event(payload)

        try:
            result = await future
        except Exception as exc:
            logger.exception("Paso 3 pipeline error")
            queries.update_run(run_id, {"status": "error"})
            yield _error_event(f"Error en pipeline: {exc}")
            return

        if result.errors:
            queries.update_run(run_id, {"status": "error"})
            yield _error_event(" | ".join(result.errors))
            return

        yield _progress_event(70)
        yield _log_event("💾 Guardando entradas de Caja...")

        if result.caja_entries:
            queries.save_caja_entries(run_id, result.caja_entries)

        yield _progress_event(85)
        yield _log_event("📤 Subiendo export de Caja...")

        output_files = list(Path(output_folder).glob("argus_export_caja_*.xlsx"))
        file_url = ""
        if output_files:
            out_local = str(output_files[0])
            out_filename = output_files[0].name
            storage_out_path = f"outputs/{run_id}/step3_{out_filename}"
            try:
                _upload_to_storage(out_local, storage_out_path)
                queries.save_output_file(run_id, 3, out_filename, storage_out_path)
                file_url = f"/api/runs/{run_id}/files/3"
                yield _log_event(f"  ✓ {out_filename}")
            except Exception as e:
                logger.warning(f"Output upload failed: {e}")
                yield _log_event(f"  ⚠ Storage upload failed: {e}")

        # Clean up processor from memory — run is fully complete
        _processors.pop(run_id, None)

        queries.update_run(run_id, {
            "status":          "complete",
            "steps_completed": 3,
        })

        yield _progress_event(100)
        yield _log_event("🎉 Todos los pasos completados — revisa los archivos de salida")
        yield _done_event(run_id, file_url)

    return EventSourceResponse(event_generator())
