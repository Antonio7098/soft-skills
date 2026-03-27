import { Palette } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';
import { THEMES, THEME_NAMES, type ThemeName } from '@/design-system/tokens/themes';
import { cn } from '@/lib/cn';

interface ThemeSwitcherProps {
  readonly collapsed?: boolean;
}

export function ThemeSwitcher({ collapsed = false }: ThemeSwitcherProps) {
  const { theme, setTheme } = useTheme();

  if (collapsed) {
    return (
      <button
        onClick={() => {
          const idx = THEME_NAMES.indexOf(theme);
          const next = THEME_NAMES[(idx + 1) % THEME_NAMES.length]!;
          setTheme(next);
        }}
        className={cn(
          'flex items-center justify-center p-2.5 rounded-button',
          'text-sidebar-text-muted hover:text-sidebar-text hover:bg-sidebar-item-hover',
          'transition-all duration-150',
        )}
        aria-label="Cycle theme"
      >
        <Palette className="w-5 h-5" />
      </button>
    );
  }

  return (
    <div className="flex flex-col gap-2 px-1">
      <div className="flex items-center gap-2 px-2 mb-1">
        <Palette className="w-4 h-4 text-sidebar-text-muted" />
        <span className="text-body-xs font-medium text-sidebar-text-muted uppercase tracking-wider">
          Theme
        </span>
      </div>
      <div className="flex flex-col gap-1">
        {THEME_NAMES.map((name: ThemeName) => {
          const meta = THEMES[name];
          return (
            <button
              key={name}
              onClick={() => setTheme(name)}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-button transition-all duration-150',
                'text-sidebar-text-muted hover:text-sidebar-text hover:bg-sidebar-item-hover',
                theme === name && 'bg-sidebar-item-active text-sidebar-text',
              )}
            >
              <span
                className="w-3.5 h-3.5 rounded-full ring-1 ring-sidebar-text-muted/30 shrink-0"
                style={{ backgroundColor: meta.swatch }}
              />
              <span className="text-body-sm">{meta.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
