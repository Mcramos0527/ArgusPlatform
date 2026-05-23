# app/db/queries.py
# Supabase database operations for ARGUS.
# All functions use the service-role client (bypasses RLS).

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.core.supabase import supabase
from app.models import BankSummary, CajaEntry, Transaction
from app.services.reconciler import ReconciliationLine

logger = logging.getLogger("argus.db")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _date_to_str(d) -> Optional[str]:
    """Convert date/datetime to ISO string for Supabase."""
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.isoformat()
    if isinstance(d, date):
        return d.isoformat()
    return str(d)


# ── Runs ──────────────────────────────────────────────────────────────────────

def create_run(data: Dict[str, Any]) -> str:
    """Insert a new run record and return its UUID."""
    result = supabase.table("runs").insert(data).execute()
    row = result.data[0]
    logger.info(f"Run created: {row['id']}")
    return row["id"]


def update_run(run_id: str, data: Dict[str, Any]) -> None:
    """Update fields on an existing run."""
    supabase.table("runs").update(data).eq("id", run_id).execute()
    logger.info(f"Run updated: {run_id} — {list(data.keys())}")


def get_runs(limit: int = 50) -> List[Dict]:
    """Return the most recent runs ordered by created_at desc."""
    result = (
        supabase.table("runs")
        .select(
            "id, created_at, status, sheets_processed, "
            "transactions_total, steps_completed"
        )
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def get_run(run_id: str) -> Optional[Dict]:
    """Return full run record or None if not found."""
    result = (
        supabase.table("runs")
        .select("*")
        .eq("id", run_id)
        .single()
        .execute()
    )
    return result.data


# ── Transactions ──────────────────────────────────────────────────────────────

def save_transactions(run_id: str, transactions: List[Transaction]) -> None:
    """Bulk-insert normalized transactions for a run (chunked to avoid limits)."""
    if not transactions:
        return

    rows = []
    for tx in transactions:
        rows.append({
            "run_id":           run_id,
            "pestana":          tx.pestaña,
            "empresa":          tx.empresa,
            "banco":            tx.banco,
            "fecha":            _date_to_str(tx.fecha),
            "fecha_valor":      _date_to_str(tx.fecha_valor),
            "descripcion":      tx.descripcion,
            "detalle":          tx.detalle,
            "debito":           tx.debito if tx.debito else None,
            "credito":          tx.credito if tx.credito else None,
            "importe_neto":     tx.importe_neto,
            "saldo":            tx.saldo,
            "nro_referencia":   tx.nro_referencia,
            "nro_cheque":       tx.nro_cheque,
            "cod_concepto":     tx.cod_concepto,
            "tipo_concepto":    tx.tipo_concepto,
            "canal":            tx.canal,
            "sucursal":         tx.sucursal,
            "categoria_codigo": tx.categoria_codigo,
            "categoria_nombre": tx.categoria_nombre,
            "tipo_movimiento":  tx.tipo_movimiento,
            "alerta":           tx.alerta,
        })

    # Insert in chunks of 500 to stay within Supabase payload limits
    chunk_size = 500
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        supabase.table("transactions").insert(chunk).execute()

    logger.info(f"Saved {len(rows)} transactions for run {run_id}")


def get_transactions(
    run_id: str,
    page: int = 1,
    limit: int = 100,
) -> Dict[str, Any]:
    """Return paginated transactions for a run."""
    offset = (page - 1) * limit

    # Count total
    count_result = (
        supabase.table("transactions")
        .select("id", count="exact")
        .eq("run_id", run_id)
        .execute()
    )
    total = count_result.count or 0

    # Fetch page
    data_result = (
        supabase.table("transactions")
        .select("*")
        .eq("run_id", run_id)
        .order("id")
        .range(offset, offset + limit - 1)
        .execute()
    )

    return {
        "data":  data_result.data or [],
        "total": total,
        "page":  page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit else 1,
    }


# ── Summaries ─────────────────────────────────────────────────────────────────

def save_summaries(run_id: str, summaries: List[BankSummary]) -> None:
    """Insert bank daily summaries for a run."""
    if not summaries:
        return

    rows = [
        {
            "run_id":            run_id,
            "empresa":           s.empresa,
            "banco":             s.banco,
            "pestana":           s.pestaña,
            "saldo_actual":      s.saldo_actual,
            "gastos_dia":        s.gastos_dia,
            "intereses_dia":     s.intereses_dia,
            "cobros_dia":        s.cobros_dia,
            "pagos_dia":         s.pagos_dia,
            "movimientos_count": s.movimientos_count,
        }
        for s in summaries
    ]
    supabase.table("bank_summaries").insert(rows).execute()
    logger.info(f"Saved {len(rows)} summaries for run {run_id}")


# ── Reconciliation ────────────────────────────────────────────────────────────

def save_reconciliation(run_id: str, lines: List[ReconciliationLine]) -> None:
    """Insert reconciliation lines for a run."""
    if not lines:
        return

    rows = [
        {
            "run_id":            run_id,
            "estado":            line.estado,
            "tipo":              line.tipo,
            "fecha_banco":       _date_to_str(line.fecha_banco),
            "fecha_erp":         _date_to_str(line.fecha_erp),
            "monto":             line.monto,
            "nombre":            line.nombre,
            "banco":             line.banco,
            "comprobante":       line.comprobante,
            "descripcion_banco": line.descripcion_banco,
            "detalle_erp":       line.detalle_erp,
            "diferencia_dias":   line.diferencia_dias,
            "alerta":            line.alerta,
        }
        for line in lines
    ]

    chunk_size = 500
    for i in range(0, len(rows), chunk_size):
        supabase.table("reconciliation_lines").insert(rows[i : i + chunk_size]).execute()

    logger.info(f"Saved {len(rows)} reconciliation lines for run {run_id}")


def get_reconciliation(run_id: str) -> List[Dict]:
    """Return all reconciliation lines for a run."""
    result = (
        supabase.table("reconciliation_lines")
        .select("*")
        .eq("run_id", run_id)
        .order("estado")
        .execute()
    )
    return result.data or []


# ── Caja entries ──────────────────────────────────────────────────────────────

def save_caja_entries(run_id: str, entries: List[CajaEntry]) -> None:
    """Insert Caja Fabrica Digital entries for a run."""
    if not entries:
        return

    rows = [
        {
            "run_id":      run_id,
            "dia":         entry.dia,
            "fecha":       _date_to_str(entry.fecha),
            "nro_tipo":    entry.nro_tipo,
            "tipo":        entry.tipo,
            "importe":     entry.importe,
            "descripcion": entry.descripcion,
            "canal":       entry.canal,
            "empresa":     entry.empresa,
            "banco":       entry.banco,
        }
        for entry in entries
    ]
    supabase.table("caja_entries").insert(rows).execute()
    logger.info(f"Saved {len(rows)} caja entries for run {run_id}")


# ── Output files ──────────────────────────────────────────────────────────────

def save_output_file(
    run_id: str,
    step: int,
    filename: str,
    storage_path: str,
) -> None:
    """Record an output Excel file generated by a pipeline step."""
    supabase.table("output_files").insert({
        "run_id":       run_id,
        "step":         step,
        "filename":     filename,
        "storage_path": storage_path,
    }).execute()
    logger.info(f"Output file recorded: step={step} path={storage_path}")


def get_output_files(run_id: str) -> List[Dict]:
    """Return all output file records for a run."""
    result = (
        supabase.table("output_files")
        .select("*")
        .eq("run_id", run_id)
        .order("step")
        .execute()
    )
    return result.data or []
