import type { ThemeTokens } from "@/types/theme";

export function tokensToCssVars(theme: ThemeTokens): string {
  const vars: string[] = [];

  // Colors - bg
  vars.push(`--color-bg-primary: ${theme.colors.bg.primary};`);
  vars.push(`--color-bg-secondary: ${theme.colors.bg.secondary};`);
  vars.push(`--color-bg-tertiary: ${theme.colors.bg.tertiary};`);
  vars.push(`--color-bg-elevated: ${theme.colors.bg.elevated};`);
  vars.push(`--color-bg-overlay: ${theme.colors.bg.overlay};`);

  // Colors - text
  vars.push(`--color-text-primary: ${theme.colors.text.primary};`);
  vars.push(`--color-text-secondary: ${theme.colors.text.secondary};`);
  vars.push(`--color-text-tertiary: ${theme.colors.text.tertiary};`);
  vars.push(`--color-text-inverse: ${theme.colors.text.inverse};`);

  // Colors - accent
  vars.push(`--color-accent-primary: ${theme.colors.accent.primary};`);
  vars.push(`--color-accent-secondary: ${theme.colors.accent.secondary};`);
  vars.push(`--color-accent-muted: ${theme.colors.accent.muted};`);

  // Colors - border
  vars.push(`--color-border-default: ${theme.colors.border.default};`);
  vars.push(`--color-border-subtle: ${theme.colors.border.subtle};`);
  vars.push(`--color-border-strong: ${theme.colors.border.strong};`);

  // Colors - status
  vars.push(`--color-status-success: ${theme.colors.status.success};`);
  vars.push(`--color-status-warning: ${theme.colors.status.warning};`);
  vars.push(`--color-status-error: ${theme.colors.status.error};`);
  vars.push(`--color-status-info: ${theme.colors.status.info};`);

  // Colors - surface
  vars.push(`--color-surface-hover: ${theme.colors.surface.hover};`);
  vars.push(`--color-surface-active: ${theme.colors.surface.active};`);
  vars.push(`--color-surface-selected: ${theme.colors.surface.selected};`);

  // Typography
  vars.push(`--font-display: ${theme.typography.fontFamily.display};`);
  vars.push(`--font-body: ${theme.typography.fontFamily.body};`);
  vars.push(`--font-mono: ${theme.typography.fontFamily.mono};`);

  vars.push(`--font-size-xs: ${theme.typography.fontSize.xs};`);
  vars.push(`--font-size-sm: ${theme.typography.fontSize.sm};`);
  vars.push(`--font-size-base: ${theme.typography.fontSize.base};`);
  vars.push(`--font-size-lg: ${theme.typography.fontSize.lg};`);
  vars.push(`--font-size-xl: ${theme.typography.fontSize.xl};`);
  vars.push(`--font-size-2xl: ${theme.typography.fontSize["2xl"]};`);
  vars.push(`--font-size-3xl: ${theme.typography.fontSize["3xl"]};`);
  vars.push(`--font-size-4xl: ${theme.typography.fontSize["4xl"]};`);
  vars.push(`--font-size-5xl: ${theme.typography.fontSize["5xl"]};`);
  vars.push(`--font-size-6xl: ${theme.typography.fontSize["6xl"]};`);

  vars.push(`--font-weight-regular: ${theme.typography.fontWeight.regular};`);
  vars.push(`--font-weight-medium: ${theme.typography.fontWeight.medium};`);
  vars.push(`--font-weight-semibold: ${theme.typography.fontWeight.semibold};`);
  vars.push(`--font-weight-bold: ${theme.typography.fontWeight.bold};`);

  vars.push(`--line-height-tight: ${theme.typography.lineHeight.tight};`);
  vars.push(`--line-height-normal: ${theme.typography.lineHeight.normal};`);
  vars.push(`--line-height-relaxed: ${theme.typography.lineHeight.relaxed};`);

  vars.push(`--letter-spacing-tight: ${theme.typography.letterSpacing.tight};`);
  vars.push(
    `--letter-spacing-normal: ${theme.typography.letterSpacing.normal};`
  );
  vars.push(`--letter-spacing-wide: ${theme.typography.letterSpacing.wide};`);
  vars.push(`--letter-spacing-wider: ${theme.typography.letterSpacing.wider};`);

  // Spacing
  Object.entries(theme.spacing).forEach(([key, value]) => {
    vars.push(`--spacing-${key}: ${value};`);
  });

  // Radius
  Object.entries(theme.radius).forEach(([key, value]) => {
    vars.push(`--radius-${key}: ${value};`);
  });

  // Shadow
  Object.entries(theme.shadow).forEach(([key, value]) => {
    vars.push(`--shadow-${key}: ${value};`);
  });

  // Transition
  vars.push(`--transition-fast: ${theme.transition.fast};`);
  vars.push(`--transition-normal: ${theme.transition.normal};`);
  vars.push(`--transition-slow: ${theme.transition.slow};`);

  return vars.join("\n  ");
}

