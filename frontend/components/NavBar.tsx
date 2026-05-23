'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useUptime } from '@/lib/useUptime';

export default function NavBar() {
  const pathname = usePathname();
  const uptime = useUptime();

  return (
    <header className="border-b border-terminal-border bg-terminal-bg-secondary sticky top-0 z-50">
      <div className="flex items-center h-10 px-4 font-mono text-xs gap-3">
        {/* Brand */}
        <span className="text-terminal-green font-bold glow-green shrink-0">
          ■ ARGUS
        </span>
        <span className="text-terminal-gray hidden lg:block shrink-0">
          v3.0.0 ■ RECONCILIACIÓN BANCARIA ■ DELFABRO GROUP
        </span>
        <span className="text-terminal-gray hidden md:block lg:hidden shrink-0">
          v3.0.0
        </span>

        {/* Prompt */}
        <span className="text-terminal-gray hidden xl:block shrink-0">[root@argus:~$]</span>

        {/* Nav links */}
        <nav className="flex gap-1 ml-auto mr-3">
          <Link
            href="/"
            className={`px-3 py-1 rounded text-xs transition-colors
              ${
                pathname === '/'
                  ? 'text-terminal-cyan border border-terminal-cyan'
                  : 'text-terminal-gray hover:text-terminal-white'
              }`}
          >
            DASHBOARD
          </Link>
          <Link
            href="/run"
            className={`px-3 py-1 rounded text-xs transition-colors font-bold
              ${
                pathname === '/run'
                  ? 'text-terminal-green border border-terminal-green'
                  : 'text-terminal-gray hover:text-terminal-green'
              }`}
          >
            + NUEVO RUN
          </Link>
        </nav>

        {/* Uptime */}
        <span className="text-terminal-gray text-xs tabular-nums shrink-0">
          uptime:{' '}
          <span className="text-terminal-green">{uptime}</span>
        </span>
      </div>
    </header>
  );
}
