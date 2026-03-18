import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';
import { useTheme } from '../../theme';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, error, leftIcon, rightIcon, style, ...props }, ref) => {
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

    const inputWrapperStyle: React.CSSProperties = {
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
    };

    const inputStyle: React.CSSProperties = {
      width: '100%',
      padding: `${theme.spacing.space2} ${theme.spacing.space3}`,
      paddingLeft: leftIcon ? theme.spacing.space10 : theme.spacing.space3,
      paddingRight: rightIcon ? theme.spacing.space10 : theme.spacing.space3,
      fontFamily: theme.typography.fontBody,
      fontSize: theme.typography.sizeBase,
      color: theme.colors.text,
      backgroundColor: theme.colors.surface,
      border: `1px solid ${error ? theme.colors.error : theme.colors.border}`,
      borderRadius: theme.borderRadius.md,
      outline: 'none',
      transition: `all ${theme.motion.durationNormal} ${theme.motion.easeOut}`,
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

    const iconWrapperStyle: React.CSSProperties = {
      position: 'absolute',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: theme.colors.textMuted,
      pointerEvents: 'none',
    };

    return (
      <div style={containerStyle}>
        {label && <label style={labelStyle}>{label}</label>}
        <div style={inputWrapperStyle}>
          {leftIcon && (
            <span style={{ ...iconWrapperStyle, left: theme.spacing.space3 }}>
              {leftIcon}
            </span>
          )}
          <input ref={ref} style={inputStyle} {...props} />
          {rightIcon && (
            <span
              style={{ ...iconWrapperStyle, right: theme.spacing.space3 }}
            >
              {rightIcon}
            </span>
          )}
        </div>
        {hint && !error && <span style={hintStyle}>{hint}</span>}
        {error && <span style={errorStyle}>{error}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';
