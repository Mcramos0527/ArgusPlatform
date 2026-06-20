# app/services/control_engine.py
# Cross-matches bank categorized transactions vs Caja Dirección records
# by (month, category), producing a variance report.
#
# Classification rules (tickets #1 + #2):
#   Category only in one source              → CRITICAL
#   Category in both, variance  > 25%        → CRITICAL
#   Category in both, 10% < variance <= 25%  → ALERT
#   Category in both, variance <= 10%        → OK

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.models import Transaction

logger = logging.getLogger("argus.control")

# Thresholds (ticket #2)
_ALERT_PCT    = 10.0   # > 10% → ALERT
_CRITICAL_PCT = 25.0   # > 25% → CRITICAL


@dataclass
class ControlVariance:
    mes: str              # "2026-05"
    categoria: str
    total_banco: float
    total_caja: float
    diferencia: float     # banco − caja
    varianza_pct: float   # |diferencia| / max(banco, caja) * 100
    estado: str           # "OK" | "ALERT" | "CRITICAL"
    origen: str           # "BANCO" | "CAJA" | "AMBOS"


def _month_key(d: Optional[date]) -> str:
    return d.strftime("%Y-%m") if d else "SIN FECHA"


def _variance_pct(total_banco: float, total_caja: float, diferencia: float) -> float:
    """Percentage variance relative to the larger of the two totals."""
    base = max(abs(total_banco), abs(total_caja))
    if base == 0:
        return 0.0
    return round(abs(diferencia) / base * 100, 2)


def run_control(
    bank_transactions: List[Transaction],
    caja_rows: List[dict],
) -> List[ControlVariance]:
    """
    Build monthly category pivots from both sources and compute variances.

    Categories matched via literal uppercase text comparison (ticket #1).
    Status assigned by variance percentage (ticket #2):
      - Category only in one source           → CRITICAL
      - variance > 25%                        → CRITICAL
      - 10% < variance <= 25%                 → ALERT
      - variance <= 10%                       → OK
    """

    # ── Bank pivot: (month, CATEGORY) → sum |importe_neto| ──────────────────
    bank_pivot: dict = defaultdict(float)
    for tx in bank_transactions:
        if not tx.categoria_nombre:
            continue
        key = (_month_key(tx.fecha), tx.categoria_nombre.strip().upper())
        bank_pivot[key] += abs(tx.importe_neto)

    # ── Caja pivot: (month, CATEGORY) → sum |importe| ────────────────────────
    caja_pivot: dict = defaultdict(float)
    for row in caja_rows:
        cat = (row.get("categoria") or "").strip().upper()
        if not cat:
            continue
        key = (_month_key(row.get("fecha")), cat)
        caja_pivot[key] += abs(row.get("importe", 0.0))

    # ── Cross-join all (month, category) keys ────────────────────────────────
    all_keys = set(bank_pivot) | set(caja_pivot)
    variances: List[ControlVariance] = []

    for mes, cat in sorted(all_keys):
        total_banco = bank_pivot.get((mes, cat), 0.0)
        total_caja  = caja_pivot.get((mes, cat), 0.0)
        diferencia  = total_banco - total_caja

        in_banco = (mes, cat) in bank_pivot
        in_caja  = (mes, cat) in caja_pivot

        if not in_banco or not in_caja:
            # Single-source → always CRITICAL (ticket #1)
            varianza_pct = 100.0
            estado = "CRITICAL"
            origen = "BANCO" if in_banco else "CAJA"
        else:
            varianza_pct = _variance_pct(total_banco, total_caja, diferencia)
            origen = "AMBOS"
            if varianza_pct > _CRITICAL_PCT:
                estado = "CRITICAL"
            elif varianza_pct > _ALERT_PCT:
                estado = "ALERT"
            else:
                estado = "OK"

        variances.append(
            ControlVariance(
                mes=mes,
                categoria=cat,
                total_banco=round(total_banco, 2),
                total_caja=round(total_caja, 2),
                diferencia=round(diferencia, 2),
                varianza_pct=varianza_pct,
                estado=estado,
                origen=origen,
            )
        )

    critical = sum(1 for v in variances if v.estado == "CRITICAL")
    alert    = sum(1 for v in variances if v.estado == "ALERT")
    ok       = sum(1 for v in variances if v.estado == "OK")
    logger.info(
        f"Control — {ok} OK, {alert} ALERT, {critical} CRITICAL "
        f"({len(variances)} total)"
    )
    return variances
