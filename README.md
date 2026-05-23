# ARGUS Platform — Wave 3

> **Sistema de Reconciliación Bancaria Automatizada**  
> Delfabro Group · v3.0.0 · 2026

```
■ ARGUS v3.0.0 ■ RECONCILIACIÓN BANCARIA ■ DELFABRO GROUP [root@argus:~$]
```

---

## ¿Qué es ARGUS?

ARGUS es un sistema web de automatización financiera que reemplaza horas de trabajo manual diario. Procesa extractos bancarios de **12 cuentas en 7 bancos distintos**, normaliza los datos, detecta errores humanos de categorización, y genera reportes listos para usar — todo en menos de 2 minutos.

### El problema que resuelve

Antes de ARGUS, el equipo de finanzas de Delfabro pasaba horas cada día:
- Copiando manualmente transacciones de 11 planillas Excel distintas
- Asignando categorías contables a mano (40 categorías posibles)
- Construyendo resúmenes bancarios diarios
- Preparando exportaciones para el sistema ERP Coliseo
- Detectando errores de clasificación manualmente

**ARGUS hace todo eso automáticamente.**

---

## 📋 Cómo usarlo (Guía de Usuario)

### Acceso
```
https://argusdelfabro2026.github.io/ArgusPlatform/
```

No requiere instalación. Solo un navegador web.

---

### PASO 1 — Movimientos Bancarios

**Qué hace:** Normaliza y clasifica todas las transacciones bancarias del día.

1. Hacer click en **`+ NUEVO RUN`** en la barra superior
2. En el panel **[1] MOVIMIENTOS**, hacer click en **"Seleccionar Movimientos.xlsx"**
3. Seleccionar el archivo `Movimientos.xlsx` del sistema (contiene todas las cuentas bancarias)
4. Hacer click en **▶ EJECUTAR**
5. Observar el terminal en tiempo real mientras procesa cada cuenta
6. Al finalizar, aparece el botón **↓ DESCARGAR** para obtener el Excel normalizado

**Qué genera:** `argus_movimientos_normalizados_[fecha].xlsx`
- Todas las transacciones normalizadas con colores por empresa y tipo
- Alertas de errores humanos de categorización resaltadas
- Resumen por cuenta bancaria

---

### PASO 2 — Conciliación ERP *(opcional)*

**Qué hace:** Cruza las transacciones bancarias contra los registros del ERP Coliseo.

> ⚠️ Requiere completar el Paso 1 primero.

1. Subir `COBROS.xlsx` (ingresos registrados en Coliseo)
2. Subir `PAGOS.xlsx` (pagos registrados en Coliseo)
3. Hacer click en **▶ EJECUTAR**

**Qué genera:** `argus_conciliacion_[fecha].xlsx`
- Estado por transacción: `CONCILIADO` / `PENDIENTE BANCO` / `PENDIENTE ERP`

---

### PASO 3 — Caja Fábrica Digital *(opcional)*

**Qué hace:** Genera las entradas listas para copiar al libro de caja mensual.

> ⚠️ Requiere completar el Paso 1 primero.

1. Subir `Caja.xlsx` (libro de caja mensual)
2. Hacer click en **▶ EJECUTAR**

**Qué genera:** `argus_export_caja_[fecha].xlsx`
- Entradas de caja listas para pegar en el archivo mensual

---

### Dashboard — Historial de Runs

Desde el **DASHBOARD** se puede:
- Ver todos los runs anteriores (últimos 3 meses)
- Ver el detalle de transacciones de cada run
- Re-descargar los Excel generados
- Ver estadísticas: total de transacciones procesadas, alertas detectadas

---

### Bancos soportados

| Empresa | Banco | Cuenta |
|---|---|---|
| DD SRL | ICBC | ICBC dd srl |
| DD SRL | Mercado Pago | MP fondo azul |
| DD SRL | Mercado Pago | MP fondo blanco |
| DD SRL | BBVA | BBVA dd srl 486 |
| DD SRL | BBVA | BBVA dd srl 487 |
| DD SRL | Bancor | Bancor dd srl |
| DD SRL | Cresium | CRESIUM dd srl |
| D y CIA | Banco Nación | Nacion Y CIA |
| D y CIA | ICBC | ICBC y cia |
| D y CIA | BBVA | BBVA y cia 407 |
| D y CIA | BBVA | BBVA y cia 151 |
| D y CIA | Galicia | GALICIA y cia |

