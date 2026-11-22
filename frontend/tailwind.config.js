/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        blush: '#FFF0F5',
        'blush-pattern': '#FCE4EC',
        'pastel-pink': '#F8BBD0',
        'rose-pink': '#F48FB1',
        'berry-pink': '#EC407A',
        'dusty-mauve': '#4A353D',
        pearl: '#FFFFFF',
      },
      fontFamily: {
        display: ['"Playfair Display"', 'serif'],
        body: ['"Quicksand"', 'sans-serif'],
      },
      borderRadius: {
        '4xl': '2rem',
      },
      boxShadow: {
        'pink-soft': '0 10px 30px rgba(244, 143, 177, 0.25)',
        'pink-hover': '0 15px 40px rgba(236, 64, 122, 0.3)',
      },
      keyframes: {
        'bounce-soft': {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.07)' },
        },
        'heartbeat': {
          '0%, 100%': { transform: 'scale(1)' },
          '14%': { transform: 'scale(1.15)' },
          '28%': { transform: 'scale(1)' },
          '42%': { transform: 'scale(1.15)' },
          '56%': { transform: 'scale(1)' },
        },
        'sparkle': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.5', transform: 'scale(0.8)' },
        },
        'ribbon-sway': {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'bounce-soft': 'bounce-soft 0.4s ease-in-out',
        'heartbeat': 'heartbeat 1.2s ease-in-out infinite',
        'sparkle': 'sparkle 1.5s ease-in-out infinite',
        'ribbon-sway': 'ribbon-sway 3s ease-in-out infinite',
        'fade-in-up': 'fade-in-up 0.5s ease-out',
      },
    },
  },
  plugins: [],
}
