import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: 'class',
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        earth: {
          950: '#070a12',
          900: '#0b0f19',
          850: '#111728',
          800: '#172036',
          700: '#1f2b48',
          600: '#2b3b60',
        },
        cyanGlow: {
          400: '#38bdf8',
          500: '#00f2fe',
          600: '#0284c7',
        },
        emeraldGlow: {
          400: '#34d399',
          500: '#10b981',
        },
        warningAmber: {
          400: '#fbbf24',
          500: '#f59e0b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glow-cyan': '0 0 20px -3px rgba(0, 242, 254, 0.3)',
        'glow-emerald': '0 0 20px -3px rgba(16, 185, 129, 0.3)',
        'glow-amber': '0 0 20px -3px rgba(245, 158, 11, 0.3)',
      },
    },
  },
  plugins: [],
};
export default config;
