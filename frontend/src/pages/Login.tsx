import { useState } from 'react';
import { Mail, Lock, User, ArrowRight, Loader2, Sparkles } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Input } from '@/design-system/primitives/Input';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { useData, getDataMode } from '@/data';

interface LoginFormData {
  email: string;
  password: string;
}

interface RegisterFormData {
  email: string;
  displayName: string;
  password: string;
  confirmPassword: string;
}

type AuthMode = 'login' | 'register';

export function Login() {
  const [mode, setMode] = useState<AuthMode>('login');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loginData, setLoginData] = useState<LoginFormData>({ email: '', password: '' });
  const [registerData, setRegisterData] = useState<RegisterFormData>({
    email: '',
    displayName: '',
    password: '',
    confirmPassword: '',
  });

  const data = useData();

  const isMock = getDataMode() === 'mock';
  const isAuto = getDataMode() === 'auto';

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!isMock) {
      setError('Email login is only available in demo mode. Use the demo accounts below.');
      return;
    }

    setIsLoading(true);

    try {
      const user = await data.register({
        email: loginData.email,
        display_name: loginData.email.split('@')[0] || 'User',
        role: 'standard_user',
      });
      
      if (user) {
        window.location.href = '/';
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!isMock) {
      setError('Registration is only available in demo mode. Use the demo accounts below.');
      return;
    }

    if (registerData.password !== registerData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (registerData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);

    try {
      const user = await data.register({
        email: registerData.email,
        display_name: registerData.displayName,
        role: 'standard_user',
      });

      if (user) {
        window.location.href = '/';
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const switchToLogin = () => {
    setMode('login');
    setError(null);
  };

  const switchToRegister = () => {
    setMode('register');
    setError(null);
  };

  return (
    <AuthLayout>
      <div className="animate-fade-in">
        <div className="text-center mb-8">
          <h1 className="font-display text-display-md text-content-primary mb-2">
            {mode === 'login' ? 'Welcome back' : 'Create account'}
          </h1>
          <p className="text-body-md text-content-secondary">
            {mode === 'login'
              ? 'Sign in to continue your soft skills journey'
              : 'Start practicing your communication skills today'}
          </p>
        </div>

        <Card variant="elevated" padding="lg" className="border border-line">
          {mode === 'login' ? (
            <form onSubmit={handleLogin} className="flex flex-col gap-5">
              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                value={loginData.email}
                onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                icon={<Mail className="w-4 h-4" />}
                required
              />
              <Input
                label="Password"
                type="password"
                placeholder="Enter your password"
                value={loginData.password}
                onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                icon={<Lock className="w-4 h-4" />}
                required
              />
              {error && (
                <p className="text-body-sm text-status-error bg-status-error/10 px-3 py-2 rounded-input">
                  {error}
                </p>
              )}
              <Button type="submit" size="lg" className="w-full mt-2" disabled={isLoading}>
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Sign in
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="flex flex-col gap-5">
              <Input
                label="Display name"
                type="text"
                placeholder="How should we call you?"
                value={registerData.displayName}
                onChange={(e) => setRegisterData({ ...registerData, displayName: e.target.value })}
                icon={<User className="w-4 h-4" />}
                required
              />
              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                value={registerData.email}
                onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                icon={<Mail className="w-4 h-4" />}
                required
              />
              <Input
                label="Password"
                type="password"
                placeholder="Create a password"
                value={registerData.password}
                onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                icon={<Lock className="w-4 h-4" />}
                required
              />
              <Input
                label="Confirm password"
                type="password"
                placeholder="Confirm your password"
                value={registerData.confirmPassword}
                onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
                icon={<Lock className="w-4 h-4" />}
                required
              />
              {error && (
                <p className="text-body-sm text-status-error bg-status-error/10 px-3 py-2 rounded-input">
                  {error}
                </p>
              )}
              <Button type="submit" size="lg" className="w-full mt-2" disabled={isLoading}>
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Create account
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </form>
          )}
        </Card>

        <div className="mt-6 text-center">
          <p className="text-body-sm text-content-secondary">
            {mode === 'login' ? (
              <>
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={switchToRegister}
                  className="text-accent hover:text-accent-hover font-medium transition-colors"
                >
                  Sign up
                </button>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={switchToLogin}
                  className="text-accent hover:text-accent-hover font-medium transition-colors"
                >
                  Sign in
                </button>
              </>
            )}
          </p>
        </div>

        <div className="mt-8 pt-6 border-t border-line">
          <p className="text-body-xs text-content-tertiary text-center mb-4">
            Development mode: Quick access
          </p>
          <div className="flex flex-col gap-2">
            <DevProfileButton profileId="learner-alex" label="Learner (Demo)" />
            <DevProfileButton profileId="org-admin-alex" label="Org Admin (Demo)" />
            <DevProfileButton profileId="superadmin-henry" label="Super Admin (Demo)" />
          </div>
        </div>
      </div>
    </AuthLayout>
  );
}

function DevProfileButton({ profileId, label }: { profileId: string; label: string }) {
  const [isLoading, setIsLoading] = useState(false);
  const data = useData();

  const handleClick = async () => {
    setIsLoading(true);
    try {
      await data.switchAuthProfile(profileId);
      window.location.href = '/';
    } catch (err) {
      console.error('Failed to switch profile:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      className="w-full justify-start gap-2 text-content-secondary hover:text-content-primary"
      onClick={handleClick}
      disabled={isLoading}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Sparkles className="w-4 h-4 text-accent" />
      )}
      {label}
    </Button>
  );
}