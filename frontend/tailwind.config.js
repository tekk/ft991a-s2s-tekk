/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'IBM Plex Mono', 'Fira Code', 'ui-monospace', 'monospace'],
      },
      colors: {
        shack: {
          950: '#070a0f',
          900: '#0b0f17',
          850: '#101622',
          800: '#161e2e',
          700: '#222d42',
          600: '#334155',
          amber: '#f59e0b',
          amberGlow: '#fbbf24',
          cyan: '#06b6d4',
          cyanGlow: '#22d3ee',
          green: '#10b981',
          greenGlow: '#34d399',
          red: '#ef4444',
        }
      },
      boxShadow: {
        'glow-amber': '0 0 15px rgba(245, 158, 11, 0.35)',
        'glow-cyan': '0 0 15px rgba(6, 182, 212, 0.35)',
        'glow-green': '0 0 15px rgba(16, 185, 129, 0.35)',
        'glow-red': '0 0 15px rgba(239, 68, 68, 0.45)',
      }
    },
  },
  plugins: [],
}
