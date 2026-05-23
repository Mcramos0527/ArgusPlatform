'use client';

interface ProgressBarProps {
  pct: number;
  isRunning: boolean;
  color?: string;
}

export default function ProgressBar({
  pct,
  isRunning,
  color = 'text-terminal-cyan',
}: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, pct));
  const filled = Math.round(clamped / 5); // 20 blocks total
  const empty = 20 - filled;

  const blocks = '█'.repeat(filled) + '─'.repeat(empty);

  return (
    <div className="flex items-center gap-2 font-mono text-xs">
      <span className="text-terminal-gray">[</span>
      <span className={color}>{blocks}</span>
      <span className="text-terminal-gray">]</span>
      <span className={`${color} tabular-nums`}>{clamped}%</span>
      {isRunning && (
        <span className="text-terminal-cyan animate-pulse text-xs">●</span>
      )}
    </div>
  );
}
