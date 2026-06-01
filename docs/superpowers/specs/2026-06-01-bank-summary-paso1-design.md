# Bank Summary in Paso 1 — Design Spec

**Date:** 2026-06-01  
**Status:** Approved  
**Scope:** Backend only — 3 file changes, no new files, no schema changes, no frontend changes

---

## Goal

Wire up the existing-but-disconnected bank summary code so that Paso 1 automatically:
1. Generates a `BankSummary` per bank account from the normalized transactions
2. Adds a "Bancos del Día" second sheet to the Paso 1 Excel output
3. Persists the summaries to the `bank_summaries` Supabase table

---

## Context

All the required code already exists in the codebase but is never called:

| File | What exists | Status |
|---|---|---|
| `app/services/summary.py` | `SummaryGenerator.generate_bank_summaries()` | ✅ Implemented, never called |
| `app/services/exporter.py` | `Exporter.export_bank_summary()` + `_export_summary()` | ✅ Implemented, never called |
| `app/db/queries.py` | `save_summaries()` | ✅ Implemented, never called |
| `supabase/migrations/` | `bank_summaries` table | ✅ Exists in DB |

This is purely a wiring task — no new logic, no new schema.

---

## Architecture

```
run_paso1() in processor.py
  ├── [existing] normalize all transactions
  ├── [NEW] generate_bank_summaries(all_transactions)  → result.summaries
  ├── [existing] export_paso1(transactions, output_folder)
  │     └── [MODIFIED] also receives summaries → adds Sheet 2 "Bancos del Día"
  └── [existing] return result

proceso_paso1() in process.py (API route)
  ├── [existing] queries.save_transactions(run_id, result.transactions)
  └── [NEW] queries.save_summaries(run_id, result.summaries)
```

---

## File Changes

### 1. `backend/app/services/processor.py`

**Location:** `run_paso1()`, after the transaction normalization loop completes.

**Add after** `result.transactions_total = len(all_transactions)`:
```python
progress("Generando resumen bancario del día...")
result.summaries = self.summarizer.generate_bank_summaries(all_transactions)
progress(f"  → {len(result.summaries)} cuentas resumidas")
```

**Modify** the `export_paso1()` call to pass summaries:
```python
generated = self.exporter.export_paso1(
    transactions=result.transactions,
    summaries=result.summaries,
    output_folder=output_folder,
)
```

---

### 2. `backend/app/services/exporter.py`

**Modify** `export_paso1()` signature:
```python
def export_paso1(
    self,
    transactions: List[Transaction],
    summaries: List[BankSummary],   # NEW parameter
    output_folder: str,
) -> List[str]:
```

**After** `self._export_transactions(transactions, path)`, add a second sheet to the same workbook:
```python
self._add_summary_sheet(path, summaries)
```

**New private method** `_add_summary_sheet(path, summaries)`:
- Opens the existing workbook at `path`
- Adds a new sheet named "Bancos del Día"
- Writes the summary using the existing `_export_summary()` logic (adapted to write into an existing workbook sheet instead of creating a new file)
- Saves the workbook

The sheet layout matches the existing `_export_summary()` output:
- One row per bank account, grouped by empresa
- Columns: Empresa, Banco/Cuenta, Saldo Actual, Cobros del Día, Pagos del Día, Gastos Bancarios, Intereses, Movimientos
- Company separator rows (DD SRL header, D y CIA header)
- Totals row at the bottom

---

### 3. `backend/app/api/routes/process.py`

**Location:** `proceso_paso1()`, inside `event_generator()`, after `queries.save_transactions()`.

**Add:**
```python
if result.summaries:
    queries.save_summaries(run_id, result.summaries)
    yield _log_event(f"  ✓ {len(result.summaries)} resúmenes bancarios guardados")
```

---

## Output

**Before this change:**
```
argus_movimientos_normalizados_YYYY-MM-DD.xlsx
  └── Sheet: "Movimientos"
```

**After this change:**
```
argus_movimientos_normalizados_YYYY-MM-DD.xlsx
  ├── Sheet 1: "Movimientos"     (unchanged)
  └── Sheet 2: "Bancos del Día"  (NEW)
```

**"Bancos del Día" sheet layout:**

| Empresa | Banco / Cuenta | Saldo Actual | Cobros del Día | Pagos del Día | Gastos Bancarios | Intereses | Movimientos |
|---|---|---|---|---|---|---|---|
| *(DD SRL header row)* | | | | | | | |
| DD SRL | ICBC dd srl | $X | $X | $X | $X | — | N |
| DD SRL | MP Fondo Azul | $X | $X | $X | $X | — | N |
| ... | | | | | | | |
| *(D y CIA header row)* | | | | | | | |
| D y CIA | Nación Argentina | $X | $X | $X | $X | — | N |
| ... | | | | | | | |
| **TOTAL GENERAL** | | **$X** | **$X** | **$X** | | | |

---

## What Does NOT Change

- Frontend — no changes (same download button, same file URL)
- DB schema — `bank_summaries` table already exists
- Paso 2 and Paso 3 — untouched
- `ProcessResult` model — already has a `summaries` field (or add it if missing)
- `summary.py` — no changes
- `queries.py` — no changes

---

## Error Handling

- If `generate_bank_summaries()` returns an empty list (e.g., no transactions), skip the summary sheet and the DB save silently. Paso 1 still completes successfully.
- The summary sheet is non-critical — if `_add_summary_sheet()` fails, log a warning but do not fail the entire Paso 1 run.

---

## Testing

Manual test:
1. Run Paso 1 with a real `Movimientos.xlsx`
2. Download the output Excel
3. Verify two sheets exist: "Movimientos" and "Bancos del Día"
4. Verify "Bancos del Día" has one row per bank account with correct saldo_actual
5. Check Supabase `bank_summaries` table — verify rows were inserted for the run
