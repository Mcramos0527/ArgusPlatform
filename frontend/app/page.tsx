'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import type { Run } from '@/lib/types';
import { getRuns } from '@/lib/api';
import RunCard from '@/components/RunCard';

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export default function DashboardPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchRuns = useCallback(async () => {
    try {
      const data = await getRuns();
      setRuns(data);
      setLastRefresh(new Date());
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchRuns();
    const interval = setInterval(() => void fetchRuns(), 15000);
    return () => clearInterval(interval);
  }, [fetchRuns]);

  function handleDeleted(id: string) {
    setRuns((prev) => prev.filter((r) => r.id !== id));
  }

  const totalTx = runs.reduce((s, r) => s + r.transactions_total, 0);
  const lastRunAgo =
    runs[0]
      ? Math.round(
          (Date.now() - new Date(runs[0].created_at).getTime()) / 60000
        )
      : null;

  return (
    <div className="p-4 font-mono text-xs max-w-6xl mx-auto w-full">
      {/* Shell prompt header */}
      <div className="border border-terminal-border rounded mb-4 bg-terminal-bg-card">
        {/* Command line */}
        <div className="border-b border-terminal-border px-3 py-2 text-terminal-green">
          root@argus:~$ ls -la runs/
        </div>

        {/* Stats bar */}
        <div className="flex items-center gap-3 px-3 py-2 border-b border-terminal-border text-terminal-gray flex-wrap">
          <span className="text-terminal-cyan font-bold">RUNS HISTORY</span>
          <span className="text-terminal-gray-dim">──</span>
          <span>
            <span className="text-terminal-white">{runs.length}</span> runs
          </span>
          <span className="text-terminal-gray-dim">│</span>
          <span>
            total:{' '}
            <span className="text-terminal-white tabular-nums">
              {totalTx.toLocaleString()}
            </span>{' '}
            tx
          </span>
          {lastRunAgo !== null && (
            <>
              <span className="text-terminal-gray-dim">│</span>
              <span>
                last:{' '}
                <span className="text-terminal-white">
                  {lastRunAgo < 60
                    ? `${lastRunAgo}m ago`
                    : `${Math.round(lastRunAgo / 60)}h ago`}
                </span>
              </span>
            </>
          )}
          <span className="ml-auto flex items-center gap-2">
            <button
              onClick={() => void fetchRuns()}
              className="text-terminal-gray hover:text-terminal-white border border-terminal-border
                rounded px-2 py-0.5 transition-colors hover:border-terminal-border-bright"
            >
              ↻ refresh
            </button>
            <span className="text-terminal-gray-dim text-xs tabular-nums">
              {lastRefresh.toLocaleTimeString('es-AR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              })}
            </span>
          </span>
        </div>

        {/* New run CTA */}
        <div className="px-3 py-2 border-b border-terminal-border">
          <Link
            href="/run"
            className="inline-flex items-center gap-2 px-4 py-2 border border-terminal-green
              text-terminal-green rounded text-sm font-bold hover:bg-terminal-green hover:text-terminal-bg
              transition-all glow-green active:scale-95"
          >
            ▶ NUEVO RUN →
          </Link>
          <span className="ml-3 text-terminal-gray text-xs">
            Iniciar pipeline de reconciliación bancaria
          </span>
        </div>

        {/* Run list */}
        <div className="p-3">
          {loading && (
            <div className="text-terminal-cyan animate-pulse py-4 text-center">
              root@argus:~$ Cargando runs...
              <span className="cursor ml-1" />
            </div>
          )}

          {error && (
            <div className="text-terminal-red border border-terminal-red/30 rounded p-3 mb-3">
              <div className="font-bold mb-1">✗ Error fetching runs:</div>
              <div className="text-terminal-red/80">{error}</div>
              <div className="mt-2 text-terminal-gray">
                Verificá que el backend esté corriendo en{' '}
                <span className="text-terminal-white">{BACKEND_URL}</span>
              </div>
            </div>
          )}

          {!loading && !error && runs.length === 0 && (
            <div className="text-terminal-gray py-6 text-center">
              <div className="text-terminal-gray-dim mb-1">total 0</div>
              <div>No hay runs. Iniciá tu primer run →</div>
            </div>
          )}

          {runs.map((run) => (
            <RunCard key={run.id} run={run} onDeleted={handleDeleted} />
          ))}
        </div>
      </div>

      {/* System info footer */}
      <div className="text-terminal-gray-dim text-xs border border-terminal-border rounded px-3 py-2 flex gap-3 flex-wrap">
        <span>
          <span className="text-terminal-green">ARGUS</span> v3.0.0
        </span>
        <span className="text-terminal-border">│</span>
        <span>
          backend:{' '}
          <span className="text-terminal-white">{BACKEND_URL}</span>
        </span>
        <span className="text-terminal-border">│</span>
        <span>Delfabro Group © 2026</span>
      </div>
    </div>
  );
}
