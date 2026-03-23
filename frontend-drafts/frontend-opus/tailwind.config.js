/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          primary: 'var(--color-surface-primary)',
          secondary: 'var(--color-surface-secondary)',
          elevated: 'var(--color-surface-elevated)',
          inverse: 'var(--color-surface-inverse)',
        },
        content: {
          primary: 'var(--color-content-primary)',
          secondary: 'var(--color-content-secondary)',
          tertiary: 'var(--color-content-tertiary)',
          inverse: 'var(--color-content-inverse)',
        },
        accent: {
          DEFAULT: 'var(--color-accent)',
          hover: 'var(--color-accent-hover)',
          muted: 'var(--color-accent-muted)',
          text: 'var(--color-accent-text)',
        },
        line: {
          DEFAULT: 'var(--color-line)',
          hover: 'var(--color-line-hover)',
        },
        status: {
          success: 'var(--color-status-success)',
          error: 'var(--color-status-error)',
          warning: 'var(--color-status-warning)',
          info: 'var(--color-status-info)',
        },
        sidebar: {
          bg: 'var(--color-sidebar-bg)',
          text: 'var(--color-sidebar-text)',
          'text-muted': 'var(--color-sidebar-text-muted)',
          'item-hover': 'var(--color-sidebar-item-hover)',
          'item-active': 'var(--color-sidebar-item-active)',
        },
      },
      fontFamily: {
        display: ['"IBM Plex Sans"', 'sans-serif'],
        body: ['"Source Sans 3"', 'sans-serif'],
      },
      fontSize: {
        'display-xl': ['3rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'display-lg': ['2.25rem', { lineHeight: '1.15', letterSpacing: '-0.015em' }],
        'display-md': ['1.75rem', { lineHeight: '1.2', letterSpacing: '-0.01em' }],
        'display-sm': ['1.375rem', { lineHeight: '1.3', letterSpacing: '-0.005em' }],
        'body-lg': ['1.125rem', { lineHeight: '1.6' }],
        'body-md': ['0.9375rem', { lineHeight: '1.6' }],
        'body-sm': ['0.8125rem', { lineHeight: '1.5' }],
        'body-xs': ['0.6875rem', { lineHeight: '1.5' }],
      },
      borderRadius: {
        card: '10px',
        input: '8px',
        badge: '6px',
        button: '8px',
      },
      boxShadow: {
        card: 'var(--shadow-card)',
        'card-hover': 'var(--shadow-card-hover)',
        elevated: 'var(--shadow-elevated)',
      },
      transitionDuration: {
        theme: '300ms',
      },
      keyframes: {
        'skeleton-pulse': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-left': {
          from: { opacity: '0', transform: 'translateX(-12px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.95)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        spin: {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        'skeleton-pulse': 'skeleton-pulse 1.8s ease-in-out infinite',
        'fade-in': 'fade-in 0.4s ease-out forwards',
        'slide-in-left': 'slide-in-left 0.3s ease-out forwards',
        'scale-in': 'scale-in 0.25s ease-out forwards',
        spin: 'spin 1s linear infinite',
      },
    },
  },
  plugins: [],
};
