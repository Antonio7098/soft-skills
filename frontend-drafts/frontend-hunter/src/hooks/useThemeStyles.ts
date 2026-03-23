import { useTheme } from "@/theme";
import type { CSSProperties } from "react";

export function useThemeStyles() {
  const { theme } = useTheme();

  return {
    theme,
    tokens: theme,
    colors: theme.colors,
    typography: theme.typography,
    spacing: theme.spacing,
    radius: theme.radius,
    shadow: theme.shadow,
    transition: theme.transition,
  };
}

export function useTokenStyle(
  buildStyle: (theme: ReturnType<typeof useTheme>["theme"]) => CSSProperties
): CSSProperties {
  const { theme } = useTheme();
  return buildStyle(theme);
}
