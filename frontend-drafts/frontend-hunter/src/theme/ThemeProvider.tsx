import { useEffect, useState, useCallback, type ReactNode } from "react";
import type { ThemeMode, ThemeTokens } from "@/types/theme";
import { themes } from "./themes";
import { applyThemeToDocument } from "./css";
import { ThemeContextProvider } from "./ThemeContext";

const STORAGE_KEY = "softskills-theme";

function getInitialMode(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "dark" || stored === "light") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function getTheme(mode: ThemeMode): ThemeTokens {
  return themes[mode];
}

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [mode, setModeState] = useState<ThemeMode>(getInitialMode);
  const theme = getTheme(mode);

  useEffect(() => {
    applyThemeToDocument(theme);
  }, [theme]);

  const setMode = useCallback((newMode: ThemeMode) => {
    setModeState(newMode);
    localStorage.setItem(STORAGE_KEY, newMode);
  }, []);

  const toggleTheme = useCallback(() => {
    setMode(mode === "dark" ? "light" : "dark");
  }, [mode, setMode]);

  return (
    <ThemeContextProvider
      value={{
        theme,
        mode,
        toggleTheme,
        setMode,
      }}
    >
      {children}
    </ThemeContextProvider>
  );
}
