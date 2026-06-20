# app/config.py
# ARGUS — Automated Reconciliation & General Unified System
# Powered by McFlow
#
# Configuration based on REAL client files — Delfabro group.
# Updated: added CRESIUM, fixed Galicia sign, updated income categories.

from typing import Dict, Any

APP_NAME    = "ARGUS"
APP_SUBTITLE = "Powered by McFlow"
APP_VERSION = "1.1.0"
WINDOW_SIZE = "1040x700"

# ── Bank sheet mapping ───────────────────────────────────────────────────────
# Keys:
#   company    : company that owns the account
#   bank       : display bank name
#   header_row : 1-based row index of the column header row
#   data_row   : 1-based first row with actual transaction data
#   format     : normalizer key
#   columns    : original_header → normalized_field

SHEET_CONFIG: Dict[str, Dict[str, Any]] = {

    # ── DD SRL (blue sheets) ──────────────────────────────────────────────────

    "ICBC dd srl": {
        "company": "Dario A. Delfabro S.R.L.",
        "bank": "ICBC",
        "header_row": 5,
        "data_row": 6,
        "format": "ICBC",
        # ICBC: debito column comes as NEGATIVE values, credito as POSITIVE.
        # net = credito + debito  (debito is already negative, so this is correct)
        "columns": {
            "Fecha contable":            "fecha",
            "Cod de Concepto":           "cod_concepto",
            "Concepto":                  "descripcion",
            "Debito en $":               "debito_raw",   # negative value from bank
            "Credito en $":              "credito_raw",  # positive value from bank
            "Saldo en $":                "saldo",
            "Informacion Complementaria":"detalle",
            "Nro de cheque":             "nro_cheque",
            "Canal":                     "canal",
            "tipo concepto":             "tipo_concepto",
            "CONCEPTO2":                 "categoria_codigo",
        },
    },

    "MP fondo azul": {
        "company": "Dario A. Delfabro S.R.L.",
        "bank": "Mercado Pago Gerencia (Fondo Azul)",
        "header_row": 5,
        "data_row": 6,
        "format": "MP",
        "columns": {
            "Fecha":       "fecha",
            "Descripción": "descripcion",
            "ID de la":    "nro_referencia",
            "Valor":       "importe_neto",  # signed: negative=debit, positive=credit
            "Saldo":       "saldo",
            "CATEGORÍA":   "categoria_codigo",
        },
    },

    "MP fondo blanco": {
        "company": "Dario A. Delfabro S.R.L.",
        "bank": "Mercado Pago Ventas (Fondo Blanco)",
        "header_row": 5,
        "data_row": 6,
        "format": "MP",
        "columns": {
            "Fecha":       "fecha",
            "Descripción": "descripcion",
            "ID de la":    "nro_referencia",
            "Valor":       "importe_neto",
            "Saldo":       "saldo",
            "CATEGORÍA":   "categoria_codigo",
        },
    },

    "BBVA dd srl 486": {
        "company": "Dario A. Delfabro S.R.L.",
        "bank": "BBVA 486",
        "header_row": 5,
        "data_row": 6,
        "format": "BBVA",
        # BBVA: Crédito positive, Débito negative
        "columns": {
            "Fecha":            "fecha",
            "Fecha Valor":      "fecha_valor",
            "Concepto":         "descripcion",
            "Codigo":           "cod_concepto",
            "Número Documento": "nro_referencia",
            "Oficina":          "sucursal",
            "Crédito":          "credito_raw",
            "Débito":           "debito_raw",
            "Detalle":          "detalle",
            "Saldo disponible": "saldo",
            "CATEGORÍA":        "categoria_codigo",
        },
    },

    "BBVA dd srl 487": {
        "company": "Dario A. Delfabro S.R.L.",
        "bank": "BBVA 487",
        "header_row": 5,
        "data_row": 6,
        "format": "BBVA",
        "columns": {
            "Fecha":            "fecha",
            "Fecha Valor":      "fecha_valor",
            "Concepto":         "descripcion",
            "Codigo":           "cod_concepto",
            "Número Documento": "nro_referencia",
            "Oficina":          "sucursal",
            "Crédito":          "credito_raw",
            "Débito":           "debito_raw",
            "Detalle":          "detalle",
            "Saldo disponible": "saldo",
            "CATEGORÍA":        "categoria_codigo",
        },
    },

    "Bancor dd srl": {
        "company": "Dario A. Delfabro S.R.L.",
        "bank": "Bancor",
        "header_row": 5,
        "data_row": 6,
        "format": "BANCOR",
        # Bancor: headers have trailing spaces — matched via strip() in normalizer
        "columns": {
            "Fecha     ":          "fecha",
            "Nro.Comprobante     ":"nro_referencia",
            "Concepto                                          ": "descripcion",
            "Descripcion                                                                                                                     ": "detalle",
            "Monto               ":"importe_neto",  # signed
            "Saldo Parcial       ":"saldo",
            "CATEGORÍA":           "categoria_codigo",
        },
    },

    # ── NEW: Cresium DD SRL ───────────────────────────────────────────────────
    "CRESIUM dd srl": {
        "company": "Dario A. Delfabro S.R.L.",
        "bank": "Cresium",
        "header_row": 5,
        "data_row": 8,   # Cresium has blank rows 6–7, data starts at row 8
        "format": "CRESIUM",
        # Cresium: single signed Monto column. IMPUESTO column is ignored for now.
        "columns": {
            "FECHA DE ENVIO":    "fecha",
            "MOVIMIENTO":        "descripcion",
            "RAZÓN SOCIAL / NOMBRE Y APELLIDO": "detalle",
            "CUIT":              "nro_referencia",
            "Monto               ": "importe_neto",  # signed: negative=debit
            "Saldo Parcial       ": "saldo",
            "CATEGORÍA DE TRANSACCIÓN": "tipo_concepto",
            "MOTIVO":            "cod_concepto",
            "CATEGORÍA":         "categoria_codigo",
            # "IMPUESTO AL DÉBITO / LEY N 25.413" — ignored for now (future wave)
        },
    },

    # ── D y CIA (yellow sheets) ───────────────────────────────────────────────

    "Nacion Y CIA": {
        "company": "Delfabro y Cia S.R.L.",
        "bank": "Banco Nación",
        "header_row": 5,
        "data_row": 6,
        "format": "NACION",
        "columns": {
            "Fecha":       "fecha",
            "Comprobante": "nro_referencia",
            "Concepto":    "descripcion",
            "Importe":     "importe_neto",  # signed
            "Saldo":       "saldo",
            "CATEGORÍA":   "categoria_codigo",
        },
    },

    "ICBC y cia": {
        "company": "Delfabro y Cia S.R.L.",
        "bank": "ICBC",
        "header_row": 5,
        "data_row": 6,
        "format": "ICBC",
        "columns": {
            "Fecha contable":            "fecha",
            "Cod de Concepto":           "cod_concepto",
            "Concepto":                  "descripcion",
            "Debito en $":               "debito_raw",
            "Credito en $":              "credito_raw",
            "Saldo en $":                "saldo",
            "Informacion Complementaria":"detalle",
            "Nro de cheque":             "nro_cheque",
            "Canal":                     "canal",
            "CATEGORÍA":                 "categoria_codigo",
        },
    },

    "BBVA y cia 407": {
        "company": "Delfabro y Cia S.R.L.",
        "bank": "BBVA 407",
        "header_row": 5,
        "data_row": 6,
        "format": "BBVA",
        "columns": {
            "Fecha":            "fecha",
            "Fecha Valor":      "fecha_valor",
            "Concepto":         "descripcion",
            "Codigo":           "cod_concepto",
            "Número Documento": "nro_referencia",
            "Oficina":          "sucursal",
            "Crédito":          "credito_raw",
            "Débito":           "debito_raw",
            "Detalle":          "detalle",
            "Saldo disponible": "saldo",
            "CATEGORÍA":        "categoria_codigo",
        },
    },

    "BBVA y cia 151": {
        "company": "Delfabro y Cia S.R.L.",
        "bank": "BBVA 151",
        "header_row": 5,
        "data_row": 6,
        "format": "BBVA",
        "columns": {
            "Fecha":            "fecha",
            "Fecha Valor":      "fecha_valor",
            "Concepto":         "descripcion",
            "Codigo":           "cod_concepto",
            "Número Documento": "nro_referencia",
            "Oficina":          "sucursal",
            "Crédito":          "credito_raw",
            "Débito":           "debito_raw",
            "Detalle":          "detalle",
            "Saldo disponible": "saldo",
            "CATEGORÍA":        "categoria_codigo",
        },
    },

    "GALICIA y cia": {
        "company": "Delfabro y Cia S.R.L.",
        "bank": "Galicia Más",
        "header_row": 5,
        "data_row": 6,
        "format": "GALICIA",
        # IMPORTANT: Galicia exports ALL values as positive (+), including debits.
        # The normalizer must invert the debit column sign manually.
        "columns": {
            "Fecha":                "fecha",
            "Tipo operación":       "tipo_concepto",
            "Comprobante":          "nro_referencia",
            "Descripción":          "descripcion",
                "Débito":               "debito_raw",   # always positive — inverted in normalizer
            "Crédito":              "credito_raw",  # always positive
            "Descripción Completa": "detalle",
            "CATEGORÍA":            "categoria_codigo",
        },
    },
}

