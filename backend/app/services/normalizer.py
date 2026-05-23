# app/services/normalizer.py
# Core normalization engine — converts 7 different bank export formats
# into a single unified Transaction model.
#
# Bank formats handled:
#   ICBC    — separate debit/credit columns, debits come as NEGATIVE values
#   BBVA    — separate debit/credit columns, debits come as NEGATIVE values
#   GALICIA — separate debit/credit columns, but ALL values are POSITIVE
#             (debits must be manually negated)
#   MP      — single signed Valor column (negative=debit, positive=credit)
#   BANCOR  — single signed Monto column (headers have trailing spaces)
#   NACION  — single signed Importe column
#   CRESIUM — single signed Monto column, data starts at row 8

import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from app.config import (
    SHEET_CONFIG, INCOME_CATEGORIES, EXPENSE_CATEGORIES, INTERNAL_CATEGORY
)
from app.models import Transaction

logger = logging.getLogger("argus.normalizer")


# ── Date parsing ──────────────────────────────────────────────────────────────

def _parse_date(value) -> Optional[date]:
    """Safely parse any date format into a date object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        value = value.strip()
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d",
                    "%d-%m-%y", "%d/%m/%y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _safe_float(value) -> float:
    """Convert any value to float safely, returning 0.0 on failure."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(" ", "").replace("$", "")
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0


def _safe_str(value) -> str:
    """Convert to clean string, discarding Excel formulas."""
    if value is None:
        return ""
    s = str(value).strip()
    return "" if s.startswith("=") else s


