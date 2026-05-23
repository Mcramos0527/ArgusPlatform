'use client';

import { useState, useCallback, useRef } from 'react';
import type { LogLine, StepState, SSEEvent } from '@/lib/types';
import {
  streamPaso1,
  streamPaso2,
  streamPaso3,
  downloadFile,
} from '@/lib/api';
import TerminalLog from '@/components/TerminalLog';
import StepPanel from '@/components/StepPanel';

let lineCounter = 0;

function makeId(): string {
  return `line-${Date.now()}-${lineCounter++}`;
}

function detectType(msg: string): LogLine['type'] {
  if (msg.includes('✓') || msg.includes('COMPLETADO') || msg.includes('completados'))
    return 'success';
  if (
    msg.includes('⚠') ||
    msg.includes('ERROR HUMANO') ||
    msg.includes('FALTA') ||
    msg.includes('alerta') ||
    msg.includes('⚠️')
  )
    return 'warning';
  if (msg.includes('✗') || msg.startsWith('Error') || msg.startsWith('error'))
    return 'error';
  if (msg.startsWith('═') || msg.startsWith('─') || msg.startsWith('━'))
    return 'separator';
  return 'info';
}

function makeLogLine(msg: string, ts?: string): LogLine {
  return {
    id: makeId(),
    ts: ts ?? new Date().toLocaleTimeString('es-AR', { hour12: false }),
    msg,
    type: detectType(msg),
  };
}

function makeSeparator(): LogLine {
  return { id: makeId(), ts: '', msg: '', type: 'separator' };
}

const INITIAL_IDLE: StepState = { status: 'idle', progress: 0 };
const INITIAL_LOCKED: StepState = { status: 'locked', progress: 0 };

const BOOT_LINES: LogLine[] = [
  makeLogLine('root@argus:~/run$ ./argus --interactive', '00:00:00'),
  makeLogLine('ARGUS v3.0.0 — Sistema de Reconciliación Bancaria', '00:00:00'),
  makeLogLine('Delfabro Group — pipeline listo', '00:00:00'),
  makeSeparator(),
  makeLogLine('Seleccioná un archivo para comenzar el Paso 1', '00:00:00'),
];

