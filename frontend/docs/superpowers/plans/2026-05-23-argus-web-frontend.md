# ARGUS Web Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete Next.js 14 frontend for ARGUS Web with a hacker/terminal aesthetic — monospace fonts, terminal colors, real-time SSE log streaming, and pipeline step management.

**Architecture:** App Router (Next.js 14), three pages (dashboard, new run, run detail), shared terminal components (TerminalLog, StepPanel, RunCard), and a typed API client in `lib/api.ts`. All SSE streaming uses `fetch` + `ReadableStream` directly (no EventSource, to allow POST requests).

**Tech Stack:** Next.js 14.2.0, TypeScript 5, Tailwind CSS 3.4, JetBrains Mono font, no external UI libraries.

---

### Task 1: Project scaffold — package.json, configs, globals

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.js`
- Create: `frontend/.env.example`
- Create: `frontend/app/globals.css`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "argus-web",
  "version": "3.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.2.0",
    "react": "^18",
    "react-dom": "^18"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "tailwindcss": "^3.4.0",
    "postcss": "^8",
    "autoprefixer": "^10"
  }
}
```

Write to `frontend/package.json`.

- [ ] **Step 2: Create tailwind.config.ts**

```ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'Fira Code', 'Consolas', 'monospace'],
      },
      colors: {
        terminal: {
          bg: '#0a0a0a',
          'bg-secondary': '#111111',
          'bg-card': '#0d0d0d',
          border: '#1a1a1a',
          'border-bright': '#2a2a2a',
          green: '#00ff41',
          'green-dim': '#00aa2b',
          cyan: '#00d4ff',
          'cyan-dim': '#0088aa',
          amber: '#ffb000',
          'amber-dim': '#aa7500',
          red: '#ff3333',
          purple: '#b44fff',
          'purple-dim': '#7733aa',
          gray: '#555555',
          'gray-dim': '#333333',
          white: '#e0e0e0',
        },
      },
      animation: {
        'blink': 'blink 1s infinite',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}

export default config
```

Write to `frontend/tailwind.config.ts`.

- [ ] **Step 3: Create postcss.config.js**

```js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

Write to `frontend/postcss.config.js`.

- [ ] **Step 4: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

Write to `frontend/tsconfig.json`.

- [ ] **Step 5: Create next.config.js**

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL,
  },
}

module.exports = nextConfig
```

Write to `frontend/next.config.js`.

- [ ] **Step 6: Create .env.example**

```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Write to `frontend/.env.example`.

- [ ] **Step 7: Create globals.css**

```css
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

* {
  box-sizing: border-box;
}

body {
  background: #0a0a0a;
  color: #e0e0e0;
  font-family: 'JetBrains Mono', monospace;
  overflow-x: hidden;
}

/* terminal cursor blink */
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.cursor {
  display: inline-block;
  width: 8px;
  height: 14px;
  background: #00ff41;
  animation: blink 1s infinite;
  vertical-align: middle;
  margin-left: 2px;
}

/* scanline overlay */
body::after {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.03) 2px,
    rgba(0, 0, 0, 0.03) 4px
  );
  pointer-events: none;
  z-index: 9999;
}

/* custom scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: #00ff41; border-radius: 2px; }

/* terminal glow effects */
.glow-green {
  text-shadow: 0 0 8px #00ff41, 0 0 16px #00ff4155;
}
.glow-cyan {
  text-shadow: 0 0 8px #00d4ff, 0 0 16px #00d4ff55;
}
.glow-amber {
  text-shadow: 0 0 8px #ffb000, 0 0 16px #ffb00055;
}

/* file input hide default */
input[type='file'] {
  display: none;
}

/* progress bar animation */
@keyframes scanbar {
  0% { background-position: -200px 0; }
  100% { background-position: 200px 0; }
}

.progress-animated {
  background: linear-gradient(
    90deg,
    #00d4ff 0%,
    #00ff41 50%,
    #00d4ff 100%
  );
  background-size: 200px 100%;
  animation: scanbar 1.5s linear infinite;
}
```

Write to `frontend/app/globals.css`.

---

### Task 2: Type definitions and API client

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/api.ts`

- [ ] **Step 1: Create lib/types.ts**

```ts
// frontend/lib/types.ts
// Shared TypeScript types for the ARGUS Web frontend.

export type RunStatus =
  | 'running'
  | 'running_step2'
  | 'running_step3'
  | 'step1_complete'
  | 'step2_complete'
  | 'complete'
  | 'error';

export interface Run {
  id: string;
  created_at: string;
  status: RunStatus;
  steps_completed: number;
  sheets_processed: number;
  transactions_total: number;
}

export interface Transaction {
  id: string;
  run_id: string;
  fecha: string;
  descripcion: string;
  monto: number;
  banco: string;
  categoria: string;
  tipo: string;
  hoja: string;
}

export interface ReconciliationLine {
  id: string;
  run_id: string;
  estado: string;
  tipo: string;
  monto: number;
  nombre: string;
  banco: string;
  fecha?: string;
  referencia?: string;
}

export interface OutputFile {
  id: string;
  run_id: string;
  step: number;
  filename: string;
  storage_path: string;
  created_at: string;
}

export interface TransactionPage {
  data: Transaction[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// SSE event types
export type SSEEventType = 'log' | 'progress' | 'done' | 'error';

export interface SSELogEvent {
  type: 'log';
  msg: string;
  ts: string;
}

export interface SSEProgressEvent {
  type: 'progress';
  pct: number;
}

export interface SSEDoneEvent {
  type: 'done';
  run_id: string;
  file_url: string;
}

export interface SSEErrorEvent {
  type: 'error';
  msg: string;
}

export type SSEEvent = SSELogEvent | SSEProgressEvent | SSEDoneEvent | SSEErrorEvent;

// Terminal log line for UI
export type LogLineType = 'info' | 'success' | 'warning' | 'error' | 'separator';

export interface LogLine {
  id: string;
  ts: string;
  msg: string;
  type: LogLineType;
}

// Step status for pipeline UI
export type StepStatus = 'idle' | 'running' | 'done' | 'locked' | 'error';

export interface StepState {
  status: StepStatus;
  file?: File;
  file2?: File; // pagos for step 2
  progress: number;
  errorMsg?: string;
}
```

