import {
  createContext,
  useContext,
} from "react";
import type { ThemeContextValue } from "@/types/theme";

const ThemeContext = createContext<ThemeContextValue | null>(null);

export const ThemeContextProvider = ThemeContext.Provider;

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}

export { ThemeContext };
