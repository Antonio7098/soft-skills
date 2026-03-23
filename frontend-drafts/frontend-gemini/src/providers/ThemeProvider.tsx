import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'professional' | 'brutalist' | 'neo-corporate';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    // Check local storage or default to professional
    const saved = localStorage.getItem('theme') as Theme;
    return saved || 'professional';
  });

  useEffect(() => {
    // Update local storage
    localStorage.setItem('theme', theme);
    // Update document data attribute for CSS variables
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
