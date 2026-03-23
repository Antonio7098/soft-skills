import { useEffect } from 'react';
import { useTheme, generateThemeCSS } from '../theme';

const STYLE_ID = 'theme-css-vars';

export function useThemeStyles(): void {
  const { activeTheme } = useTheme();

  useEffect(() => {
    let styleEl = document.getElementById(STYLE_ID);

    if (!styleEl) {
      styleEl = document.createElement('style');
      styleEl.id = STYLE_ID;
      document.head.appendChild(styleEl);
    }

    styleEl.textContent = generateThemeCSS(activeTheme);
  }, [activeTheme]);
}