Write to `frontend/lib/types.ts`.

- [ ] **Step 2: Create lib/api.ts**

```ts
// frontend/lib/api.ts
// Typed API client for the ARGUS backend.
// SSE streaming uses fetch + ReadableStream (not EventSource) to support POST.

import type {
  Run,
  Transaction,
  ReconciliationLine,
  OutputFile,
  TransactionPage,
  SSEEvent,
} from './types';

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// ── REST helpers ──────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} → ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function getRuns(): Promise<Run[]> {
  const data = await apiFetch<{ runs: Run[]; count: number }>('/api/runs');
  return data.runs;
}

export async function getRun(id: string): Promise<Run> {
  return apiFetch<Run>(`/api/runs/${id}`);
}

export async function getTransactions(
  runId: string,
  page = 1,
  limit = 100
): Promise<TransactionPage> {
  return apiFetch<TransactionPage>(
    `/api/runs/${runId}/transactions?page=${page}&limit=${limit}`
  );
}

export async function getReconciliation(
  runId: string
): Promise<ReconciliationLine[]> {
  const data = await apiFetch<{ run_id: string; lines: ReconciliationLine[]; count: number }>(
    `/api/runs/${runId}/reconciliation`
  );
  return data.lines;
}

export async function getOutputFiles(runId: string): Promise<OutputFile[]> {
  const data = await apiFetch<{ run_id: string; files: OutputFile[] }>(
    `/api/runs/${runId}/files`
  );
  return data.files;
}

export function downloadFile(runId: string, step: number): void {
  window.open(`${BACKEND_URL}/api/runs/${runId}/files/${step}`, '_blank');
}

export async function deleteRun(runId: string): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/api/runs/${runId}`, {
    method: 'DELETE',
  });
  if (!res.ok && res.status !== 204) {
    throw new Error(`Delete failed: ${res.status}`);
  }
}

// ── SSE streaming helpers ─────────────────────────────────────────────────────
// Returns a cancel function. Call it to abort the stream early.

function streamSSE(
  url: string,
  formData: FormData,
  onEvent: (e: SSEEvent) => void
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(url, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        const text = await res.text();
        onEvent({ type: 'error', msg: `HTTP ${res.status}: ${text}` });
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data:')) {
            const json = trimmed.slice(5).trim();
            if (json) {
              try {
                const event = JSON.parse(json) as SSEEvent;
                onEvent(event);
              } catch {
                // malformed JSON — ignore
              }
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        onEvent({ type: 'error', msg: String(err) });
      }
    }
  })();

  return () => controller.abort();
}

export function streamPaso1(
  file: File,
  onEvent: (e: SSEEvent) => void
): () => void {
  const fd = new FormData();
  fd.append('movimientos', file);
  return streamSSE(`${BACKEND_URL}/api/process/paso1`, fd, onEvent);
}

export function streamPaso2(
  runId: string,
  cobros: File,
  pagos: File,
  onEvent: (e: SSEEvent) => void
): () => void {
  const fd = new FormData();
  fd.append('cobros', cobros);
  fd.append('pagos', pagos);
  return streamSSE(`${BACKEND_URL}/api/process/paso2/${runId}`, fd, onEvent);
}

export function streamPaso3(
  runId: string,
  caja: File,
  onEvent: (e: SSEEvent) => void
): () => void {
  const fd = new FormData();
  fd.append('caja', caja);
  return streamSSE(`${BACKEND_URL}/api/process/paso3/${runId}`, fd, onEvent);
}
```

Write to `frontend/lib/api.ts`.

---

### Task 3: Shared utility hooks

**Files:**
- Create: `frontend/lib/useUptime.ts`

- [ ] **Step 1: Create useUptime hook**

```ts
// frontend/lib/useUptime.ts
'use client';

import { useState, useEffect, useRef } from 'react';

export function useUptime(): string {
  const startRef = useRef<number>(Date.now());
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setElapsed(Date.now() - startRef.current);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  const totalSeconds = Math.floor(elapsed / 1000);
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;

  return [h, m, s].map((n) => String(n).padStart(2, '0')).join(':');
}
```

Write to `frontend/lib/useUptime.ts`.

---

### Task 4: TerminalLog component

**Files:**
- Create: `frontend/components/TerminalLog.tsx`

- [ ] **Step 1: Create TerminalLog component**

```tsx
// frontend/components/TerminalLog.tsx
'use client';

import { useEffect, useRef } from 'react';
import type { LogLine } from '@/lib/types';

interface TerminalLogProps {
  lines: LogLine[];
  isRunning: boolean;
  title?: string;
}

