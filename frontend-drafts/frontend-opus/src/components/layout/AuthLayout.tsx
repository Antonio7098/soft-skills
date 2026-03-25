import type { ReactNode } from 'react';

interface AuthLayoutProps {
  readonly children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen w-full bg-surface-primary items-center justify-center p-6">
      <div className="noise-overlay" />
      <div className="w-full max-w-md relative z-0">
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <div className="w-10 h-10 rounded-lg bg-accent flex items-center justify-center">
            <span className="font-display text-body-lg text-surface-primary font-bold">S</span>
          </div>
          <span className="font-display text-display-md text-content-primary">SoftSkills</span>
        </div>
        {children}
      </div>
    </div>
  );
}
