import { forwardRef, type TextareaHTMLAttributes } from 'react';
import { useTheme } from '../../theme';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, hint, error, style, ...props }, ref) => {
    const { activeTheme: theme } = useTheme();

    const containerStyle: React.CSSProperties = {
      display: 'flex',
      flexDirection: 'column',
      gap: theme.spacing.space1,
      width: '100%',
    };

    const labelStyle: React.CSSProperties = {
      fontFamily: theme.typography.fontBody,
      fontSize: theme.typography.sizeSm,
      fontWeight: theme.typography.weightMedium,
      color: theme.colors.text,
      letterSpacing: theme.typography.letterSpacingWide,
      textTransform: 'uppercase',
    };

    const textareaStyle: React.CSSProperties = {
      width: '100%',
      minHeight: '8rem',
      padding: theme.spacing.space3,
      fontFamily: theme.typography.fontBody,
      fontSize: theme.typography.sizeBase,
      color: theme.colors.text,
      backgroundColor: theme.colors.surface,
      border: `1px solid ${error ? theme.colors.error : theme.colors.border}`,
      borderRadius: theme.borderRadius.md,
      outline: 'none',
      resize: 'vertical',
      transition: `all ${theme.motion.durationNormal} ${theme.motion.easeOut}`,
      lineHeight: theme.typography.lineHeightRelaxed,
      ...style,
    };

    const hintStyle: React.CSSProperties = {
      fontFamily: theme.typography.fontBody,
      fontSize: theme.typography.sizeXs,
      color: theme.colors.textMuted,
    };

    const errorStyle: React.CSSProperties = {
      fontFamily: theme.typography.fontBody,
      fontSize: theme.typography.sizeXs,
      color: theme.colors.error,
    };

    return (
      <div style={containerStyle}>
        {label && <label style={labelStyle}>{label}</label>}
        <textarea ref={ref} style={textareaStyle} {...props} />
        {hint && !error && <span style={hintStyle}>{hint}</span>}
        {error && <span style={errorStyle}>{error}</span>}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