function lineColor(type: LogLine['type']): string {
  switch (type) {
    case 'success':
      return 'text-terminal-green';
    case 'warning':
      return 'text-terminal-amber';
    case 'error':
      return 'text-terminal-red';
    case 'separator':
      return 'text-terminal-gray';
    default:
      return 'text-terminal-white';
  }
}

export default function TerminalLog({
  lines,
  isRunning,
  title = 'root@argus:~/run$',
}: TerminalLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines]);

  return (
    <div className="flex flex-col h-full bg-terminal-bg border border-terminal-border rounded">
      {/* Terminal header bar */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-terminal-border bg-terminal-bg-secondary">
        <div className="flex gap-1.5">
          <span className="w-3 h-3 rounded-full bg-terminal-red opacity-80" />
          <span className="w-3 h-3 rounded-full bg-terminal-amber opacity-80" />
          <span className="w-3 h-3 rounded-full bg-terminal-green opacity-80" />
        </div>
        <span className="ml-2 text-xs text-terminal-gray font-mono">{title}</span>
        {isRunning && (
          <span className="ml-auto text-xs text-terminal-cyan animate-pulse">
            ● RUNNING
          </span>
        )}
      </div>

      {/* Log output area */}
      <div className="flex-1 overflow-y-auto p-3 font-mono text-xs leading-relaxed min-h-0">
        {lines.length === 0 && (
          <div className="text-terminal-gray italic">
            Awaiting pipeline start...
          </div>
        )}

        {lines.map((line) => (
          <div key={line.id} className={`flex gap-2 ${lineColor(line.type)}`}>
            {line.type === 'separator' ? (
              <span className="text-terminal-gray-dim w-full">
                {line.msg || '────────────────────────────────────────────'}
              </span>
            ) : (
              <>
                <span className="text-terminal-gray shrink-0 select-none">
                  [{line.ts}]
                </span>
                <span className="break-all">{line.msg}</span>
              </>
            )}
          </div>
        ))}

        {/* Blinking cursor when running */}
        {isRunning && (
          <div className="flex items-center gap-1 mt-1">
            <span className="text-terminal-gray text-xs">&gt;</span>
            <span className="cursor" />
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
```

Write to `frontend/components/TerminalLog.tsx`.

---

### Task 5: ProgressBar component

**Files:**
- Create: `frontend/components/ProgressBar.tsx`

- [ ] **Step 1: Create ProgressBar component**

```tsx
// frontend/components/ProgressBar.tsx
'use client';

interface ProgressBarProps {
  pct: number;
  isRunning: boolean;
  color?: string;
}

export default function ProgressBar({
  pct,
  isRunning,
  color = 'terminal-cyan',
}: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, pct));
  const filled = Math.round(clamped / 5); // 20 blocks total
  const empty = 20 - filled;

  const blocks = '█'.repeat(filled) + '─'.repeat(empty);

  return (
    <div className="flex items-center gap-2 font-mono text-xs">
      <span className="text-terminal-gray">
        [<span className={isRunning ? 'progress-animated-text' : `text-${color}`}>{blocks}</span>]
      </span>
      <span className={`text-${color} tabular-nums`}>{clamped}%</span>
      {isRunning && <span className="text-terminal-cyan animate-pulse text-xs">●</span>}
    </div>
  );
}
```

Write to `frontend/components/ProgressBar.tsx`.

---

### Task 6: StepPanel component

**Files:**
- Create: `frontend/components/StepPanel.tsx`

- [ ] **Step 1: Create StepPanel component**

```tsx
// frontend/components/StepPanel.tsx
'use client';

import { useRef } from 'react';
import type { StepStatus } from '@/lib/types';
import ProgressBar from './ProgressBar';

interface StepPanelProps {
  step: number;
  title: string;
  description: string;
  status: StepStatus;
  accent: string;          // Tailwind color class suffix, e.g. 'cyan', 'green', 'purple'
  progress: number;
  // File inputs
  fileLabel: string;
  file?: File;
  file2Label?: string;     // optional second file (step 2 needs cobros + pagos)
  file2?: File;
  onFileChange: (file: File) => void;
  onFile2Change?: (file: File) => void;
  onExecute: () => void;
  onDownload?: () => void;
  errorMsg?: string;
  runId?: string;
}

const accentMap: Record<string, { text: string; border: string; bg: string }> = {
  cyan:   { text: 'text-terminal-cyan',   border: 'border-terminal-cyan',   bg: 'bg-terminal-cyan' },
  green:  { text: 'text-terminal-green',  border: 'border-terminal-green',  bg: 'bg-terminal-green' },
  purple: { text: 'text-terminal-purple', border: 'border-terminal-purple', bg: 'bg-terminal-purple' },
};

export default function StepPanel({
  step,
  title,
  description,
  status,
  accent,
  progress,
  fileLabel,
  file,
  file2Label,
  file2,
  onFileChange,
  onFile2Change,
  onExecute,
  onDownload,
  errorMsg,
}: StepPanelProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const file2Ref = useRef<HTMLInputElement>(null);
  const colors = accentMap[accent] ?? accentMap['cyan'];

  const isLocked = status === 'locked';
  const isRunning = status === 'running';
  const isDone = status === 'done';
  const isError = status === 'error';
  const isIdle = status === 'idle';

  const canExecute =
    isIdle &&
    !!file &&
    (file2Label === undefined || !!file2);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>, which: 'primary' | 'secondary') {
    const f = e.target.files?.[0];
    if (!f) return;
    if (which === 'primary') onFileChange(f);
    else onFile2Change?.(f);
  }

  return (
    <div
      className={`border rounded p-3 mb-3 bg-terminal-bg-card font-mono text-xs transition-all
        ${isLocked ? 'border-terminal-border opacity-50' : colors.border}
        ${isRunning ? 'shadow-lg' : ''}
      `}
    >
      {/* Step header */}
      <div className="flex items-center gap-2 mb-2">
        <span
          className={`font-bold text-sm ${
            isLocked ? 'text-terminal-gray' :
            isDone   ? 'text-terminal-green' :
            isError  ? 'text-terminal-red' :
            isRunning ? 'text-terminal-cyan animate-pulse' :
            colors.text
          }`}
        >
          {isDone   ? '✓' :
           isError  ? '✗' :
           isRunning ? '▶' :
           isLocked  ? '●' :
           '○'}
          {' '}[{step}] {title}
        </span>

        {isDone && (
          <span className="text-terminal-green text-xs ml-auto">COMPLETE</span>
        )}
        {isRunning && (
          <span className="text-terminal-cyan text-xs ml-auto animate-pulse">RUNNING</span>
        )}
        {isLocked && (
          <span className="text-terminal-gray text-xs ml-auto">LOCKED</span>
        )}
        {isError && (
          <span className="text-terminal-red text-xs ml-auto">ERROR</span>
        )}
      </div>

      <div className="text-terminal-gray text-xs mb-2">{description}</div>

      {/* Running state: show progress */}
      {isRunning && (
        <div className="mb-2">
          <ProgressBar pct={progress} isRunning color={`terminal-${accent}`} />
        </div>
      )}

      {/* Error message */}
      {isError && errorMsg && (
        <div className="text-terminal-red text-xs mb-2 border border-terminal-red/30 rounded p-2 bg-terminal-red/5">
          ✗ {errorMsg}
        </div>
      )}

      {/* File inputs — only show when idle */}
      {(isIdle || isError) && (
        <div className="space-y-2">
          {/* Primary file */}
          <div>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => handleFileChange(e, 'primary')}
            />
            <button
              onClick={() => fileRef.current?.click()}
              className={`w-full text-left px-3 py-1.5 border rounded text-xs font-mono
                border-terminal-border-bright text-terminal-gray hover:${colors.border} hover:${colors.text}
                transition-colors
              `}
            >
              📁 {file ? file.name : fileLabel}
            </button>
          </div>

          {/* Secondary file (step 2 only) */}
          {file2Label !== undefined && (
            <div>
              <input
                ref={file2Ref}
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => handleFileChange(e, 'secondary')}
              />
              <button
                onClick={() => file2Ref.current?.click()}
                className={`w-full text-left px-3 py-1.5 border rounded text-xs font-mono
                  border-terminal-border-bright text-terminal-gray hover:${colors.border} hover:${colors.text}
                  transition-colors
                `}
              >
                📁 {file2 ? file2.name : file2Label}
              </button>
            </div>
          )}

          {/* Execute button */}
          <button
            onClick={onExecute}
            disabled={!canExecute}
            className={`w-full px-3 py-1.5 border rounded text-xs font-mono font-bold
              transition-all
              ${canExecute
                ? `${colors.border} ${colors.text} hover:bg-terminal-border cursor-pointer`
                : 'border-terminal-gray-dim text-terminal-gray-dim cursor-not-allowed opacity-40'
              }
            `}
          >
            ▶ EJECUTAR
          </button>
        </div>
      )}

      {/* Done state: download button */}
      {isDone && onDownload && (
        <button
          onClick={onDownload}
          className="w-full mt-1 px-3 py-1.5 border border-terminal-green text-terminal-green
            rounded text-xs font-mono font-bold hover:bg-terminal-green hover:text-terminal-bg
            transition-all"
        >
          ↓ DESCARGAR XLSX
        </button>
      )}
    </div>
  );
}
```

Write to `frontend/components/StepPanel.tsx`.

---

### Task 7: RunCard component

**Files:**
- Create: `frontend/components/RunCard.tsx`

- [ ] **Step 1: Create RunCard component**

```tsx
// frontend/components/RunCard.tsx
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
    case 'complete':        return { label: 'DONE', color: 'text-terminal-green border-terminal-green' };
    case 'step2_complete':  return { label: 'STEP2', color: 'text-terminal-cyan border-terminal-cyan' };
    case 'step1_complete':  return { label: 'STEP1', color: 'text-terminal-amber border-terminal-amber' };
    case 'running':
    case 'running_step2':
    case 'running_step3':   return { label: 'RUNNING', color: 'text-terminal-cyan border-terminal-cyan animate-pulse' };
    case 'error':           return { label: 'ERROR', color: 'text-terminal-red border-terminal-red' };
    default:                return { label: status.toUpperCase(), color: 'text-terminal-gray border-terminal-gray' };
  }
}

