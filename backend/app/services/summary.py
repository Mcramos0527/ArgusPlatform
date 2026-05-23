# app/services/summary.py
# Genera el resumen bancario diario (replica la lógica de BANCOS DEL DIA)
# y las entradas para CAJA FÁBRICA DIGITAL.

import logging
from datetime import date
from typing import Dict, List, Optional

from app.models import BankSummary, CajaEntry, Transaction
from app.config import SHEET_CONFIG

logger = logging.getLogger("argus.summary")

# Categorías que representan gastos bancarios (para la columna GASTOS DEL DIA)
BANK_EXPENSE_CATEGORIES = {17}   # 17 = GASTOS BANCOS
INTEREST_CATEGORIES     = {29}   # 29 = INTERESES GANADOS (también 3 = DEUDA para intereses pagados)
BANK_FEE_CATEGORIES     = {17, 19}  # gastos e impuestos


class SummaryGenerator:
    """Genera resúmenes bancarios diarios y entradas de caja."""

    def generate_bank_summaries(
        self,
        transactions: List[Transaction],
        reference_date: Optional[date] = None,
    ) -> List[BankSummary]:
        """
        Genera un BankSummary por cada cuenta bancaria.
        Si reference_date es None, usa el día con más transacciones.
        """
        if not transactions:
            return []

        # Agrupar por pestaña
        by_sheet: Dict[str, List[Transaction]] = {}
        for tx in transactions:
            by_sheet.setdefault(tx.pestaña, []).append(tx)

        summaries: List[BankSummary] = []

        for sheet_name, txs in by_sheet.items():
            cfg = SHEET_CONFIG.get(sheet_name, {})

            # Calcular el día de referencia
            if reference_date:
                ref = reference_date
            else:
                ref = self._most_recent_date(txs)

            # Filtrar transacciones del día de referencia
            day_txs = [tx for tx in txs if tx.fecha == ref] if ref else txs

            # Último saldo disponible (mayor fecha)
            last_tx = max(
                (tx for tx in txs if tx.saldo != 0),
                key=lambda t: t.fecha or date.min,
                default=None,
            )
            saldo_actual = last_tx.saldo if last_tx else 0.0

            gastos_dia = sum(
                abs(tx.importe_neto) for tx in day_txs
                if tx.categoria_codigo in BANK_FEE_CATEGORIES
                and tx.importe_neto < 0
            )

            intereses_dia = sum(
                tx.importe_neto for tx in day_txs
                if tx.categoria_codigo in INTEREST_CATEGORIES
            )

            cobros_dia = sum(
                tx.credito for tx in day_txs
                if tx.tipo_movimiento == "COBRO"
            )
            pagos_dia = sum(
                tx.debito for tx in day_txs
                if tx.tipo_movimiento == "PAGO"
            )

            summary = BankSummary(
                empresa          = cfg.get("company", ""),
                banco            = cfg.get("bank", sheet_name),
                pestaña          = sheet_name,
                saldo_actual     = saldo_actual,
                gastos_dia       = gastos_dia,
                intereses_dia    = intereses_dia,
                cobros_dia       = cobros_dia,
                pagos_dia        = pagos_dia,
                movimientos_count= len(day_txs),
            )
            summaries.append(summary)

        # Ordenar: primero DD SRL, luego D y CIA
        summaries.sort(key=lambda s: (
            0 if "Dario" in s.empresa else 1,
            s.banco
        ))

        logger.info(f"Resúmenes generados: {len(summaries)} cuentas")
        return summaries

    def generate_caja_entries(
        self,
        transactions: List[Transaction],
        reference_date: Optional[date] = None,
    ) -> List[CajaEntry]:
        """
        Genera entradas para CAJA FÁBRICA DIGITAL.
        Extrae gastos bancarios y movimientos significativos del día.
        """
        if not transactions:
            return []

        if reference_date:
            ref = reference_date
        else:
            ref = self._most_recent_date(transactions)

        # Filtrar solo del día de referencia y solo movimientos con categoría
        day_txs = [
            tx for tx in transactions
            if (tx.fecha == ref or ref is None)
            and tx.categoria_codigo is not None
            and tx.importe_neto != 0
        ]

        entries: List[CajaEntry] = []
        for tx in day_txs:
            entry = CajaEntry(
                dia         = tx.fecha.day if tx.fecha else 0,
                fecha       = tx.fecha,
                nro_tipo    = tx.categoria_codigo,
                tipo        = tx.categoria_nombre,
                importe     = abs(tx.importe_neto),
                descripcion = tx.descripcion[:50] if tx.descripcion else "",
                canal       = tx.canal or _infer_canal(tx),
                empresa     = tx.empresa,
                banco       = tx.banco,
            )
            entries.append(entry)

        logger.info(f"Entradas de caja generadas: {len(entries)}")
        return entries

    def _most_recent_date(self, txs: List[Transaction]) -> Optional[date]:
        """Retorna la fecha más reciente con transacciones."""
        dates = [tx.fecha for tx in txs if tx.fecha is not None]
        return max(dates) if dates else None


def _infer_canal(tx: Transaction) -> str:
    """Infiere el canal de pago desde la descripción si no está disponible."""
    desc = (tx.descripcion or "").upper()
    if "TRANSFER" in desc or "TRANSFERENCIA" in desc:
        return "Transfer"
    if "CHEQUE" in desc or "ECHEQ" in desc:
        return "Cheque"
    if "EFECTIVO" in desc:
        return "Efectivo"
    if "MERCADO PAGO" in desc or "MP" in desc:
        return "Transfer"
    return "Transfer"