def _parse_cat_code(value) -> Optional[int]:
    """Extract integer category code from cell value."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    if isinstance(value, str):
        try:
            return int(float(value.strip()))
        except ValueError:
            return None
    return None


# ── Header index builder ──────────────────────────────────────────────────────

def build_headers(header_row: tuple) -> Dict[str, int]:
    """Build {column_name: index} dict from a header row tuple."""
    return {str(cell): idx for idx, cell in enumerate(header_row) if cell is not None}


def _get(row: tuple, headers: Dict[str, int], key: str):
    """Get cell value by column name."""
    idx = headers.get(key)
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def _get_stripped(row: tuple, headers: Dict[str, int], key: str):
    """Get cell value by column name, matching with .strip() (for Bancor/Cresium)."""
    for h_key, idx in headers.items():
        if str(h_key).strip() == key.strip() and idx < len(row):
            return row[idx]
    return None


# ── Movement type classification ──────────────────────────────────────────────

def _classify_movement(tx: Transaction) -> str:
    """
    Classify transaction as COBRO, PAGO, INTERNO, or SIN CLASIFICAR.

    Rules (from client spec):
    - Category 39                        → INTERNO (internal transfer)
    - Categories 25-30                   → COBRO (income)
    - Categories 1-24, 31-38             → PAGO (expense)
    - Fallback: sign of importe_neto     → COBRO if positive, PAGO if negative
    """
    cat = tx.categoria_codigo

    if cat == INTERNAL_CATEGORY:
        return "INTERNO"

    if cat in INCOME_CATEGORIES:
        return "COBRO"

    if cat in EXPENSE_CATEGORIES:
        return "PAGO"

    # Fallback: use sign
    if tx.importe_neto > 0:
        return "COBRO"
    if tx.importe_neto < 0:
        return "PAGO"

    return "SIN CLASIFICAR"


# ── Human error detection ─────────────────────────────────────────────────────

# MP fondo azul exception: category 37 on credits is valid (sale returns from ML)
# This is the only bank where cat 37 credits are NOT a human error.
MP_FONDO_AZUL_CREDIT_EXCEPTIONS = {37}


def _detect_human_error(tx: Transaction) -> str:
    """
    Detect human categorization errors per client spec:

    Rule 0 — Missing category:
      If category is None → "FALTA CATEGORIZAR" (applies to ALL banks)

    Rule A — Debit assigned income category:
      If money went OUT (debit > 0) but category is income (25-30) → human error.
      Exception: category 39 (internal transfer) is always excluded.

    Rule B — Credit assigned expense category:
      If money came IN (credit > 0) but category is expense (1-24, 31-38) → human error.
      Exception: MP fondo azul cat 37 credits are valid (Mercado Libre sale returns).

    Returns an alert string or empty string if no error.
    """
    cat   = tx.categoria_codigo
    banco = tx.pestaña

    # Rule 0: no category assigned — applies to all banks
    if cat is None:
        return "⚠ FALTA CATEGORIZAR"

    # Internal transfers are never errors
    if cat == INTERNAL_CATEGORY:
        return ""

    debit_amount  = tx.debito
    credit_amount = tx.credito

    # Rule A: debit transaction with income category
    if debit_amount > 0 and cat in INCOME_CATEGORIES:
        return f"⚠ ERROR HUMANO: débito con categoría de ingreso (cat {cat})"

    # Rule B: credit transaction with expense category
    # Exception: MP fondo azul cat 37 credits = valid sale returns from Mercado Libre
    if credit_amount > 0 and cat in EXPENSE_CATEGORIES:
        if banco == "MP fondo azul" and cat in MP_FONDO_AZUL_CREDIT_EXCEPTIONS:
            return ""
        return f"⚠ ERROR HUMANO: crédito con categoría de egreso (cat {cat})"

    return ""


# ── Bank-specific normalizers ─────────────────────────────────────────────────

def _normalize_icbc(row: tuple, headers: Dict[str, int], cfg: dict) -> Optional[Transaction]:
    """
    ICBC format: separate Debito en $ and Credito en $ columns.
    IMPORTANT: ICBC exports debits as NEGATIVE values in the debit column.
    So net = credito_raw + debito_raw  (debito_raw is already negative).
    """
    fecha = _parse_date(_get(row, headers, "Fecha contable"))
    if fecha is None:
        return None

    debito_raw  = _safe_float(_get(row, headers, "Debito en $"))   # negative or 0
    credito_raw = _safe_float(_get(row, headers, "Credito en $"))  # positive or 0

    # Net = credit + debit (debit already negative from bank)
    neto    = credito_raw + debito_raw
    debito  = abs(debito_raw) if debito_raw < 0 else 0.0
    credito = credito_raw if credito_raw > 0 else 0.0

    return Transaction(
        pestaña          = cfg.get("sheet_name", ""),
        empresa          = cfg["company"],
        banco            = cfg["bank"],
        fecha            = fecha,
        descripcion      = _safe_str(_get(row, headers, "Concepto")),
        detalle          = _safe_str(_get(row, headers, "Informacion Complementaria")),
        debito           = debito,
        credito          = credito,
        importe_neto     = neto,
        saldo            = _safe_float(_get(row, headers, "Saldo en $")),
        nro_cheque       = _safe_str(_get(row, headers, "Nro de cheque")),
        cod_concepto     = _safe_str(_get(row, headers, "Cod de Concepto")),
        canal            = _safe_str(_get(row, headers, "Canal")),
        tipo_concepto    = _safe_str(_get(row, headers, "tipo concepto")),
        # Category code at col 10 — read by fixed index (CONCEPTO2 col 11 = name, not code)
        categoria_codigo = _parse_cat_code(row[10] if len(row) > 10 else None),
    )


def _normalize_bbva(row: tuple, headers: Dict[str, int], cfg: dict) -> Optional[Transaction]:
    """
    BBVA format: separate Crédito and Débito columns.
    BBVA exports credits as positive and debits as negative.
    """
    fecha = _parse_date(_get(row, headers, "Fecha"))
    if fecha is None:
        return None

    credito_raw = _safe_float(_get(row, headers, "Crédito"))
    debito_raw  = _safe_float(_get(row, headers, "Débito"))

    neto    = credito_raw + debito_raw
    debito  = abs(debito_raw) if debito_raw < 0 else 0.0
    credito = credito_raw if credito_raw > 0 else 0.0

    return Transaction(
        pestaña          = cfg.get("sheet_name", ""),
        empresa          = cfg["company"],
        banco            = cfg["bank"],
        fecha            = fecha,
        fecha_valor      = _parse_date(_get(row, headers, "Fecha Valor")),
        descripcion      = _safe_str(_get(row, headers, "Concepto")),
        detalle          = _safe_str(_get(row, headers, "Detalle")),
        cod_concepto     = _safe_str(_get(row, headers, "Codigo")),
        nro_referencia   = _safe_str(_get(row, headers, "Número Documento")),
        sucursal         = _safe_str(_get(row, headers, "Oficina")),
        credito          = credito,
        debito           = debito,
        importe_neto     = neto,
        saldo            = _safe_float(_get(row, headers, "Saldo disponible")),
        # Category code at col 10 — no header in row 5, read by fixed index
        categoria_codigo = _parse_cat_code(row[10] if len(row) > 10 else None),
    )


def _normalize_galicia(row: tuple, headers: Dict[str, int], cfg: dict) -> Optional[Transaction]:
    """
    Galicia format: separate Débito and Crédito columns.
    IMPORTANT: Galicia exports ALL values as POSITIVE (including debits).
    We must manually invert the debit column sign.

    IMPORTANT: Galicia's CATEGORÍA and CONCEPTO columns have NO header in row 5.
    They are always at fixed positions: col 10 = category code, col 11 = concept name.
    We read them directly by index instead of by header name.
    """
    fecha = _parse_date(_get(row, headers, "Fecha"))
    if fecha is None:
        return None

    debito_abs  = _safe_float(_get(row, headers, "Débito"))
    credito_raw = _safe_float(_get(row, headers, "Crédito"))

    if debito_abs > 0:
        neto    = -debito_abs
        debito  = debito_abs
        credito = 0.0
    else:
        neto    = credito_raw
        debito  = 0.0
        credito = credito_raw

    # Read category by fixed column index (no header in row 5)
    cat_code = _parse_cat_code(row[10] if len(row) > 10 else None)

    return Transaction(
        pestaña          = cfg.get("sheet_name", ""),
        empresa          = cfg["company"],
        banco            = cfg["bank"],
        fecha            = fecha,
        descripcion      = _safe_str(_get(row, headers, "Descripción")),
        detalle          = _safe_str(_get(row, headers, "Descripción Completa")),
        tipo_concepto    = _safe_str(_get(row, headers, "Tipo operación")),
        nro_referencia   = _safe_str(_get(row, headers, "Comprobante")),
        debito           = debito,
        credito          = credito,
        importe_neto     = neto,
        categoria_codigo = cat_code,
    )


def _normalize_mp(row: tuple, headers: Dict[str, int], cfg: dict) -> Optional[Transaction]:
    """
    Mercado Pago format: single Valor column (negative=debit, positive=credit).
    """
    fecha = _parse_date(_get(row, headers, "Fecha"))
    if fecha is None:
        return None

    neto    = _safe_float(_get(row, headers, "Valor"))
    debito  = abs(neto) if neto < 0 else 0.0
    credito = neto      if neto > 0 else 0.0

    return Transaction(
        pestaña          = cfg.get("sheet_name", ""),
        empresa          = cfg["company"],
        banco            = cfg["bank"],
        fecha            = fecha,
        descripcion      = _safe_str(_get(row, headers, "Descripción")),
        nro_referencia   = _safe_str(_get(row, headers, "ID de la")),
        debito           = debito,
        credito          = credito,
        importe_neto     = neto,
        saldo            = _safe_float(_get(row, headers, "Saldo")),
        categoria_codigo = _parse_cat_code(_get(row, headers, "CATEGORÍA")),
    )


def _normalize_bancor(row: tuple, headers: Dict[str, int], cfg: dict) -> Optional[Transaction]:
    """
    Bancor format: single signed Monto column. Headers have trailing spaces —
    matched using strip() via _get_stripped().
    """
    fecha = _parse_date(_get_stripped(row, headers, "Fecha"))
    if fecha is None:
        return None

    neto    = _safe_float(_get_stripped(row, headers, "Monto"))
    debito  = abs(neto) if neto < 0 else 0.0
    credito = neto      if neto > 0 else 0.0

    # Category code at col 10 — no header in row 5, read by fixed index
    cat_code_bancor = _parse_cat_code(row[10] if len(row) > 10 else None)

    return Transaction(
        pestaña          = cfg.get("sheet_name", ""),
        empresa          = cfg["company"],
        banco            = cfg["bank"],
        fecha            = fecha,
        descripcion      = _safe_str(_get_stripped(row, headers, "Concepto")),
        detalle          = _safe_str(_get_stripped(row, headers, "Descripcion")),
        nro_referencia   = _safe_str(_get_stripped(row, headers, "Nro.Comprobante")),
        debito           = debito,
        credito          = credito,
        importe_neto     = neto,
        saldo            = _safe_float(_get_stripped(row, headers, "Saldo Parcial")),
        categoria_codigo = cat_code_bancor,
    )


def _normalize_nacion(row: tuple, headers: Dict[str, int], cfg: dict) -> Optional[Transaction]:
    """
    Banco Nación format: single signed Importe column.
    """
    fecha = _parse_date(_get(row, headers, "Fecha"))
    if fecha is None:
        return None

    neto    = _safe_float(_get(row, headers, "Importe"))
    debito  = abs(neto) if neto < 0 else 0.0
    credito = neto      if neto > 0 else 0.0

    # Category code at col 10 — no header in row 5, read by fixed index
    cat_code_nacion = _parse_cat_code(row[10] if len(row) > 10 else None)

    return Transaction(
        pestaña          = cfg.get("sheet_name", ""),
        empresa          = cfg["company"],
        banco            = cfg["bank"],
        fecha            = fecha,
        descripcion      = _safe_str(_get(row, headers, "Concepto")),
        nro_referencia   = _safe_str(_get(row, headers, "Comprobante")),
        debito           = debito,
        credito          = credito,
        importe_neto     = neto,
        saldo            = _safe_float(_get(row, headers, "Saldo")),
        categoria_codigo = cat_code_nacion,
    )


def _normalize_cresium(row: tuple, headers: Dict[str, int], cfg: dict) -> Optional[Transaction]:
    """
    Cresium format: single signed Monto column (negative=debit, positive=credit).
    Data starts at row 8 (rows 6-7 are blank).

    Column layout (fixed positions):
      col 0  FECHA DE ENVIO
      col 1  MOVIMIENTO
      col 2  RAZÓN SOCIAL / NOMBRE Y APELLIDO
      col 3  CUIT
      col 4  Monto (signed)
      col 5  Saldo Parcial
      col 6  CATEGORÍA DE TRANSACCIÓN (bank label — informational only)
      col 7  MOTIVO
      col 10 IMPUESTO AL DÉBITO (ignored for now)
      col 11 CATEGORÍA  ← accounting category code (1-39)
      col 12 CONCEPTO   ← accounting category name
      col 13 DETALLE

    CATEGORÍA (col 11) is the internal company category code.
    CATEGORÍA DE TRANSACCIÓN (col 6) is the bank's own label — ignored for classification.
    """
    fecha = _parse_date(_get_stripped(row, headers, "FECHA DE ENVIO"))
    if fecha is None:
        return None

    neto    = _safe_float(_get_stripped(row, headers, "Monto"))
    debito  = abs(neto) if neto < 0 else 0.0
    credito = neto      if neto > 0 else 0.0

    # Read CATEGORÍA by fixed index (col 11) to avoid confusion with
    # CATEGORÍA DE TRANSACCIÓN (col 6) which is the bank's own label
    cat_code = _parse_cat_code(row[11] if len(row) > 11 else None)

    return Transaction(
        pestaña          = cfg.get("sheet_name", ""),
        empresa          = cfg["company"],
        banco            = cfg["bank"],
        fecha            = fecha,
        descripcion      = _safe_str(_get(row, headers, "MOVIMIENTO")),
        detalle          = _safe_str(_get(row, headers, "RAZÓN SOCIAL / NOMBRE Y APELLIDO")),
        nro_referencia   = _safe_str(_get(row, headers, "CUIT")),
        cod_concepto     = _safe_str(_get(row, headers, "MOTIVO")),
        tipo_concepto    = _safe_str(_get(row, headers, "CATEGORÍA DE TRANSACCIÓN")),
        debito           = debito,
        credito          = credito,
        importe_neto     = neto,
        saldo            = _safe_float(_get_stripped(row, headers, "Saldo Parcial")),
        categoria_codigo = cat_code,
    )


# ── Normalizer registry ───────────────────────────────────────────────────────

NORMALIZERS = {
    "ICBC":    _normalize_icbc,
    "BBVA":    _normalize_bbva,
    "GALICIA": _normalize_galicia,
    "MP":      _normalize_mp,
    "BANCOR":  _normalize_bancor,
    "NACION":  _normalize_nacion,
    "CRESIUM": _normalize_cresium,
}


# ── Main normalizer class ─────────────────────────────────────────────────────

class Normalizer:
    """Converts raw bank sheet rows into unified Transaction objects."""

    def normalize_sheet(
        self,
        sheet_name: str,
        rows: List[tuple],
        categories: Dict[int, str],
    ) -> Tuple[List[Transaction], List[str]]:
        """
        Normalize all rows from a single bank sheet.
        Returns (transactions, warnings).
        """
        cfg = SHEET_CONFIG.get(sheet_name)
        if cfg is None:
            return [], [f"Sheet '{sheet_name}' has no configuration"]

        fmt = cfg["format"]
        normalizer_fn = NORMALIZERS.get(fmt)
        if normalizer_fn is None:
            return [], [f"Format '{fmt}' not implemented for '{sheet_name}'"]

        header_row_idx = cfg["header_row"] - 1
        data_row_start = cfg["data_row"] - 1

        if len(rows) <= header_row_idx:
            return [], [f"'{sheet_name}': header row not found"]

        headers = build_headers(rows[header_row_idx])
        if not headers:
            return [], [f"'{sheet_name}': empty headers"]

        cfg_with_name = {**cfg, "sheet_name": sheet_name}
        transactions: List[Transaction] = []
        warnings: List[str] = []
        skipped = 0

        for row_idx, row in enumerate(rows[data_row_start:], start=data_row_start + 1):
            # Skip fully empty rows
            if all(v is None or str(v).strip() == "" for v in row):
                continue

            try:
                tx = normalizer_fn(row, headers, cfg_with_name)
                if tx is None:
                    skipped += 1
                    continue

                # Enrich with category name
                if tx.categoria_codigo and tx.categoria_codigo in categories:
                    tx.categoria_nombre = categories[tx.categoria_codigo]

                # Classify movement type
                tx.tipo_movimiento = _classify_movement(tx)

                # Detect human categorization errors
                tx.alerta = _detect_human_error(tx)

                transactions.append(tx)

            except Exception as e:
                warnings.append(f"'{sheet_name}' row {row_idx}: {e}")

        logger.info(
            f"'{sheet_name}' ({fmt}): {len(transactions)} transactions, "
            f"{skipped} skipped (no date), {len(warnings)} warnings"
        )
        return transactions, warnings
