'use client';

import { useState } from 'react';
import type { Run, Transaction, OutputFile } from '@/lib/types';
import { getTransactions, getOutputFiles, downloadFile, deleteRun } from '@/lib/api';

interface RunCardProps {
  run: Run;
  onDeleted: (id: string) => void;
}

function statusBadge(status: Run['status']): { label: string; color: string } {
  switch (status) {
    case 'complete':
      return { label: 'DONE', color: 'text-terminal-green border-terminal-green' };
    case 'step2_complete':
      return { label: 'STEP2', color: 'text-terminal-cyan border-terminal-cyan' };
    case 'step1_complete':
      return { label: 'STEP1', color: 'text-terminal-amber border-terminal-amber' };
    case 'running':
    case 'running_step2':
    case 'running_step3':
      return {
        label: 'RUNNING',
        color: 'text-terminal-cyan border-terminal-cyan animate-pulse',
      };
    case 'error':
      return { label: 'ERROR', color: 'text-terminal-red border-terminal-red' };
    default: {
      const s = status as string;
      return { label: s.toUpperCase(), color: 'text-terminal-gray border-terminal-gray' };
    }
  }
}

function progressBlocks(steps: number, max = 3): string {
  const filled = '█'.repeat(Math.min(steps, max));
  const empty = '─'.repeat(Math.max(0, max - steps));
  return `[${filled}${empty}]`;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return (
    d.toLocaleDateString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }) +
    ' ' +
    d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
  );
}

