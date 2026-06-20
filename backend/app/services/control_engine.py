# app/services/control_engine.py
# Cross-matches bank categorized transactions vs Caja Dirección records
# by (month, category), producing a variance report per the ticket spec.

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.models import Transaction

logger = logging.getLogger("argus.control")


@dataclass
class ControlVariance:
    mes: str            # "2026-05"
    categoria: str
    total_banco: float
    total_caja: float
    diferencia: float   # banco − caja
    estado: str         # "OK" | "DIFERENCIA" | "CRITICO"
    origen: str         # "BANCO" | "CAJA" | "AMBOS"


def _month_key(d: Optional[date]) -> str:
    return d.strftime("%Y-%m") if d else "SIN FECHA"


def run_control(
    bank_transactions: List[Transaction],
    caja_rows: List[dict],
    tolerance: float = 0.01,
) -> List[ControlVariance]:
    """
    Build monthly category pivots from both sources and compute variances.

    Rules (per ticket spec):
    - Categories matched via literal uppercase text comparison.
    - Category present only in one source → estado = CRITICO.
    - Category in both but |diff| > tolerance → estado = DIFERENCIA.
    - Category in both and |diff| <= tolerance → estado = OK.
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
            estado = "CRITICO"
            origen = "BANCO" if in_banco else "CAJA"
        elif abs(diferencia) <= tolerance:
            estado = "OK"
            origen = "AMBOS"
        else:
            estado = "DIFERENCIA"
            origen = "AMBOS"

        variances.append(
            ControlVariance(
                mes=mes,
                categoria=cat,
                total_banco=round(total_banco, 2),
                total_caja=round(total_caja, 2),
                diferencia=round(diferencia, 2),
                estado=estado,
                origen=origen,
            )
        )

    criticos    = sum(1 for v in variances if v.estado == "CRITICO")
    diferencias = sum(1 for v in variances if v.estado == "DIFERENCIA")
    ok          = sum(1 for v in variances if v.estado == "OK")
    logger.info(
        f"Control — {ok} OK, {diferencias} diferencias, {criticos} críticos "
        f"({len(variances)} total)"
    )
    return variances
