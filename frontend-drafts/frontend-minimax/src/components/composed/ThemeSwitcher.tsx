import { type JSX } from 'react';
import { useTheme } from '../../theme';
import type { ThemeId } from '../../types/theme';
import { Button } from '../primitives';

interface ThemeSwitcherProps {
  compact?: boolean;
}

export function ThemeSwitcher({ compact = false }: ThemeSwitcherProps): JSX.Element {
  const { activeTheme, activeThemeId, themes, setTheme, cycleTheme } = useTheme();

  if (compact) {
    return (
      <Button variant="ghost" size="sm" onClick={cycleTheme}>
        {activeTheme.name}
      </Button>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        gap: activeTheme.spacing.space2,
        flexWrap: 'wrap',
      }}
    >
      {(Object.keys(themes) as ThemeId[]).map((id) => (
        <Button
          key={id}
          variant={activeThemeId === id ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => setTheme(id)}
        >
          {themes[id].name}
        </Button>
      ))}
    </div>
  );
}
