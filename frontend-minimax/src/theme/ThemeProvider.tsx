import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  type ReactNode,
  type JSX,
} from 'react';
import type { Theme, ThemeId } from '../types/theme';
import { obsidianTheme, parchmentTheme, neonTheme } from './themes';

interface ThemeContextValue {
  activeTheme: Theme;
  activeThemeId: ThemeId;
  themes: Record<ThemeId, Theme>;
  setTheme: (id: ThemeId) => void;
  toggleTheme: () => void;
  cycleTheme: () => void;
}

const themes: Record<ThemeId, Theme> = {
  obsidian: obsidianTheme,
  parchment: parchmentTheme,
  neon: neonTheme,
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = 'softskills-theme';
const THEME_ORDER: ThemeId[] = ['obsidian', 'parchment', 'neon'];

function getStoredTheme(): ThemeId {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && stored in themes) {
      return stored as ThemeId;
    }
  } catch {}
  return 'obsidian';
}

function storeTheme(id: ThemeId): void {
  try {
    localStorage.setItem(STORAGE_KEY, id);
  } catch {}
}

interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: ThemeId;
}

export function ThemeProvider({
  children,
  defaultTheme,
}: ThemeProviderProps): JSX.Element {
  const [activeThemeId, setActiveThemeId] = useState<ThemeId>(
    () => defaultTheme ?? getStoredTheme()
  );

  const setTheme = useCallback((id: ThemeId) => {
    setActiveThemeId(id);
    storeTheme(id);
  }, []);

  const toggleTheme = useCallback(() => {
    setActiveThemeId((prev) => {
      const next = prev === 'obsidian' ? 'parchment' : prev === 'parchment' ? 'neon' : 'obsidian';
      storeTheme(next);
      return next;
    });
  }, []);

  const cycleTheme = useCallback(() => {
    setActiveThemeId((prev) => {
      const idx = THEME_ORDER.indexOf(prev);
      const next = THEME_ORDER[(idx + 1) % THEME_ORDER.length];
      storeTheme(next);
      return next;
    });
  }, []);

  const value = useMemo<ThemeContextValue>(
    () => ({
      activeTheme: themes[activeThemeId],
      activeThemeId,
      themes,
      setTheme,
      toggleTheme,
      cycleTheme,
    }),
    [activeThemeId, setTheme, toggleTheme, cycleTheme]
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return ctx;
}

export { themes };
