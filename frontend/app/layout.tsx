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
      <body className="min-h-screen bg-terminal-bg text-terminal-white font-mono flex flex-col">
        <NavBar />
        <main className="flex-1 flex flex-col min-h-0">{children}</main>
      </body>
    </html>
  );
}
