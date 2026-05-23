-- Enable pg_cron extension for auto-purge
create extension if not exists pg_cron;

-- RUNS: one record per processing session
create table if not exists runs (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  status text not null default 'running', -- running | completed | error
  steps_completed int[] default '{}',     -- e.g. {1, 2, 3}
  sheets_processed integer default 0,
  transactions_total integer default 0,
  errors text[] default '{}',
  warnings text[] default '{}'
);

-- TRANSACTIONS: normalized bank transactions from Step 1
create table if not exists transactions (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references runs(id) on delete cascade,
  created_at timestamptz default now(),
  pestana text,
  empresa text,
  banco text,
  fecha date,
  descripcion text,
  detalle text,
  debito numeric(18,2),
  credito numeric(18,2),
  importe_neto numeric(18,2),
  saldo numeric(18,2),
  categoria_codigo integer,
  categoria_nombre text,
  tipo_movimiento text,  -- COBRO | PAGO | INTERNO | SIN CLASIFICAR
  alerta text
);

-- BANK_SUMMARIES: daily summary per account from Step 1
create table if not exists bank_summaries (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references runs(id) on delete cascade,
  created_at timestamptz default now(),
  empresa text,
  banco text,
  pestana text,
  saldo_actual numeric(18,2),
  gastos_dia numeric(18,2),
  intereses_dia numeric(18,2),
  cobros_dia numeric(18,2),
  pagos_dia numeric(18,2),
  movimientos_count integer
);

-- RECONCILIATION_LINES: ERP vs bank reconciliation from Step 2
create table if not exists reconciliation_lines (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references runs(id) on delete cascade,
  created_at timestamptz default now(),
  estado text,  -- CONCILIADO | PENDIENTE BANCO | PENDIENTE ERP
  tipo text,
  fecha_banco date,
  fecha_erp date,
  monto numeric(18,2),
  nombre text,
  banco text,
  comprobante text,
  descripcion text,
  diferencia_dias integer,
  alerta text
);

-- CAJA_ENTRIES: cash register entries from Step 3
create table if not exists caja_entries (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references runs(id) on delete cascade,
  created_at timestamptz default now(),
  dia integer,
  fecha date,
  nro_tipo text,
  tipo text,
  importe numeric(18,2),
  descripcion text,
  canal text,
  empresa text,
  banco text
);

-- OUTPUT_FILES: generated Excel files
create table if not exists output_files (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references runs(id) on delete cascade,
  created_at timestamptz default now(),
  step integer not null,           -- 1, 2, or 3
  filename text not null,
  storage_path text not null       -- path in Supabase Storage bucket
);

-- INDEXES for performance
create index if not exists idx_transactions_run_id on transactions(run_id);
create index if not exists idx_transactions_empresa on transactions(empresa);
create index if not exists idx_transactions_tipo on transactions(tipo_movimiento);
create index if not exists idx_reconciliation_run_id on reconciliation_lines(run_id);
create index if not exists idx_reconciliation_estado on reconciliation_lines(estado);
create index if not exists idx_caja_run_id on caja_entries(run_id);
create index if not exists idx_output_files_run_id on output_files(run_id);
create index if not exists idx_runs_created_at on runs(created_at);

-- AUTO-PURGE: delete runs older than 3 months (cascade deletes all related data)
-- Runs daily at 2:00 AM UTC
select cron.schedule(
  'purge-old-runs',
  '0 2 * * *',
  $$
    delete from runs
    where created_at < now() - interval '3 months';
  $$
);

-- ROW LEVEL SECURITY: disabled (no auth per design decision)
-- All tables are publicly accessible (internal tool only)
alter table runs disable row level security;
alter table transactions disable row level security;
alter table bank_summaries disable row level security;
alter table reconciliation_lines disable row level security;
alter table caja_entries disable row level security;
alter table output_files disable row level security;
