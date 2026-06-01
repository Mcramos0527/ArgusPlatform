'use client';

import type { RunStats } from '@/lib/types';

// ── SVG Donut Chart ───────────────────────────────────────────────────────────

function DonutChart({ cobros, pagos, internos, sinClasificar }: {
  cobros: number; pagos: number; internos: number; sinClasificar: number;
}) {
  const total = cobros + pagos + internos + sinClasificar;
  if (total === 0) return null;

  const r = 36;
  const cx = 50;
  const cy = 50;
  const circ = 2 * Math.PI * r;

  const segments = [
    { value: cobros,        color: '#00ff41', label: 'COBRO' },
    { value: pagos,         color: '#ff4444', label: 'PAGO'  },
    { value: internos,      color: '#444466', label: 'INT'   },
    { value: sinClasificar, color: '#ffb000', label: 'S/C'   },
  ].filter(s => s.value > 0);

  let offset = -circ / 4; // start at top

  return (
    <svg viewBox="0 0 100 100" className="w-28 h-28 drop-shadow-lg">
      {/* Track */}
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#111" strokeWidth="14" />

      {segments.map((seg, i) => {
        const len = (seg.value / total) * circ;
        const dash = `${len} ${circ}`;
        const el = (
          <circle
            key={i}
            cx={cx} cy={cy} r={r}
            fill="none"
            stroke={seg.color}
            strokeWidth="14"
            strokeDasharray={dash}
            strokeDashoffset={offset}
            strokeLinecap="butt"
            style={{ filter: `drop-shadow(0 0 4px ${seg.color}88)` }}
          />
        );
        offset -= len;
        return el;
      })}

      {/* Center */}
      <text x={cx} y={cy - 5} textAnchor="middle" fill="#e0e0e0"
        fontSize="13" fontFamily="monospace" fontWeight="bold">
        {(total / 1000).toFixed(1)}k
      </text>
      <text x={cx} y={cy + 7} textAnchor="middle" fill="#555"
        fontSize="5.5" fontFamily="monospace">
        transacciones
      </text>
    </svg>
  );
}

// ── Stat Card ─────────────────────────────────────────────────────────────────

function StatCard({ label, value, color = '#e0e0e0', sub }: {
  label: string; value: string | number; color?: string; sub?: string;
}) {
  return (
    <div className="border border-[#222] rounded px-3 py-2 bg-[#0d0d0d] flex flex-col gap-0.5">
      <span className="text-[10px] text-[#555] font-mono uppercase tracking-widest">{label}</span>
      <span className="text-xl font-bold font-mono" style={{ color }}>{value}</span>
      {sub && <span className="text-[9px] text-[#444] font-mono">{sub}</span>}
    </div>
  );
}

// ── Legend Item ───────────────────────────────────────────────────────────────

function LegendItem({ color, label, value, total }: {
  color: string; label: string; value: number; total: number;
}) {
  const pct = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
  const barW = total > 0 ? Math.round((value / total) * 80) : 0;

  return (
    <div className="flex items-center gap-2 text-[10px] font-mono">
      <span className="w-2 h-2 rounded-sm shrink-0" style={{ background: color, boxShadow: `0 0 4px ${color}` }} />
      <span className="text-[#888] w-16">{label}</span>
      <div className="flex-1 h-1 bg-[#111] rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${barW}%`, background: color }} />
      </div>
      <span className="text-[#666] w-10 text-right">{pct}%</span>
      <span className="text-[#444] w-16 text-right">{value.toLocaleString()}</span>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function RunSummary({ stats, runId }: { stats: RunStats; runId: string }) {
  const { total, cobros, pagos, internos, sin_clasificar, alerts, banks } = stats;

  return (
    <div className="border border-[#1a1a2e] rounded bg-[#080810] p-3 shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 border-b border-[#1a1a2e] pb-2">
        <span className="text-[#00ff41] text-[10px] font-mono font-bold tracking-widest glow-green">
          ■ RUN SUMMARY
        </span>
        <span className="text-[#333] text-[9px] font-mono">{runId.slice(0, 8)}</span>
      </div>

      <div className="flex gap-4 items-start">
        {/* Donut Chart */}
        <div className="shrink-0">
          <DonutChart
            cobros={cobros}
            pagos={pagos}
            internos={internos}
            sinClasificar={sin_clasificar}
          />
        </div>

        {/* Right: stats + legend */}
        <div className="flex-1 flex flex-col gap-2 min-w-0">
          {/* Stat cards row */}
          <div className="grid grid-cols-3 gap-1.5">
            <StatCard label="Transacciones" value={total.toLocaleString()} color="#00d4ff" />
            <StatCard label="Alertas" value={alerts} color={alerts > 0 ? '#ff4444' : '#00ff41'}
              sub={alerts > 0 ? 'errores humanos' : 'sin errores'} />
            <StatCard label="Bancos" value={banks} color="#ffb000" sub="cuentas procesadas" />
          </div>

          {/* Legend */}
          <div className="flex flex-col gap-1 mt-1">
            <LegendItem color="#00ff41" label="COBROS"   value={cobros}        total={total} />
            <LegendItem color="#ff4444" label="PAGOS"    value={pagos}         total={total} />
            {internos > 0 && (
              <LegendItem color="#444466" label="INTERNO" value={internos}     total={total} />
            )}
            {sin_clasificar > 0 && (
              <LegendItem color="#ffb000" label="SIN CAT" value={sin_clasificar} total={total} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
