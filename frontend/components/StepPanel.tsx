'use client';

import { useRef } from 'react';
import type { StepStatus } from '@/lib/types';
import ProgressBar from './ProgressBar';

interface StepPanelProps {
  step: number;
  title: string;
  description: string;
  status: StepStatus;
  accent: 'cyan' | 'green' | 'purple';
  progress: number;
  fileLabel: string;
  file?: File;
  file2Label?: string;
  file2?: File;
  onFileChange: (file: File) => void;
  onFile2Change?: (file: File) => void;
  onExecute: () => void;
  onDownload?: () => void;
  errorMsg?: string;
  runId?: string;
}

const accentStyles = {
  cyan: {
    text: 'text-terminal-cyan',
    border: 'border-terminal-cyan',
    hoverText: 'hover:text-terminal-cyan',
    hoverBorder: 'hover:border-terminal-cyan',
    progressColor: 'text-terminal-cyan',
  },
  green: {
    text: 'text-terminal-green',
    border: 'border-terminal-green',
    hoverText: 'hover:text-terminal-green',
    hoverBorder: 'hover:border-terminal-green',
    progressColor: 'text-terminal-green',
  },
  purple: {
    text: 'text-terminal-purple',
    border: 'border-terminal-purple',
    hoverText: 'hover:text-terminal-purple',
    hoverBorder: 'hover:border-terminal-purple',
    progressColor: 'text-terminal-purple',
  },
} as const;

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
  const colors = accentStyles[accent];

  const isLocked = status === 'locked';
  const isRunning = status === 'running';
  const isDone = status === 'done';
  const isError = status === 'error';
  const isIdle = status === 'idle';

  const canExecute =
    (isIdle || isError) &&
    !!file &&
    (file2Label === undefined || !!file2);

  function handleFileChange(
    e: React.ChangeEvent<HTMLInputElement>,
    which: 'primary' | 'secondary'
  ) {
    const f = e.target.files?.[0];
    if (!f) return;
    if (which === 'primary') onFileChange(f);
    else onFile2Change?.(f);
    // Reset input so same file can be re-selected
    e.target.value = '';
  }

  const stepIcon =
    isDone    ? '✓' :
    isError   ? '✗' :
    isRunning ? '▶' :
    isLocked  ? '●' :
    '○';

  const stepColor =
    isLocked  ? 'text-terminal-gray' :
    isDone    ? 'text-terminal-green' :
    isError   ? 'text-terminal-red' :
    isRunning ? 'text-terminal-cyan' :
    colors.text;

  const borderColor =
    isLocked  ? 'border-terminal-border' :
    isError   ? 'border-terminal-red' :
    isDone    ? 'border-terminal-green' :
    isRunning ? 'border-terminal-cyan' :
    colors.border;

  return (
    <div
      className={`border rounded p-3 mb-3 bg-terminal-bg-card font-mono text-xs transition-all
        ${borderColor}
        ${isLocked ? 'opacity-50' : ''}
        ${isRunning ? 'shadow-lg shadow-terminal-cyan/10' : ''}
      `}
    >
      {/* Step header */}
      <div className="flex items-center gap-2 mb-1">
        <span className={`font-bold text-sm ${stepColor} ${isRunning ? 'animate-pulse' : ''}`}>
          {stepIcon} [{step}] {title}
        </span>
        <span className={`ml-auto text-xs ${stepColor}`}>
          {isDone    ? 'COMPLETE' :
           isRunning ? 'RUNNING' :
           isLocked  ? 'LOCKED' :
           isError   ? 'ERROR' :
           'READY'}
        </span>
      </div>

      <div className="text-terminal-gray text-xs mb-2 leading-relaxed">{description}</div>

      {/* Running: progress bar */}
      {isRunning && (
        <div className="mb-2">
          <ProgressBar pct={progress} isRunning color={colors.progressColor} />
        </div>
      )}

      {/* Error message */}
      {isError && errorMsg && (
        <div className="text-terminal-red text-xs mb-2 border border-terminal-red/30 rounded p-2 bg-terminal-red/5 break-words">
          ✗ {errorMsg}
        </div>
      )}

      {/* File inputs — show when idle or error */}
      {(isIdle || isError) && (
        <div className="space-y-1.5">
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
              className={`w-full text-left px-2 py-1.5 border rounded text-xs font-mono
                border-terminal-border-bright text-terminal-gray
                hover:border-terminal-border-bright ${colors.hoverText}
                transition-colors truncate
              `}
            >
              📁 {file ? file.name : fileLabel}
            </button>
          </div>

          {/* Secondary file (step 2: pagos) */}
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
                className={`w-full text-left px-2 py-1.5 border rounded text-xs font-mono
                  border-terminal-border-bright text-terminal-gray
                  hover:border-terminal-border-bright ${colors.hoverText}
                  transition-colors truncate
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
            className={`w-full px-3 py-2 border rounded text-xs font-mono font-bold
              transition-all
              ${canExecute
                ? `${colors.border} ${colors.text} hover:bg-terminal-border cursor-pointer active:scale-95`
                : 'border-terminal-gray-dim text-terminal-gray-dim cursor-not-allowed opacity-40'
              }
            `}
          >
            ▶ EJECUTAR
          </button>
        </div>
      )}

      {/* Done: download button */}
      {isDone && onDownload && (
        <button
          onClick={onDownload}
          className="w-full mt-1 px-3 py-2 border border-terminal-green text-terminal-green
            rounded text-xs font-mono font-bold hover:bg-terminal-green hover:text-terminal-bg
            transition-all active:scale-95"
        >
          ↓ DESCARGAR XLSX
        </button>
      )}
    </div>
  );
}
