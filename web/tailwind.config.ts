import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [],
  corePlugins: {
    preflight: false, // 避免与 Ant Design 样式冲突
  },
} satisfies Config