export function applyThemeToDocument(theme: ThemeTokens): void {
  const root = document.documentElement;
  root.setAttribute("data-theme", theme.mode);

  // Colors
  root.style.setProperty("--color-bg-primary", theme.colors.bg.primary);
  root.style.setProperty("--color-bg-secondary", theme.colors.bg.secondary);
  root.style.setProperty("--color-bg-tertiary", theme.colors.bg.tertiary);
  root.style.setProperty("--color-bg-elevated", theme.colors.bg.elevated);
  root.style.setProperty("--color-bg-overlay", theme.colors.bg.overlay);

  root.style.setProperty("--color-text-primary", theme.colors.text.primary);
  root.style.setProperty("--color-text-secondary", theme.colors.text.secondary);
  root.style.setProperty("--color-text-tertiary", theme.colors.text.tertiary);
  root.style.setProperty("--color-text-inverse", theme.colors.text.inverse);

  root.style.setProperty(
    "--color-accent-primary",
    theme.colors.accent.primary
  );
  root.style.setProperty(
    "--color-accent-secondary",
    theme.colors.accent.secondary
  );
  root.style.setProperty("--color-accent-muted", theme.colors.accent.muted);

  root.style.setProperty(
    "--color-border-default",
    theme.colors.border.default
  );
  root.style.setProperty(
    "--color-border-subtle",
    theme.colors.border.subtle
  );
  root.style.setProperty(
    "--color-border-strong",
    theme.colors.border.strong
  );

  root.style.setProperty(
    "--color-status-success",
    theme.colors.status.success
  );
  root.style.setProperty(
    "--color-status-warning",
    theme.colors.status.warning
  );
  root.style.setProperty("--color-status-error", theme.colors.status.error);
  root.style.setProperty("--color-status-info", theme.colors.status.info);

  root.style.setProperty("--color-surface-hover", theme.colors.surface.hover);
  root.style.setProperty(
    "--color-surface-active",
    theme.colors.surface.active
  );
  root.style.setProperty(
    "--color-surface-selected",
    theme.colors.surface.selected
  );

  // Typography
  root.style.setProperty("--font-display", theme.typography.fontFamily.display);
  root.style.setProperty("--font-body", theme.typography.fontFamily.body);
  root.style.setProperty("--font-mono", theme.typography.fontFamily.mono);

  root.style.setProperty("--font-size-xs", theme.typography.fontSize.xs);
  root.style.setProperty("--font-size-sm", theme.typography.fontSize.sm);
  root.style.setProperty("--font-size-base", theme.typography.fontSize.base);
  root.style.setProperty("--font-size-lg", theme.typography.fontSize.lg);
  root.style.setProperty("--font-size-xl", theme.typography.fontSize.xl);
  root.style.setProperty("--font-size-2xl", theme.typography.fontSize["2xl"]);
  root.style.setProperty("--font-size-3xl", theme.typography.fontSize["3xl"]);
  root.style.setProperty("--font-size-4xl", theme.typography.fontSize["4xl"]);
  root.style.setProperty("--font-size-5xl", theme.typography.fontSize["5xl"]);
  root.style.setProperty("--font-size-6xl", theme.typography.fontSize["6xl"]);

  root.style.setProperty(
    "--font-weight-regular",
    String(theme.typography.fontWeight.regular)
  );
  root.style.setProperty(
    "--font-weight-medium",
    String(theme.typography.fontWeight.medium)
  );
  root.style.setProperty(
    "--font-weight-semibold",
    String(theme.typography.fontWeight.semibold)
  );
  root.style.setProperty(
    "--font-weight-bold",
    String(theme.typography.fontWeight.bold)
  );

  root.style.setProperty(
    "--line-height-tight",
    theme.typography.lineHeight.tight
  );
  root.style.setProperty(
    "--line-height-normal",
    theme.typography.lineHeight.normal
  );
  root.style.setProperty(
    "--line-height-relaxed",
    theme.typography.lineHeight.relaxed
  );

  root.style.setProperty(
    "--letter-spacing-tight",
    theme.typography.letterSpacing.tight
  );
  root.style.setProperty(
    "--letter-spacing-normal",
    theme.typography.letterSpacing.normal
  );
  root.style.setProperty(
    "--letter-spacing-wide",
    theme.typography.letterSpacing.wide
  );
  root.style.setProperty(
    "--letter-spacing-wider",
    theme.typography.letterSpacing.wider
  );

  // Spacing
  Object.entries(theme.spacing).forEach(([key, value]) => {
    root.style.setProperty(`--spacing-${key}`, value as string);
  });

  // Radius
  Object.entries(theme.radius).forEach(([key, value]) => {
    root.style.setProperty(`--radius-${key}`, value as string);
  });

  // Shadow
  Object.entries(theme.shadow).forEach(([key, value]) => {
    root.style.setProperty(`--shadow-${key}`, value as string);
  });

  // Transition
  root.style.setProperty("--transition-fast", theme.transition.fast);
  root.style.setProperty("--transition-normal", theme.transition.normal);
  root.style.setProperty("--transition-slow", theme.transition.slow);
}
