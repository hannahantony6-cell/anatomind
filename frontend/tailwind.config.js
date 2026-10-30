/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: { 50: '#f2f6fb', 100: '#e1eaf5', 200: '#c3d4ea', 600: '#25507f', 700: '#1b3d65', 800: '#142f50', 900: '#0d2038' },
        teal: { 50: '#effbf9', 100: '#d3f5ef', 500: '#14a595', 600: '#0d8a7c', 700: '#0f6f65' },
        sky: { 25: '#f6faff', 50: '#eef6fd', 100: '#dcecfa' },
      },
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'] },
      boxShadow: { card: '0 1px 2px rgba(13,32,56,0.04), 0 4px 16px rgba(13,32,56,0.05)' },
    },
  },
  plugins: [],
}