function progressBlocks(steps: number, max = 3): string {
  const filled = '█'.repeat(steps);
  const empty = '─'.repeat(max - steps);
  return `[${filled}${empty}]`;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
    ' ' + d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
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
        // non-fatal
      } finally {
        setTxLoading(false);
      }
    }
    setExpanded((v) => !v);
  }

  async function handleDelete() {
    if (!confirm(`Delete run ${shortId}? This cannot be undone.`)) return;
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
      {/* ls -la style row */}
      <div
        className="flex items-center gap-2 px-3 py-2 cursor-pointer select-none"
        onClick={handleExpand}
      >
        <span className="text-terminal-gray shrink-0">drwxr-xr-x</span>
        <span className="text-terminal-gray shrink-0">{formatDate(run.created_at)}</span>
        <span className="text-terminal-cyan shrink-0 font-bold">run_{shortId}</span>
        <span className="text-terminal-green shrink-0">{progressBlocks(run.steps_completed)}</span>
        <span className={`border rounded px-1 text-xs shrink-0 ${badge.color}`}>
          {badge.label}
        </span>
        <span className="text-terminal-gray ml-auto shrink-0">
          {run.steps_completed}/3
        </span>
        <span className={`text-terminal-gray text-xs transition-transform ${expanded ? 'rotate-90' : ''}`}>
          ▶
        </span>
      </div>

      {/* Subtitle row */}
      <div className="flex items-center gap-4 px-3 pb-2 text-terminal-gray text-xs border-t border-terminal-border/30">
        <span>
          └─ <span className="text-terminal-white">{run.transactions_total.toLocaleString()}</span> tx
        </span>
        <span>
          <span className="text-terminal-white">{run.sheets_processed}</span> hojas
        </span>
        {run.steps_completed >= 1 && <span className="text-terminal-green">MOVIMIENTOS ✓</span>}
        {run.steps_completed >= 2 && <span className="text-terminal-green">COBROS ✓</span>}
        {run.steps_completed >= 3 && <span className="text-terminal-green">CAJA ✓</span>}
        {run.steps_completed < 2 && <span className="text-terminal-gray">COBROS ─</span>}
        {run.steps_completed < 3 && <span className="text-terminal-gray">CAJA ─</span>}

        {/* Download buttons */}
        <div className="ml-auto flex gap-2">
          {[1, 2, 3].map((step) => (
            run.steps_completed >= step && (
              <button
                key={step}
                onClick={(e) => { e.stopPropagation(); downloadFile(run.id, step); }}
                className="text-terminal-green border border-terminal-green rounded px-1.5 py-0.5
                  hover:bg-terminal-green hover:text-terminal-bg transition-colors text-xs"
              >
                ↓ S{step}
              </button>
            )
          ))}
          <button
            onClick={(e) => { e.stopPropagation(); handleDelete(); }}
            disabled={deleting}
            className="text-terminal-red border border-terminal-red rounded px-1.5 py-0.5
              hover:bg-terminal-red hover:text-terminal-bg transition-colors text-xs disabled:opacity-40"
          >
            {deleting ? '...' : '✗'}
          </button>
        </div>
      </div>

      {/* Expanded: transaction table */}
      {expanded && (
        <div className="border-t border-terminal-border px-3 py-2">
          {txLoading ? (
            <div className="text-terminal-cyan animate-pulse py-2">Loading transactions...</div>
          ) : transactions.length === 0 ? (
            <div className="text-terminal-gray py-2">No transactions found.</div>
          ) : (
            <>
              {/* Output files */}
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

              {/* Transaction table */}
              <div className="text-terminal-gray mb-1">
                Showing {transactions.length} of {txTotal} transactions
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="text-terminal-cyan border-b border-terminal-border">
                      <th className="text-left py-1 pr-3">FECHA</th>
                      <th className="text-left py-1 pr-3">BANCO</th>
                      <th className="text-left py-1 pr-3">DESCRIPCION</th>
                      <th className="text-right py-1 pr-3">MONTO</th>
                      <th className="text-left py-1">CAT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx) => (
                      <tr key={tx.id} className="border-b border-terminal-border/30 hover:bg-terminal-border/20">
                        <td className="py-0.5 pr-3 text-terminal-gray">{tx.fecha}</td>
                        <td className="py-0.5 pr-3 text-terminal-amber">{tx.banco}</td>
                        <td className="py-0.5 pr-3 text-terminal-white truncate max-w-xs">{tx.descripcion}</td>
                        <td className={`py-0.5 pr-3 text-right tabular-nums ${tx.monto >= 0 ? 'text-terminal-green' : 'text-terminal-red'}`}>
                          {tx.monto.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
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
```

Write to `frontend/components/RunCard.tsx`.

---

### Task 8: Root layout

**Files:**
- Create: `frontend/app/layout.tsx`

- [ ] **Step 1: Create app/layout.tsx**

```tsx
// frontend/app/layout.tsx
import type { Metadata } from 'next';
import './globals.css';
import NavBar from '@/components/NavBar';

export const metadata: Metadata = {
  title: 'ARGUS v3.0.0 — Sistema de Reconciliación Bancaria',
  description: 'ARGUS — Delfabro Group banking reconciliation system',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-terminal-bg text-terminal-white font-mono">
        <NavBar />
        <main className="flex-1">
          {children}
        </main>
      </body>
    </html>
  );
}
```

Write to `frontend/app/layout.tsx`.

- [ ] **Step 2: Create NavBar component**

```tsx
// frontend/components/NavBar.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useUptime } from '@/lib/useUptime';

export default function NavBar() {
  const pathname = usePathname();
  const uptime = useUptime();

  return (
    <header className="border-b border-terminal-border bg-terminal-bg-secondary sticky top-0 z-50">
      <div className="flex items-center gap-0 h-10 px-4 font-mono text-xs">
        {/* Brand */}
        <span className="text-terminal-green font-bold glow-green mr-4">
          ■ ARGUS
        </span>
        <span className="text-terminal-gray mr-4 hidden sm:block">
          v3.0.0 ■ SISTEMA DE RECONCILIACIÓN BANCARIA ■ DELFABRO GROUP
        </span>

        {/* Prompt */}
        <span className="text-terminal-gray hidden md:block mr-6">
          [root@argus:~$]
        </span>

        {/* Nav links */}
        <nav className="flex gap-1 mr-auto">
          <Link
            href="/"
            className={`px-3 py-1 rounded text-xs transition-colors
              ${pathname === '/'
                ? 'text-terminal-cyan border border-terminal-cyan'
                : 'text-terminal-gray hover:text-terminal-white'
              }`}
          >
            DASHBOARD
          </Link>
          <Link
            href="/run"
            className={`px-3 py-1 rounded text-xs transition-colors
              ${pathname === '/run'
                ? 'text-terminal-green border border-terminal-green'
                : 'text-terminal-gray hover:text-terminal-white'
              }`}
          >
            NUEVO RUN
          </Link>
        </nav>

        {/* Uptime */}
        <span className="text-terminal-gray text-xs tabular-nums">
          uptime: <span className="text-terminal-green">{uptime}</span>
        </span>
      </div>
    </header>
  );
}
```

Write to `frontend/components/NavBar.tsx`.

---

### Task 9: Dashboard page

**Files:**
- Create: `frontend/app/page.tsx`

- [ ] **Step 1: Create dashboard page**

```tsx
// frontend/app/page.tsx
'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import type { Run } from '@/lib/types';
import { getRuns } from '@/lib/api';
import RunCard from '@/components/RunCard';

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
    fetchRuns();
    const interval = setInterval(fetchRuns, 15000); // auto-refresh every 15s
    return () => clearInterval(interval);
  }, [fetchRuns]);

  function handleDeleted(id: string) {
    setRuns((prev) => prev.filter((r) => r.id !== id));
  }

  const totalTx = runs.reduce((s, r) => s + r.transactions_total, 0);
  const lastRunAgo = runs[0]
    ? Math.round((Date.now() - new Date(runs[0].created_at).getTime()) / 60000)
    : null;

  return (
    <div className="p-4 font-mono text-xs max-w-6xl mx-auto">
      {/* Shell prompt header */}
      <div className="border border-terminal-border rounded mb-4 bg-terminal-bg-card">
        <div className="border-b border-terminal-border px-3 py-2 text-terminal-green">
          root@argus:~$ ls -la runs/
        </div>

        {/* Stats bar */}
        <div className="flex items-center gap-4 px-3 py-2 border-b border-terminal-border text-terminal-gray">
          <span className="text-terminal-cyan font-bold">RUNS HISTORY</span>
          <span>──</span>
          <span>
            <span className="text-terminal-white">{runs.length}</span> runs
          </span>
          <span>│</span>
          <span>
            total: <span className="text-terminal-white">{totalTx.toLocaleString()}</span> tx
          </span>
          {lastRunAgo !== null && (
            <>
              <span>│</span>
              <span>
                last: <span className="text-terminal-white">
                  {lastRunAgo < 60 ? `${lastRunAgo}m ago` : `${Math.round(lastRunAgo / 60)}h ago`}
                </span>
              </span>
            </>
          )}
          <span className="ml-auto flex items-center gap-2">
            <button
              onClick={fetchRuns}
              className="text-terminal-gray hover:text-terminal-white border border-terminal-border
                rounded px-2 py-0.5 transition-colors"
            >
              ↻ refresh
            </button>
            <span className="text-terminal-gray-dim text-xs">
              {lastRefresh.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          </span>
        </div>

        {/* New run CTA */}
        <div className="px-3 py-2 border-b border-terminal-border">
          <Link
            href="/run"
            className="inline-flex items-center gap-2 px-4 py-2 border border-terminal-green
              text-terminal-green rounded text-sm font-bold hover:bg-terminal-green hover:text-terminal-bg
              transition-all glow-green"
          >
            ▶ NUEVO RUN →
          </Link>
        </div>

        {/* Run list */}
        <div className="p-3">
          {loading && (
            <div className="text-terminal-cyan animate-pulse py-4">
              root@argus:~$ Loading runs...
            </div>
          )}

          {error && (
            <div className="text-terminal-red border border-terminal-red/30 rounded p-3 mb-3">
              ✗ Error fetching runs: {error}
              <br />
              <span className="text-terminal-gray">Make sure the backend is running at {process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}</span>
            </div>
          )}

          {!loading && runs.length === 0 && !error && (
            <div className="text-terminal-gray py-4 text-center">
              <div>total 0</div>
              <div className="mt-2">No runs found. Start your first run →</div>
            </div>
          )}

          {runs.map((run) => (
            <RunCard key={run.id} run={run} onDeleted={handleDeleted} />
          ))}
        </div>
      </div>

      {/* System info footer */}
      <div className="text-terminal-gray-dim text-xs border border-terminal-border rounded px-3 py-2 flex gap-4">
        <span>ARGUS v3.0.0</span>
        <span>│</span>
        <span>backend: <span className="text-terminal-white">{process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}</span></span>
        <span>│</span>
        <span>Delfabro Group © 2026</span>
      </div>
    </div>
  );
}
```

Write to `frontend/app/page.tsx`.

---

### Task 10: New Run page (3-step pipeline)

**Files:**
- Create: `frontend/app/run/page.tsx`

- [ ] **Step 1: Create run page**

```tsx
// frontend/app/run/page.tsx
'use client';

import { useState, useCallback, useRef } from 'react';
import type { LogLine, StepState, SSEEvent } from '@/lib/types';
import { streamPaso1, streamPaso2, streamPaso3, downloadFile } from '@/lib/api';
import TerminalLog from '@/components/TerminalLog';
import StepPanel from '@/components/StepPanel';

function makeLogLine(msg: string, ts?: string): LogLine {
  const type: LogLine['type'] =
    msg.includes('✓') || msg.includes('COMPLETADO') ? 'success' :
    msg.includes('⚠') || msg.includes('ERROR HUMANO') || msg.includes('FALTA') ? 'warning' :
    msg.includes('✗') || msg.includes('Error') || msg.includes('error') ? 'error' :
    msg.startsWith('═') || msg.startsWith('─') ? 'separator' :
    'info';

  return {
    id: `${Date.now()}-${Math.random()}`,
    ts: ts || new Date().toLocaleTimeString('es-AR', { hour12: false }),
    msg,
    type,
  };
}

const INITIAL_STEP_STATE: StepState = { status: 'idle', progress: 0 };

export default function RunPage() {
  const [logLines, setLogLines] = useState<LogLine[]>([
    makeLogLine('root@argus:~/run$ ./argus --interactive', '00:00:00'),
    makeLogLine('ARGUS v3.0.0 — Sistema de Reconciliación Bancaria', '00:00:00'),
    makeLogLine('Delfabro Group — ready for input', '00:00:00'),
    { id: 'sep0', ts: '', msg: '', type: 'separator' },
  ]);

  const [step1, setStep1] = useState<StepState>({ ...INITIAL_STEP_STATE });
  const [step2, setStep2] = useState<StepState>({ ...INITIAL_STEP_STATE, status: 'locked' });
  const [step3, setStep3] = useState<StepState>({ ...INITIAL_STEP_STATE, status: 'locked' });

  const [runId, setRunId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const cancelRef = useRef<(() => void) | null>(null);

  const addLog = useCallback((msg: string, ts?: string) => {
    setLogLines((prev) => [...prev, makeLogLine(msg, ts)]);
  }, []);

  // ── Step 1 ─────────────────────────────────────────────────────────────────

  function executeStep1() {
    if (!step1.file) return;
    setStep1((s) => ({ ...s, status: 'running', progress: 5 }));
    setIsRunning(true);
    addLog('⚡ Iniciando ARGUS v3.0.0 — Paso 1: Movimientos Bancarios');

    cancelRef.current = streamPaso1(step1.file, (event: SSEEvent) => {
      if (event.type === 'log') {
        addLog(event.msg, event.ts);
      } else if (event.type === 'progress') {
        setStep1((s) => ({ ...s, progress: event.pct }));
      } else if (event.type === 'done') {
        setRunId(event.run_id);
        setStep1((s) => ({ ...s, status: 'done', progress: 100 }));
        setStep2((s) => ({ ...s, status: 'idle' }));
        setIsRunning(false);
        addLog('════════════════════════════════════════');
        addLog(`✓ PASO 1 COMPLETADO — run_id: ${event.run_id}`);
        addLog('════════════════════════════════════════');
      } else if (event.type === 'error') {
        setStep1((s) => ({ ...s, status: 'error', errorMsg: event.msg }));
        setIsRunning(false);
        addLog(`✗ ERROR: ${event.msg}`);
      }
    });
  }

  // ── Step 2 ─────────────────────────────────────────────────────────────────

  function executeStep2() {
    if (!runId || !step2.file || !step2.file2) return;
    setStep2((s) => ({ ...s, status: 'running', progress: 5 }));
    setIsRunning(true);
    addLog('⚡ Iniciando Paso 2 — Conciliación ERP Coliseo');

    cancelRef.current = streamPaso2(runId, step2.file, step2.file2, (event: SSEEvent) => {
      if (event.type === 'log') {
        addLog(event.msg, event.ts);
      } else if (event.type === 'progress') {
        setStep2((s) => ({ ...s, progress: event.pct }));
      } else if (event.type === 'done') {
        setStep2((s) => ({ ...s, status: 'done', progress: 100 }));
        setStep3((s) => ({ ...s, status: 'idle' }));
        setIsRunning(false);
        addLog('════════════════════════════════════════');
        addLog('✓ PASO 2 COMPLETADO — Conciliación lista');
        addLog('════════════════════════════════════════');
      } else if (event.type === 'error') {
        setStep2((s) => ({ ...s, status: 'error', errorMsg: event.msg }));
        setIsRunning(false);
        addLog(`✗ ERROR: ${event.msg}`);
      }
    });
  }

  // ── Step 3 ─────────────────────────────────────────────────────────────────

  function executeStep3() {
    if (!runId || !step3.file) return;
    setStep3((s) => ({ ...s, status: 'running', progress: 5 }));
    setIsRunning(true);
    addLog('⚡ Iniciando Paso 3 — Export Caja Fábrica Digital');

    cancelRef.current = streamPaso3(runId, step3.file, (event: SSEEvent) => {
      if (event.type === 'log') {
        addLog(event.msg, event.ts);
      } else if (event.type === 'progress') {
        setStep3((s) => ({ ...s, progress: event.pct }));
      } else if (event.type === 'done') {
        setStep3((s) => ({ ...s, status: 'done', progress: 100 }));
        setIsRunning(false);
        addLog('════════════════════════════════════════');
        addLog('✓ TODOS LOS PASOS COMPLETADOS');
        addLog(`  Run ID: ${event.run_id}`);
        addLog('  Descarga los archivos de salida →');
        addLog('════════════════════════════════════════');
      } else if (event.type === 'error') {
        setStep3((s) => ({ ...s, status: 'error', errorMsg: event.msg }));
        setIsRunning(false);
        addLog(`✗ ERROR: ${event.msg}`);
      }
    });
  }

  function handleReset() {
    cancelRef.current?.();
    setStep1({ ...INITIAL_STEP_STATE });
    setStep2({ ...INITIAL_STEP_STATE, status: 'locked' });
    setStep3({ ...INITIAL_STEP_STATE, status: 'locked' });
    setRunId(null);
    setIsRunning(false);
    setLogLines([
      makeLogLine('root@argus:~/run$ ./argus --interactive'),
      makeLogLine('Pipeline reset — ready for new run'),
      { id: `sep-${Date.now()}`, ts: '', msg: '', type: 'separator' },
    ]);
  }

  return (
    <div className="h-[calc(100vh-40px)] flex flex-col md:flex-row gap-0 font-mono text-xs overflow-hidden">
      {/* ── Left: Step controls ─────────────────────────────────────────── */}
      <div className="w-full md:w-72 lg:w-80 border-r border-terminal-border bg-terminal-bg-secondary overflow-y-auto p-3 shrink-0">
        <div className="text-terminal-gray mb-3 border-b border-terminal-border pb-2">
          <span className="text-terminal-green font-bold">PIPELINE</span>
          <span className="text-terminal-gray ml-2">
            {runId ? `─ run_${runId.slice(0, 8)}` : '─ no active run'}
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

        {/* Reset */}
        <div className="border-t border-terminal-border pt-3 mt-1">
          <button
            onClick={handleReset}
            className="w-full px-3 py-1.5 border border-terminal-red text-terminal-red
              rounded text-xs font-mono hover:bg-terminal-red hover:text-terminal-bg transition-all"
          >
            ↺ RESET PIPELINE
          </button>
        </div>

        {/* Run ID display */}
        {runId && (
          <div className="mt-3 p-2 border border-terminal-border rounded bg-terminal-bg text-terminal-gray text-xs">
            <div className="text-terminal-gray-dim">run_id:</div>
            <div className="text-terminal-cyan break-all">{runId}</div>
          </div>
        )}
      </div>

      {/* ── Right: Terminal log ─────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 p-3">
        <TerminalLog
          lines={logLines}
          isRunning={isRunning}
          title={`root@argus:~/run$ ./argus${runId ? ` --run=${runId.slice(0, 8)}` : ''}`}
        />
      </div>
    </div>
  );
}
```

Write to `frontend/app/run/page.tsx`.

---

### Task 11: Install dependencies and verify build

**Files:** None (shell commands only)

- [ ] **Step 1: Install npm dependencies**

```bash
cd /c/Users/manol/OneDrive/Documents/GITHUB_repo/argus-web/frontend
npm install
```

Expected: packages install without errors, `node_modules/` created.

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd /c/Users/manol/OneDrive/Documents/GITHUB_repo/argus-web/frontend
npx tsc --noEmit
```

Expected: No errors. If errors appear, fix the indicated file + line.

- [ ] **Step 3: Run dev server to spot-check**

```bash
cd /c/Users/manol/OneDrive/Documents/GITHUB_repo/argus-web/frontend
npm run dev
```

Expected: "ready - started server on 0.0.0.0:3000".
Open http://localhost:3000 — should show ARGUS dashboard with terminal aesthetic.

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: add ARGUS Web Next.js frontend with terminal aesthetic"
```

---

## Self-Review

**Spec coverage:**
- [x] package.json, tailwind config, postcss, tsconfig, next.config — Task 1
- [x] globals.css with JetBrains Mono, scanlines, cursor blink, custom scrollbar — Task 1
- [x] Terminal color palette (green, cyan, amber, red, purple) — Task 1
- [x] All API functions: getRuns, getRun, getTransactions, getReconciliation, getOutputFiles, downloadFile — Task 2
- [x] SSE streaming for paso1, paso2, paso3 using fetch + ReadableStream — Task 2
- [x] TerminalLog with auto-scroll, color coding, cursor blink, timestamps — Task 4
- [x] ProgressBar with block characters — Task 5
- [x] StepPanel with all 5 states (idle, running, done, locked, error) — Task 6
- [x] RunCard in `ls -la` style with expandable transaction table — Task 7
- [x] NavBar with uptime counter — Task 8
- [x] Dashboard page with run history, stats, auto-refresh — Task 9
- [x] New Run page with split-panel layout (steps left, log right) — Task 10
- [x] Step 2 takes two files (cobros + pagos) — Task 6, 10
- [x] Step colors: cyan=1, green=2, purple=3 — Task 6, 10
- [x] All three steps unlock sequentially after completion — Task 10
- [x] Download buttons per step — Tasks 6, 7, 10
- [x] .env.example — Task 1

**Placeholder scan:** No TBDs, TODOs, or "implement later" found.

**Type consistency:** `StepState`, `LogLine`, `SSEEvent`, `Run` defined in `lib/types.ts` and used consistently across all components and pages.
