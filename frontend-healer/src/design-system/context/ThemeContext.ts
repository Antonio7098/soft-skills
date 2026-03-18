import { createContext, useContext } from 'react';
import type { Theme, ThemeId } from '../themes/types';

/**
 * Theme context value.
 */
export interface ThemeContextValue {
  /** Current active theme */
  theme: Theme;
  /** Current theme ID */
  themeId: ThemeId;
  /** Switch to a different theme */
  setTheme: (id: ThemeId) => void;
  /** Toggle between available themes */
  toggleTheme: () => void;
  /** List of available theme IDs */
  availableThemes: ThemeId[];
}

/**
 * React context for theme access.
 */
export const ThemeContext = createContext<ThemeContextValue | null>(null);

/**
 * Hook to access current theme.
 * Throws if used outside ThemeProvider.
 */
export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
