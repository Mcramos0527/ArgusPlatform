# app/services/caja_dir_loader.py
# Loads Caja Dirección Excel file and filters records where canal == 1 (Transfer).

import logging
from datetime import date
from typing import Dict, List, Optional, Tuple

import openpyxl

logger = logging.getLogger("argus.caja_dir")

# Column name aliases (case-insensitive exact match)
_FECHA_NAMES     = {"fecha", "date", "fecha_movimiento", "fecha_mov", "fecha mov"}
_CATEGORIA_NAMES = {"categoria", "categoría", "concepto", "descripcion", "descripción", "tipo", "rubro"}
_IMPORTE_NAMES   = {"importe", "monto", "amount", "total", "haber", "debe"}
_CANAL_NAMES     = {"canal", "channel", "tipo_canal", "tipo canal"}


def _detect_columns(header_row: tuple) -> Dict[str, int]:
    """Map logical field names to column indices from a header tuple."""
    mapping: Dict[str, int] = {}
    for idx, cell in enumerate(header_row):
        if cell is None:
            continue
        name = str(cell).strip().lower()
        if name in _FECHA_NAMES and "fecha" not in mapping:
            mapping["fecha"] = idx
        if name in _CATEGORIA_NAMES and "categoria" not in mapping:
            mapping["categoria"] = idx
        if name in _IMPORTE_NAMES and "importe" not in mapping:
            mapping["importe"] = idx
        if name in _CANAL_NAMES and "canal" not in mapping:
            mapping["canal"] = idx
    return mapping


def load_caja_direccion(path: str) -> Tuple[List[dict], List[str]]:
    """
    Load Caja Dirección Excel and filter by canal == 1 (Transfer).

    Returns:
        rows      — list of dicts with keys: fecha, categoria, importe
        warnings  — non-fatal issues detected during load
    """
    warnings: List[str] = []

    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:
        return [], [f"No se pudo abrir Caja Dirección: {exc}"]

    ws = wb.active
    all_rows = list(ws.iter_rows(values_only=True))
    if not all_rows:
        return [], ["El archivo Caja Dirección está vacío"]

    # Find first non-empty row as header
    header_row: Optional[tuple] = None
    data_start = 0
    for i, row in enumerate(all_rows):
        if any(cell is not None for cell in row):
            header_row = row
            data_start = i + 1
            break

    if header_row is None:
        return [], ["No se encontró encabezado en Caja Dirección"]

    col_map = _detect_columns(header_row)
    logger.info(f"Caja Dir — columnas detectadas: {col_map}")

    if "importe" not in col_map:
        return [], ["No se encontró columna de importe/monto en Caja Dirección"]
    if "categoria" not in col_map:
        warnings.append("Sin columna de categoría detectada — se usará texto vacío")
    if "canal" not in col_map:
        warnings.append("Sin columna 'Canal' — se incluirán todos los registros sin filtrar")

    rows: List[dict] = []
    total = 0
    skipped = 0

    for row in all_rows[data_start:]:
        if all(cell is None for cell in row):
            continue
        total += 1

        # Filter: canal must equal 1 (Transfer)
        if "canal" in col_map:
            canal_val = row[col_map["canal"]]
            try:
                if int(canal_val) != 1:
                    skipped += 1
                    continue
            except (TypeError, ValueError):
                skipped += 1
                continue

        # Parse fecha
        fecha_raw = row[col_map["fecha"]] if "fecha" in col_map else None
        fecha: Optional[date] = None
        if isinstance(fecha_raw, date):
            fecha = fecha_raw
        elif hasattr(fecha_raw, "date"):  # datetime object
            fecha = fecha_raw.date()

        # Parse categoria
        cat_idx = col_map.get("categoria")
        categoria = (
            str(row[cat_idx]).strip()
            if (cat_idx is not None and row[cat_idx] is not None)
            else ""
        )

        # Parse importe (absolute value for comparison)
        importe = 0.0
        try:
            raw = row[col_map["importe"]]
            if raw is not None:
                importe = float(raw)
        except (TypeError, ValueError):
            pass

        rows.append({"fecha": fecha, "categoria": categoria, "importe": importe})

    if "canal" in col_map:
        logger.info(
            f"Caja Dir — total: {total}, filtrados (canal≠1): {skipped}, procesados: {len(rows)}"
        )
    else:
        logger.info(f"Caja Dir — total procesados: {len(rows)}")

    return rows, warnings
