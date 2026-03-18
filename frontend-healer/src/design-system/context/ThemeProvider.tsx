import { useState, useCallback, useMemo, useEffect, type ReactNode } from 'react';
import { ThemeContext, type ThemeContextValue } from './ThemeContext';
import { themes } from '../themes';
import type { ThemeId } from '../themes/types';

const STORAGE_KEY = 'softskills-theme';
const AVAILABLE_THEMES: ThemeId[] = ['concrete', 'obsidian'];

interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: ThemeId;
}

/**
 * Persists theme selection to localStorage.
 */
function getStoredTheme(): ThemeId | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && AVAILABLE_THEMES.includes(stored as ThemeId)) {
      return stored as ThemeId;
    }
  } catch {
    // localStorage unavailable
  }
  return null;
}

function storeTheme(id: ThemeId): void {
  try {
    localStorage.setItem(STORAGE_KEY, id);
  } catch {
    // localStorage unavailable
  }
}

/**
 * Applies theme tokens as CSS custom properties on the document root.
 */
function applyThemeToDocument(themeId: ThemeId): void {
  const theme = themes[themeId];
  const root = document.documentElement;

  root.setAttribute('data-theme', themeId);

  // Apply color tokens
  const colorEntries = Object.entries(theme.colors) as Array<[string, string]>;
  colorEntries.forEach(([key, value]) => {
    const cssVarName = `--color-${camelToKebab(key)}`;
    root.style.setProperty(cssVarName, value);
  });

  // Apply typography
  root.style.setProperty('--font-display', theme.typography.fontFamilyDisplay);
  root.style.setProperty('--font-body', theme.typography.fontFamilyBody);
  root.style.setProperty('--font-mono', theme.typography.fontFamilyMono);

  // Apply spacing
  const spacingEntries = Object.entries(theme.spacing) as Array<[string, string]>;
  spacingEntries.forEach(([key, value]) => {
    const cssVarName = `--${camelToKebab(key)}`;
    root.style.setProperty(cssVarName, value);
  });

  // Apply radius
  const radiusEntries = Object.entries(theme.radius) as Array<[string, string]>;
  radiusEntries.forEach(([key, value]) => {
    const cssVarName = `--${camelToKebab(key)}`;
    root.style.setProperty(cssVarName, value);
  });

  // Apply motion
  root.style.setProperty('--duration-instant', theme.motion.durationInstant);
  root.style.setProperty('--duration-fast', theme.motion.durationFast);
  root.style.setProperty('--duration-normal', theme.motion.durationNormal);
  root.style.setProperty('--duration-slow', theme.motion.durationSlow);
  root.style.setProperty('--duration-slower', theme.motion.durationSlower);
  root.style.setProperty('--easing-default', theme.motion.easingDefault);
  root.style.setProperty('--easing-out', theme.motion.easingOut);
  root.style.setProperty('--easing-bounce', theme.motion.easingBounce);

  // Apply shadows
  const shadowEntries = Object.entries(theme.shadows) as Array<[string, string]>;
  shadowEntries.forEach(([key, value]) => {
    const cssVarName = `--${camelToKebab(key)}`;
    root.style.setProperty(cssVarName, value);
  });
}

function camelToKebab(str: string): string {
  return str.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase();
}

/**
 * ThemeProvider - manages theme state and applies CSS custom properties.
 *
 * Supports:
 * - Theme persistence via localStorage
 * - Theme toggle between available themes
 * - CSS custom property injection for all tokens
 */
export function ThemeProvider({ children, defaultTheme = 'concrete' }: ThemeProviderProps) {
  const [themeId, setThemeId] = useState<ThemeId>(() => getStoredTheme() || defaultTheme);

  const setTheme = useCallback((id: ThemeId) => {
    if (AVAILABLE_THEMES.includes(id)) {
      setThemeId(id);
      storeTheme(id);
    }
  }, []);

  const toggleTheme = useCallback(() => {
    const currentIndex = AVAILABLE_THEMES.indexOf(themeId);
    const nextIndex = (currentIndex + 1) % AVAILABLE_THEMES.length;
    const nextTheme = AVAILABLE_THEMES[nextIndex];
    setTheme(nextTheme);
  }, [themeId, setTheme]);

  const value = useMemo<ThemeContextValue>(() => ({
    theme: themes[themeId],
    themeId,
    setTheme,
    toggleTheme,
    availableThemes: AVAILABLE_THEMES,
  }), [themeId, setTheme, toggleTheme]);

  // Apply theme to document whenever themeId changes
  useEffect(() => {
    applyThemeToDocument(themeId);
  }, [themeId]);

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}
