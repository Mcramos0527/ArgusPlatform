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
    <div className="flex flex-col h-full bg-terminal-bg border border-terminal-border rounded overflow-hidden">
      {/* Terminal header bar */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-terminal-border bg-terminal-bg-secondary shrink-0">
        <div className="flex gap-1.5">
          <span className="w-3 h-3 rounded-full bg-terminal-red opacity-80" />
          <span className="w-3 h-3 rounded-full bg-terminal-amber opacity-80" />
          <span className="w-3 h-3 rounded-full bg-terminal-green opacity-80" />
        </div>
        <span className="ml-2 text-xs text-terminal-gray font-mono truncate">{title}</span>
        {isRunning && (
          <span className="ml-auto text-xs text-terminal-cyan animate-pulse shrink-0">
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
              <span className="text-terminal-gray-dim w-full overflow-hidden">
                {line.msg || '════════════════════════════════════════════════════'}
              </span>
            ) : (
              <>
                <span className="text-terminal-gray shrink-0 select-none tabular-nums">
                  [{line.ts || '--:--:--'}]
                </span>
                <span className="break-words min-w-0">{line.msg}</span>
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
