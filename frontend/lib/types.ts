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
  file2?: File;
  progress: number;
  errorMsg?: string;
}
