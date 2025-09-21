import * as React from 'react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router';
import { useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';

import { login, signup } from '@/utils/supabase/auth';
import { supabase } from '@/utils/supabase/client';
import { buildBaseUrl } from '@/utils/url';

type Mode = 'sign-in' | 'sign-up' | 'forgot';

const signInSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6).max(100),
});

const signUpSchema = signInSchema
  .extend({ confirmPassword: z.string().min(6).max(100) })
  .refine((d) => d.password === d.confirmPassword, {
    path: ['confirmPassword'],
    message: 'Passwords do not match',
  });

const forgotSchema = z.object({
  email: z.string().email(),
});

type SignInValues = z.infer<typeof signInSchema>;
type SignUpValues = z.infer<typeof signUpSchema>;
type ForgotValues = z.infer<typeof forgotSchema>;
type AuthValues = SignInValues | SignUpValues | ForgotValues;

export function LoginForm({ className, ...props }: React.ComponentProps<'div'>) {
  const theme = useTheme();

  const [mode, setMode] = useState<Mode>('sign-in');
  const [isLoading, setIsLoading] = useState(false);
  const [banner, setBanner] = useState<{ kind: 'info' | 'warn' | null; text: string }>({
    kind: null,
    text: '',
  });
  const [errorMessage, setErrorMessage] = useState('');
  const [forgotSent, setForgotSent] = useState<null | 'sent' | 'error'>(null);

  const navigate = useNavigate();

  const isSignIn = mode === 'sign-in';
  const isSignUp = mode === 'sign-up';
  const isForgot = mode === 'forgot';

  const title = isSignIn
    ? 'Login to your account'
    : isSignUp
      ? 'Create a new account'
      : 'Reset your password';

  const subtitle = isSignIn
    ? 'Enter your email below to login to your account'
    : isSignUp
      ? 'Enter your email and password to create your account'
      : 'Enter your email and we’ll send you a reset link';

  const submitText = isSignIn ? 'Login' : isSignUp ? 'Sign up' : 'Send reset link';

  const resolver = useMemo(() => {
    if (isSignIn) return zodResolver(signInSchema);
    if (isSignUp) return zodResolver(signUpSchema);
    return zodResolver(forgotSchema);
  }, [isSignIn, isSignUp]);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm({
    resolver,
    defaultValues: isSignIn
      ? ({ email: '', password: '' } as any)
      : isSignUp
        ? ({ email: '', password: '', confirmPassword: '' } as any)
        : ({ email: '' } as any),
  });

  const password = useWatch({ control, name: 'password' as const }) as string | undefined;
  const confirmPassword = useWatch({ control, name: 'confirmPassword' as any }) as
    | string
    | undefined;
  const mismatch = isSignUp && !!confirmPassword && password !== confirmPassword;

  async function sendReset(email: string) {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${buildBaseUrl()}reset-password`,
    });
    if (error) {
      setErrorMessage(error.message);
      setForgotSent(null);
      return;
    }
    setErrorMessage('');
    setForgotSent('sent');
    setBanner({
      kind: 'info',
      text: "If an account exists for that email, we've sent a password reset link.",
    });
  }

  const onSubmit = async (values: Record<string, any>) => {
    setIsLoading(true);
    setErrorMessage('');
    setBanner({ kind: null, text: '' });

    try {
      if (isSignIn) {
        const v = values as SignInValues;
        await login(v.email, v.password);
        navigate('/conferences');
        return;
      }

      if (isSignUp) {
        const v = values as SignUpValues;
        await signup(v.email, v.password);

        setBanner({
          kind: 'info',
          text: 'Check your email to confirm your account. If you don’t see it, check spam.',
        });
        return;
      }

      if (isForgot) {
        const v = values as ForgotValues;
        if (!v.email.trim()) {
          setForgotSent('error');
          return;
        }
        await sendReset(v.email);
      }
    } catch (e: any) {
      setErrorMessage(e?.message || 'Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const InlineBanner = ({
    kind,
    children,
  }: {
    kind: 'info' | 'warn';
    children: React.ReactNode;
  }) => (
    <p className={`text-sm ${kind === 'warn' ? 'text-destructive' : 'text-muted-foreground'}`}>
      {children}
    </p>
  );

  const switchMode = (next: Mode) => {
    setMode(next);
    setErrorMessage('');
    setBanner({ kind: null, text: '' });
    setForgotSent(null);
  };

  const cssVars = {
    '--secondary-main': theme.palette.secondary.main,
    '--secondary-light': theme.palette.secondary.light,
  } as React.CSSProperties;

  const inputClasses =
    'border-[var(--secondary-main)] focus-visible:ring-2 focus-visible:ring-[var(--secondary-main)]';
  const linkish = 'underline underline-offset-4 hover:cursor-pointer';
  const ctaBtn =
    '!cursor-pointer !border !border-[var(--secondary-main)] !bg-[var(--secondary-main)] hover:!bg-[var(--secondary-light)] !text-white';

  return (
    <Box
      sx={{
        borderWidth: '4px',
        borderColor: 'secondary.main',
        borderRadius: '16px',
      }}
      style={cssVars}
      className={cn('flex flex-col gap-6', className)}
      {...props}
    >
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{subtitle}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)}>
            {isSignIn && (
              <div className="flex flex-col gap-6">
                <div className="grid gap-3">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="m@example.com"
                    required
                    className={inputClasses}
                    {...register('email', {
                      onChange: () => errorMessage && setErrorMessage(''),
                    })}
                  />
                  {errors.email && (
                    <p className="text-sm font-medium text-destructive">
                      {String(errors.email.message)}
                    </p>
                  )}
                </div>

                <div className="grid gap-3">
                  <div className="flex items-center">
                    <Label htmlFor="password">Password</Label>
                    <button
                      type="button"
                      className={`ml-auto inline-block text-sm ${linkish} hover:text-[var(--secondary-main)]`}
                      onClick={() => switchMode('forgot')}
                    >
                      Forgot your password?
                    </button>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    required
                    className={inputClasses}
                    {...register('password', {
                      onChange: () => errorMessage && setErrorMessage(''),
                    })}
                  />
                  {errors.password && (
                    <p className="text-sm font-medium text-destructive">
                      {String(errors.password.message)}
                    </p>
                  )}
                  {errorMessage && (
                    <p className="text-sm font-medium text-destructive">{errorMessage}</p>
                  )}

                  {banner.kind && <InlineBanner kind={banner.kind}>{banner.text}</InlineBanner>}
                </div>

                <div className="flex flex-col gap-3">
                  <Button type="submit" className={`w-full ${ctaBtn}`} disabled={isLoading}>
                    {isLoading ? 'Working...' : submitText}
                  </Button>
                </div>

                <div className="mt-2 text-center text-sm">
                  Don&apos;t have an account?{' '}
                  <button
                    type="button"
                    className={`${linkish} hover:text-[var(--secondary-main)]`}
                    onClick={() => switchMode('sign-up')}
                  >
                    Sign up
                  </button>
                </div>
              </div>
            )}

            {isSignUp && (
              <div className="flex flex-col gap-6">
                <div className="grid gap-3">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="m@example.com"
                    required
                    className={inputClasses}
                    {...register('email', {
                      onChange: () => errorMessage && setErrorMessage(''),
                    })}
                  />
                  {errors.email && (
                    <p className="text-sm font-medium text-destructive">
                      {String(errors.email.message)}
                    </p>
                  )}
                </div>

                <div className="grid gap-3">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    required
                    className={inputClasses}
                    {...register('password', {
                      onChange: () => errorMessage && setErrorMessage(''),
                    })}
                  />
                  {errors.password && (
                    <p className="text-sm font-medium text-destructive">
                      {String(errors.password.message)}
                    </p>
                  )}
                </div>

                <div className="grid gap-3">
                  <Label htmlFor="confirmPassword">Confirm password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    required
                    className={inputClasses}
                    {...register('confirmPassword' as any, {
                      onChange: () => errorMessage && setErrorMessage(''),
                    })}
                  />
                  {(errors as any).confirmPassword && (
                    <p className="text-sm font-medium text-destructive">
                      {String((errors as any).confirmPassword?.message)}
                    </p>
                  )}
                  {!(errors as any).confirmPassword && mismatch && (
                    <p className="text-sm font-medium text-destructive">Passwords do not match!</p>
                  )}

                  {errorMessage && (
                    <p className="text-sm font-medium text-destructive">{errorMessage}</p>
                  )}

                  {banner.kind && (
                    <>
                      <InlineBanner kind={banner.kind}>{banner.text}</InlineBanner>
                      {banner.kind === 'warn' && (
                        <div className="mt-1 flex gap-3 text-sm">
                          <button
                            type="button"
                            className={`text-[var(--secondary-main)] ${linkish.replace('underline underline-offset-4 ', '')}`}
                            onClick={() => switchMode('sign-in')}
                          >
                            Sign in
                          </button>
                          <button
                            type="button"
                            className={`text-[var(--secondary-main)] ${linkish.replace('underline underline-offset-4 ', '')}`}
                            onClick={() => {
                              const email = (control._formValues as any)?.email as string;
                              if (email) void sendReset(email);
                            }}
                          >
                            Reset password
                          </button>
                        </div>
                      )}
                    </>
                  )}
                </div>

                <div className="flex flex-col gap-3">
                  <Button
                    type="submit"
                    className={`w-full ${ctaBtn}`}
                    disabled={isLoading || mismatch}
                  >
                    {isLoading ? 'Working...' : submitText}
                  </Button>
                </div>

                <div className="mt-2 text-center text-sm">
                  Already have an account?{' '}
                  <button
                    type="button"
                    className={`${linkish} hover:text-[var(--secondary-main)]`}
                    onClick={() => switchMode('sign-in')}
                  >
                    Back to sign in
                  </button>
                </div>
              </div>
            )}

            {isForgot && (
              <div className="flex flex-col gap-6">
                <div className="grid gap-3">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="m@example.com"
                    className={inputClasses}
                    {...register('email', {
                      onChange: () => {
                        if (forgotSent) setForgotSent(null);
                        if (errorMessage) setErrorMessage('');
                      },
                    })}
                    required
                  />
                  {errors.email && (
                    <p className="text-sm font-medium text-destructive">
                      {String(errors.email.message)}
                    </p>
                  )}
                  {errorMessage && (
                    <p className="text-sm font-medium text-destructive">{errorMessage}</p>
                  )}
                  {forgotSent === 'sent' && (
                    <p className="text-sm text-muted-foreground">
                      If an account exists for that email, we’ve sent a password reset link.
                    </p>
                  )}
                  {forgotSent === 'error' && (
                    <p className="text-sm text-destructive">Please enter a valid email.</p>
                  )}
                </div>

                <div className="flex flex-col gap-3">
                  <Button type="submit" className={`w-full ${ctaBtn}`} disabled={isLoading}>
                    {isLoading ? 'Working...' : submitText}
                  </Button>
                </div>

                <div className="mt-2 text-center text-sm">
                  Remembered your password?{' '}
                  <button
                    type="button"
                    className={`${linkish} hover:text-[var(--secondary-main)]`}
                    onClick={() => switchMode('sign-in')}
                  >
                    Back to sign in
                  </button>
                </div>
              </div>
            )}
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
