import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // SmartCanopy brand colors
        canopy: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        // Tree equity colors
        equity: {
          critical: '#ef4444', // RED - <15% canopy
          low: '#f97316',      // ORANGE - 15-25% canopy
          healthy: '#22c55e',  // GREEN - >25% canopy
        },
        // Priority colors for planting sites
        priority: {
          high: '#3b82f6',     // Blue - high suitability
          medium: '#f59e0b',   // Amber - medium suitability
          low: '#6b7280',      // Gray - low suitability
        }
      },
    },
  },
  plugins: [],
}
export default config