---

## 🏗️ Arquitectura Técnica

### Stack

```
┌─────────────────────────────────────────────────────┐
│  FRONTEND                                           │
│  Next.js 14 (Static Export)                        │
│  GitHub Pages → argusdelfabro2026.github.io        │
│  Terminal UI · JetBrains Mono · Tailwind CSS       │
└──────────────────────┬──────────────────────────────┘
                       │ REST + Server-Sent Events (SSE)
┌──────────────────────▼──────────────────────────────┐
│  BACKEND                                            │
│  FastAPI (Python 3.11)                              │
│  HuggingFace Spaces → Argusdelfabro-argus-api.hf.space │
│  Processing pipeline · SSE streaming               │
└──────────────────────┬──────────────────────────────┘
                       │ supabase-py SDK
┌──────────────────────▼──────────────────────────────┐
│  DATABASE + STORAGE                                 │
│  Supabase (PostgreSQL + Storage)                   │
│  arjymhqzsdnktfojftpi.supabase.co                  │
│  Auto-purge: runs > 3 meses eliminados             │
└─────────────────────────────────────────────────────┘
```

### CI/CD

```
git push origin main
        │
        ├── backend/** changed?
        │   └── GitHub Actions → push to HuggingFace Space → redeploy
        │
        └── frontend/** changed?
            └── GitHub Actions → npm run build → push to gh-pages branch → live
```

---

### Estructura del Proyecto

```
ArgusPlatform/
├── backend/                        # FastAPI (Python)
│   ├── app/
│   │   ├── main.py                 # FastAPI app + CORS
│   │   ├── config.py               # Bank configs (12 accounts, 7 formats)
│   │   ├── api/routes/
│   │   │   ├── process.py          # SSE pipeline endpoints (Paso 1, 2, 3)
│   │   │   ├── runs.py             # History endpoints
│   │   │   └── files.py            # Excel download endpoints
│   │   ├── core/
│   │   │   ├── supabase.py         # Supabase client
│   │   │   └── config.py           # Settings (env vars)
│   │   ├── db/queries.py           # All DB operations
│   │   ├── services/               # Core processing (Wave 1+2 logic)
│   │   │   ├── loader.py           # Excel file loader
│   │   │   ├── normalizer.py       # 7-format bank normalizer
│   │   │   ├── processor.py        # Pipeline orchestrator
│   │   │   ├── summary.py          # Daily summaries generator
│   │   │   ├── exporter.py         # Excel report generator
│   │   │   └── reconciler.py       # ERP reconciliation (Wave 2)
│   │   └── models/                 # Dataclasses
│   ├── Dockerfile                  # HuggingFace deployment
│   ├── Procfile                    # uvicorn run command
│   ├── runtime.txt                 # python-3.11.0
│   └── requirements.txt
│
├── frontend/                       # Next.js 14
│   ├── app/
│   │   ├── page.tsx                # Dashboard (run history)
│   │   ├── run/page.tsx            # Pipeline (3-step + terminal)
│   │   └── globals.css             # Terminal aesthetic styles
│   ├── components/
│   │   ├── NavBar.tsx              # Top bar with uptime counter
│   │   ├── TerminalLog.tsx         # Real-time SSE log viewer
│   │   ├── StepPanel.tsx           # Pipeline step card
│   │   ├── ProgressBar.tsx         # Block-style progress [████──]
│   │   └── RunCard.tsx             # History card (ls -la style)
│   ├── lib/
│   │   ├── api.ts                  # REST client + SSE streaming
│   │   ├── types.ts                # TypeScript interfaces
│   │   └── useUptime.ts            # Live uptime hook
│   └── next.config.js
│
├── supabase/migrations/
│   └── 20260523000000_initial.sql  # Full schema + pg_cron purge
│
└── .github/workflows/
    ├── deploy-backend.yml          # → HuggingFace Spaces
    └── deploy-frontend.yml         # → GitHub Pages
```

---

### Schema de Base de Datos