# Sheets that are not bank accounts — skipped during parsing
NON_BANK_SHEETS = {
    "CONCILICIACION", "CONCILIACION",
    "CATEGORIAS CONTABLES", "Explicacion"
}

# ── Category classification rules ────────────────────────────────────────────

# Income categories: money enters the company (COBRO)
# Categories 25-30 are income. All others (1-24, 31-38) are expenses.
# Exception: 39 = INTERNAL TRANSFER (money moves between accounts, not in or out)
INCOME_CATEGORIES  = {25, 26, 27, 28, 29, 30}
EXPENSE_CATEGORIES = set(range(1, 25)) | set(range(31, 39))  # 1-24 + 31-38
INTERNAL_CATEGORY  = 39

# ── Human error detection rules ───────────────────────────────────────────────
# A human categorization error occurs when:
#   - A DEBIT (money out) is assigned an income category (25-30) → should be expense
#   - A CREDIT (money in) is assigned an expense category (1-24, 31-38) → should be income
# Category 39 (internal transfer) is always excluded from error detection.

# ── Company UI colors ─────────────────────────────────────────────────────────
COMPANY_COLORS = {
    "Dario A. Delfabro S.R.L.": "#3B8BD4",
    "Delfabro y Cia S.R.L.":    "#E8A020",
}
