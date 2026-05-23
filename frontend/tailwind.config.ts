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