```sql
runs              -- Una por sesión de procesamiento
transactions      -- Todas las transacciones normalizadas (Paso 1)
bank_summaries    -- Resumen diario por cuenta (Paso 1)
reconciliation_lines -- Conciliación ERP vs banco (Paso 2)
caja_entries      -- Entradas de caja (Paso 3)
output_files      -- Archivos Excel generados (Storage paths)
```

**Retención:** Todos los datos se eliminan automáticamente a los 3 meses via `pg_cron`.

---

### Normalización Bancaria

El corazón del sistema. Cada banco exporta en un formato diferente:

| Banco | Quirk crítico |
|---|---|
| ICBC | Débitos exportados como valores NEGATIVOS |
| BBVA | Débitos exportados como valores NEGATIVOS |
| Galicia | TODOS los valores positivos (débitos deben negarse manualmente) |
| Mercado Pago | Columna `Valor` única con signo (negativo=débito) |
| Bancor | Columna `Monto` con signo + headers con espacios en trailing |
| Banco Nación | Columna `Importe` con signo |
| Cresium | Datos desde fila 8 (filas 6-7 vacías), categoría en col 11 |

**Detección de errores humanos:**
- `Rule 0`: Sin categoría asignada → `⚠ FALTA CATEGORIZAR`
- `Rule A`: Débito con categoría de ingreso (25-30) → `⚠ ERROR HUMANO`
- `Rule B`: Crédito con categoría de egreso (1-24, 31-38) → `⚠ ERROR HUMANO`
- **Excepción:** MP fondo azul cat.37 en créditos = válido (devoluciones ML)

---

## 🚀 Setup Local (Desarrollo)

### Requisitos
- Python 3.11+
- Node.js 20+
- Git

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Completar .env con credenciales de Supabase
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
# NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
npm run dev
```

Abrir: `http://localhost:3000`

### Variables de Entorno

**Backend** (`backend/.env`):
```
SUPABASE_URL=https://arjymhqzsdnktfojftpi.supabase.co
SUPABASE_SERVICE_KEY=sb_secret_...
SUPABASE_ANON_KEY=sb_publishable_...
FRONTEND_URL=http://localhost:3000
```

**Frontend** (`frontend/.env.local`):
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

---

## 🔄 Deploy

Todo es automático via GitHub Actions en cada push a `main`.

| Componente | Plataforma | Trigger |
|---|---|---|
| Backend | HuggingFace Spaces | Cambios en `backend/**` |
| Frontend | GitHub Pages | Cambios en `frontend/**` |

### GitHub Secrets requeridos

| Secret | Descripción |
|---|---|
| `HF_TOKEN` | HuggingFace Access Token (write) |
| `NEXT_PUBLIC_BACKEND_URL` | URL del backend en HuggingFace |

### URLs de Producción

| | URL |
|---|---|
| **App** | https://argusdelfabro2026.github.io/ArgusPlatform/ |
| **API** | https://Argusdelfabro-argus-api.hf.space |
| **API Docs** | https://Argusdelfabro-argus-api.hf.space/docs |

---

## 📊 Métricas del Sistema

| Métrica | Valor |
|---|---|
| Cuentas bancarias soportadas | 12 |
| Formatos bancarios distintos | 7 |
| Empresas | 2 (DD SRL + D y CIA) |
| Categorías contables | 40 |
| Transacciones por run | ~2,773 |
| Tiempo de procesamiento | < 2 minutos |
| Retención de datos | 3 meses |

---

## 🗺️ Roadmap

| Wave | Estado | Descripción |
|---|---|---|
| Wave 1 | ✅ Done | Normalización + Clasificación + Resúmenes + Caja |
| Wave 2 | ✅ Done | Conciliación ERP (COBROS/PAGOS vs banco) |
| Wave 3 | ✅ Done | Web App (FastAPI + Next.js + Supabase) |
| Wave 4 | 🔜 Planned | Dashboard analítico · Gráficos · Tendencias |
| Wave 5 | 🔜 Planned | Notificaciones automáticas · Alertas por email |

---

## 👥 Equipo

| Rol | Contacto |
|---|---|
| Desarrollo | Manuel Ramos |
| Cliente | Delfabro Group |

---

*ARGUS v3.0.0 · Built with FastAPI, Next.js & Supabase · 2026*
