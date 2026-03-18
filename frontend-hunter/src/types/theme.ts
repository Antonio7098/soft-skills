export type ThemeMode = "dark" | "light";

export interface ThemeTokens {
  mode: ThemeMode;
  colors: {
    bg: {
      primary: string;
      secondary: string;
      tertiary: string;
      elevated: string;
      overlay: string;
    };
    text: {
      primary: string;
      secondary: string;
      tertiary: string;
      inverse: string;
    };
    accent: {
      primary: string;
      secondary: string;
      muted: string;
    };
    border: {
      default: string;
      subtle: string;
      strong: string;
    };
    status: {
      success: string;
      warning: string;
      error: string;
      info: string;
    };
    surface: {
      hover: string;
      active: string;
      selected: string;
    };
  };
  typography: {
    fontFamily: {
      display: string;
      body: string;
      mono: string;
    };
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      "2xl": string;
      "3xl": string;
      "4xl": string;
      "5xl": string;
      "6xl": string;
    };
    fontWeight: {
      regular: number;
      medium: number;
      semibold: number;
      bold: number;
    };
    lineHeight: {
      tight: string;
      normal: string;
      relaxed: string;
    };
    letterSpacing: {
      tight: string;
      normal: string;
      wide: string;
      wider: string;
    };
  };
  spacing: {
    "0": string;
    "1": string;
    "2": string;
    "3": string;
    "4": string;
    "5": string;
    "6": string;
    "8": string;
    "10": string;
    "12": string;
    "16": string;
    "20": string;
    "24": string;
    "32": string;
  };
  radius: {
    none: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    full: string;
  };
  shadow: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  transition: {
    fast: string;
    normal: string;
    slow: string;
  };
}

export interface ThemeContextValue {
  theme: ThemeTokens;
  mode: ThemeMode;
  toggleTheme: () => void;
  setMode: (mode: ThemeMode) => void;
}