export default function RunPage() {
  const [logLines, setLogLines] = useState<LogLine[]>(BOOT_LINES);

  const [step1, setStep1] = useState<StepState>({ ...INITIAL_IDLE });
  const [step2, setStep2] = useState<StepState>({ ...INITIAL_LOCKED });
  const [step3, setStep3] = useState<StepState>({ ...INITIAL_LOCKED });

  const [runId, setRunId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const cancelRef = useRef<(() => void) | null>(null);

  const addLog = useCallback((msg: string, ts?: string) => {
    setLogLines((prev) => [...prev, makeLogLine(msg, ts)]);
  }, []);

  const addSep = useCallback(() => {
    setLogLines((prev) => [...prev, makeSeparator()]);
  }, []);

  // ── Step 1 ──────────────────────────────────────────────────────────────────

  function executeStep1() {
    if (!step1.file) return;
    setStep1((s) => ({ ...s, status: 'running', progress: 5 }));
    setIsRunning(true);
    addLog('⚡ Iniciando ARGUS v3.0.0 — Paso 1: Movimientos Bancarios');
    addLog(`📂 Cargando ${step1.file.name}...`);

    cancelRef.current = streamPaso1(step1.file, (event: SSEEvent) => {
      if (event.type === 'log') {
        addLog(event.msg, event.ts);
      } else if (event.type === 'progress') {
        setStep1((s) => ({ ...s, progress: event.pct }));
      } else if (event.type === 'done') {
        const rid = event.run_id;
        setRunId(rid);
        setStep1((s) => ({ ...s, status: 'done', progress: 100 }));
        setStep2((s) => ({ ...s, status: 'idle' }));
        setIsRunning(false);
        addSep();
        addLog('✓ PASO 1 COMPLETADO');
        addLog(`  run_id: ${rid}`);
        addLog('  Subí COBROS.xlsx y PAGOS.xlsx para continuar');
        addSep();
      } else if (event.type === 'error') {
        setStep1((s) => ({ ...s, status: 'error', errorMsg: event.msg }));
        setIsRunning(false);
        addSep();
        addLog(`✗ ERROR en Paso 1: ${event.msg}`);
        addSep();
      }
    });
  }

  // ── Step 2 ──────────────────────────────────────────────────────────────────

  function executeStep2() {
    if (!runId || !step2.file || !step2.file2) return;
    setStep2((s) => ({ ...s, status: 'running', progress: 5 }));
    setIsRunning(true);
    addLog('⚡ Iniciando Paso 2 — Conciliación ERP Coliseo');
    addLog(`📂 Cargando ${step2.file.name} + ${step2.file2.name}...`);

    cancelRef.current = streamPaso2(
      runId,
      step2.file,
      step2.file2,
      (event: SSEEvent) => {
        if (event.type === 'log') {
          addLog(event.msg, event.ts);
        } else if (event.type === 'progress') {
          setStep2((s) => ({ ...s, progress: event.pct }));
        } else if (event.type === 'done') {
          setStep2((s) => ({ ...s, status: 'done', progress: 100 }));
          setStep3((s) => ({ ...s, status: 'idle' }));
          setIsRunning(false);
          addSep();
          addLog('✓ PASO 2 COMPLETADO — Conciliación lista');
          addLog('  Subí Caja.xlsx para generar el export final');
          addSep();
        } else if (event.type === 'error') {
          setStep2((s) => ({ ...s, status: 'error', errorMsg: event.msg }));
          setIsRunning(false);
          addSep();
          addLog(`✗ ERROR en Paso 2: ${event.msg}`);
          addSep();
        }
      }
    );
  }

  // ── Step 3 ──────────────────────────────────────────────────────────────────

  function executeStep3() {
    if (!runId || !step3.file) return;
    setStep3((s) => ({ ...s, status: 'running', progress: 5 }));
    setIsRunning(true);
    addLog('⚡ Iniciando Paso 3 — Export Caja Fábrica Digital');
    addLog(`📂 Cargando ${step3.file.name}...`);

    cancelRef.current = streamPaso3(runId, step3.file, (event: SSEEvent) => {
      if (event.type === 'log') {
        addLog(event.msg, event.ts);
      } else if (event.type === 'progress') {
        setStep3((s) => ({ ...s, progress: event.pct }));
      } else if (event.type === 'done') {
        setStep3((s) => ({ ...s, status: 'done', progress: 100 }));
        setIsRunning(false);
        addSep();
        addLog('✓ TODOS LOS PASOS COMPLETADOS');
        addLog(`  run_id: ${event.run_id}`);
        addLog('  ↓ Descargá los archivos de salida desde los pasos');
        addSep();
        addLog('🎉 Pipeline finalizado exitosamente');
      } else if (event.type === 'error') {
        setStep3((s) => ({ ...s, status: 'error', errorMsg: event.msg }));
        setIsRunning(false);
        addSep();
        addLog(`✗ ERROR en Paso 3: ${event.msg}`);
        addSep();
      }
    });
  }

  // ── Reset ────────────────────────────────────────────────────────────────────

  function handleReset() {
    cancelRef.current?.();
    cancelRef.current = null;
    setStep1({ ...INITIAL_IDLE });
    setStep2({ ...INITIAL_LOCKED });
    setStep3({ ...INITIAL_LOCKED });
    setRunId(null);
    setIsRunning(false);
    setLogLines([
      makeLogLine('root@argus:~/run$ ./argus --reset'),
      makeLogLine('Pipeline reset — listo para nuevo run'),
      makeSeparator(),
    ]);
  }

  return (
    <div className="flex-1 flex flex-col md:flex-row min-h-0 overflow-hidden">
      {/* ── Left: Step controls ──────────────────────────────────────────── */}
      <aside className="w-full md:w-72 lg:w-80 border-b md:border-b-0 md:border-r border-terminal-border bg-terminal-bg-secondary overflow-y-auto p-3 shrink-0">
        {/* Panel header */}
        <div className="text-terminal-gray mb-3 border-b border-terminal-border pb-2 flex items-center justify-between">
          <span className="text-terminal-green font-bold text-xs">PIPELINE</span>
          <span className="text-terminal-gray text-xs">
            {runId ? `run_${runId.slice(0, 8)}` : 'no active run'}
          </span>
        </div>

        <StepPanel
          step={1}
          title="MOVIMIENTOS"
          description="Normalizar movimientos bancarios de todas las cuentas"
          status={step1.status}
          accent="cyan"
          progress={step1.progress}
          fileLabel="Seleccionar Movimientos.xlsx"
          file={step1.file}
          onFileChange={(f) => setStep1((s) => ({ ...s, file: f }))}
          onExecute={executeStep1}
          onDownload={runId ? () => downloadFile(runId, 1) : undefined}
          errorMsg={step1.errorMsg}
        />

        <StepPanel
          step={2}
          title="CONCILIACIÓN"
          description="Conciliar contra ERP Coliseo (COBROS + PAGOS)"
          status={step2.status}
          accent="green"
          progress={step2.progress}
          fileLabel="Seleccionar COBROS.xlsx"
          file={step2.file}
          file2Label="Seleccionar PAGOS.xlsx"
          file2={step2.file2}
          onFileChange={(f) => setStep2((s) => ({ ...s, file: f }))}
          onFile2Change={(f) => setStep2((s) => ({ ...s, file2: f }))}
          onExecute={executeStep2}
          onDownload={runId ? () => downloadFile(runId, 2) : undefined}
          errorMsg={step2.errorMsg}
          runId={runId ?? undefined}
        />

        <StepPanel
          step={3}
          title="CAJA"
          description="Generar export Caja Fábrica Digital"
          status={step3.status}
          accent="purple"
          progress={step3.progress}
          fileLabel="Seleccionar Caja.xlsx"
          file={step3.file}
          onFileChange={(f) => setStep3((s) => ({ ...s, file: f }))}
          onExecute={executeStep3}
          onDownload={runId ? () => downloadFile(runId, 3) : undefined}
          errorMsg={step3.errorMsg}
          runId={runId ?? undefined}
        />

        {/* Controls */}
        <div className="border-t border-terminal-border pt-3 mt-1 space-y-2">
          <button
            onClick={handleReset}
            disabled={isRunning}
            className="w-full px-3 py-2 border border-terminal-red text-terminal-red
              rounded text-xs font-mono hover:bg-terminal-red hover:text-terminal-bg
              transition-all disabled:opacity-40 disabled:cursor-not-allowed active:scale-95"
          >
            ↺ RESET PIPELINE
          </button>
        </div>

        {/* Active run ID display */}
        {runId && (
          <div className="mt-3 p-2 border border-terminal-border-bright rounded bg-terminal-bg text-xs">
            <div className="text-terminal-gray-dim text-xs">run_id:</div>
            <div className="text-terminal-cyan break-all text-xs mt-0.5">{runId}</div>
          </div>
        )}
      </aside>

      {/* ── Right: Terminal log ──────────────────────────────────────────── */}
      <section className="flex-1 p-3 min-h-0 min-w-0 flex flex-col">
        <TerminalLog
          lines={logLines}
          isRunning={isRunning}
          title={
            runId
              ? `root@argus:~/run$ ./argus --run=${runId.slice(0, 8)}`
              : 'root@argus:~/run$ ./argus --interactive'
          }
        />
      </section>
    </div>
  );
}