export default function RunCard({ run, onDeleted }: RunCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [txLoading, setTxLoading] = useState(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [txTotal, setTxTotal] = useState(0);
  const [outputFiles, setOutputFiles] = useState<OutputFile[]>([]);
  const [deleting, setDeleting] = useState(false);

  const badge = statusBadge(run.status);
  const shortId = run.id.slice(0, 8);

  async function handleExpand() {
    if (!expanded) {
      setTxLoading(true);
      try {
        const [txPage, files] = await Promise.all([
          getTransactions(run.id, 1, 50),
          getOutputFiles(run.id),
        ]);
        setTransactions(txPage.data);
        setTxTotal(txPage.total);
        setOutputFiles(files);
      } catch {
        // non-fatal — show empty state
      } finally {
        setTxLoading(false);
      }
    }
    setExpanded((v) => !v);
  }

  async function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm(`Eliminar run ${shortId}? Esta acción no se puede deshacer.`)) return;
    setDeleting(true);
    try {
      await deleteRun(run.id);
      onDeleted(run.id);
    } catch {
      setDeleting(false);
    }
  }

  return (
    <div className="border border-terminal-border hover:border-terminal-border-bright rounded mb-2 font-mono text-xs transition-colors bg-terminal-bg-card">
      {/* ls -la style header row */}
      <div
        className="flex items-center gap-2 px-3 py-2 cursor-pointer select-none flex-wrap"
        onClick={handleExpand}
      >
        <span className="text-terminal-gray shrink-0">drwxr-xr-x</span>
        <span className="text-terminal-gray shrink-0 hidden sm:block">
          {formatDate(run.created_at)}
        </span>
        <span className="text-terminal-cyan font-bold shrink-0">run_{shortId}</span>
        <span className="text-terminal-green shrink-0">{progressBlocks(run.steps_completed)}</span>
        <span
          className={`border rounded px-1 text-xs shrink-0 ${badge.color}`}
        >
          {badge.label}
        </span>
        <span className="text-terminal-gray ml-auto shrink-0 tabular-nums">
          {run.steps_completed}/3
        </span>
        <span
          className={`text-terminal-gray text-xs transition-transform duration-200 ${
            expanded ? 'rotate-90' : ''
          }`}
        >
          ▶
        </span>
      </div>

      {/* Subtitle row */}
      <div className="flex items-center gap-3 px-3 pb-2 text-terminal-gray text-xs border-t border-terminal-border/30 flex-wrap">
        <span>
          └─{' '}
          <span className="text-terminal-white tabular-nums">
            {run.transactions_total.toLocaleString()}
          </span>{' '}
          tx
        </span>
        <span>
          <span className="text-terminal-white">{run.sheets_processed}</span> hojas
        </span>
        <span
          className={run.steps_completed >= 1 ? 'text-terminal-green' : 'text-terminal-gray'}
        >
          MOV {run.steps_completed >= 1 ? '✓' : '─'}
        </span>
        <span
          className={run.steps_completed >= 2 ? 'text-terminal-green' : 'text-terminal-gray'}
        >
          COBROS {run.steps_completed >= 2 ? '✓' : '─'}
        </span>
        <span
          className={run.steps_completed >= 3 ? 'text-terminal-green' : 'text-terminal-gray'}
        >
          CAJA {run.steps_completed >= 3 ? '✓' : '─'}
        </span>

        {/* Download buttons per step */}
        <div className="ml-auto flex gap-1.5 flex-wrap">
          {[1, 2, 3].map(
            (s) =>
              run.steps_completed >= s && (
                <button
                  key={s}
                  onClick={(e) => {
                    e.stopPropagation();
                    downloadFile(run.id, s);
                  }}
                  className="text-terminal-green border border-terminal-green rounded px-1.5 py-0.5
                    hover:bg-terminal-green hover:text-terminal-bg transition-colors text-xs"
                >
                  ↓ S{s}
                </button>
              )
          )}
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="text-terminal-red border border-terminal-red rounded px-1.5 py-0.5
              hover:bg-terminal-red hover:text-terminal-bg transition-colors text-xs disabled:opacity-40"
          >
            {deleting ? '...' : '✗'}
          </button>
        </div>
      </div>

      {/* Expanded: transactions */}
      {expanded && (
        <div className="border-t border-terminal-border px-3 py-2">
          {txLoading ? (
            <div className="text-terminal-cyan animate-pulse py-2">
              Loading transactions...
            </div>
          ) : transactions.length === 0 ? (
            <div className="text-terminal-gray py-2">No transactions found.</div>
          ) : (
            <>
              {/* Output files quick links */}
              {outputFiles.length > 0 && (
                <div className="mb-2 flex gap-2 flex-wrap">
                  {outputFiles.map((f) => (
                    <button
                      key={f.id}
                      onClick={() => downloadFile(run.id, f.step)}
                      className="text-terminal-green border border-terminal-green rounded px-2 py-0.5
                        hover:bg-terminal-green hover:text-terminal-bg transition-colors text-xs"
                    >
                      ↓ {f.filename}
                    </button>
                  ))}
                </div>
              )}

              {/* Tx count */}
              <div className="text-terminal-gray mb-1">
                Mostrando{' '}
                <span className="text-terminal-white">{transactions.length}</span> de{' '}
                <span className="text-terminal-white">{txTotal}</span> transacciones
              </div>

              {/* Transaction table */}
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse min-w-[600px]">
                  <thead>
                    <tr className="text-terminal-cyan border-b border-terminal-border">
                      <th className="text-left py-1 pr-3 font-normal">FECHA</th>
                      <th className="text-left py-1 pr-3 font-normal">BANCO</th>
                      <th className="text-left py-1 pr-3 font-normal">DESCRIPCION</th>
                      <th className="text-right py-1 pr-3 font-normal">MONTO</th>
                      <th className="text-left py-1 font-normal">CAT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx) => (
                      <tr
                        key={tx.id}
                        className="border-b border-terminal-border/30 hover:bg-terminal-border/20"
                      >
                        <td className="py-0.5 pr-3 text-terminal-gray tabular-nums">
                          {tx.fecha}
                        </td>
                        <td className="py-0.5 pr-3 text-terminal-amber">{tx.banco}</td>
                        <td className="py-0.5 pr-3 text-terminal-white truncate max-w-[200px]">
                          {tx.descripcion}
                        </td>
                        <td
                          className={`py-0.5 pr-3 text-right tabular-nums ${
                            tx.monto >= 0 ? 'text-terminal-green' : 'text-terminal-red'
                          }`}
                        >
                          {tx.monto.toLocaleString('es-AR', {
                            minimumFractionDigits: 2,
                          })}
                        </td>
                        <td className="py-0.5 text-terminal-gray">{tx.categoria}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
