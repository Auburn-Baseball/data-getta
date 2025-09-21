import * as React from 'react';
import { useNavigate, useSearchParams } from 'react-router';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { supabase } from '@/utils/supabase/client';
import { useAuth } from '@/utils/supabase/useauth';

import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';

const schema = z
  .object({
    password: z.string().min(6, 'Password must be at least 6 characters'),
    confirm: z.string().min(6, 'Confirm password must be at least 6 characters'),
  })
  .refine((v) => v.password === v.confirm, {
    path: ['confirm'],
    message: 'Passwords do not match',
  });

type Values = z.infer<typeof schema>;

export function ResetPasswordForm({ className }: { className?: string }) {
  const theme = useTheme();
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const { setUser, setRecovery } = useAuth();

  const [errorMessage, setErrorMessage] = React.useState('');
  const [info, setInfo] = React.useState<string>('');

  const cssVars = React.useMemo(
    () =>
      ({
        '--secondary-main': theme.palette.secondary.main,
        '--secondary-light': theme.palette.secondary.light,
      }) as React.CSSProperties,
    [theme.palette.secondary.main, theme.palette.secondary.light],
  );

  const inputClasses =
    'border-[var(--secondary-main)] focus-visible:ring-2 focus-visible:ring-[var(--secondary-main)]';
  const linkish = 'underline underline-offset-4 hover:cursor-pointer';
  const ctaBtn =
    '!cursor-pointer !border !border-[var(--secondary-main)] !bg-[var(--secondary-main)] hover:!bg-[var(--secondary-light)] !text-white';

  React.useEffect(() => {
    const code = search.get('code');
    if (!code) return;
    (async () => {
      const { error } = await supabase.auth.exchangeCodeForSession(code);
      if (error) {
        setErrorMessage(error.message);
      } else {
        setInfo('You can now set a new password.');
      }
    })();
  }, [search]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: Values) => {
    setErrorMessage('');
    setInfo('');
    const { error } = await supabase.auth.updateUser({ password: values.password });
    if (error) {
      setErrorMessage(error.message);
      return;
    }
    setInfo('Password updated! You can now sign in with your new password.');
    setRecovery(false);
  };

  return (
    <Box
      sx={{ borderWidth: '4px', borderColor: 'secondary.main', borderRadius: '16px' }}
      style={cssVars}
      className={className}
    >
      <Card>
        <CardHeader>
          <CardTitle>Reset your password</CardTitle>
          <CardDescription>Enter a new password for your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="flex flex-col gap-6">
              <div className="grid gap-3">
                <Label htmlFor="password">New password</Label>
                <Input
                  id="password"
                  type="password"
                  className={inputClasses}
                  {...register('password')}
                />
                {errors.password && (
                  <p className="text-sm font-medium text-destructive">
                    {String(errors.password.message)}
                  </p>
                )}
              </div>

              <div className="grid gap-3">
                <Label htmlFor="confirm">Confirm password</Label>
                <Input
                  id="confirm"
                  type="password"
                  className={inputClasses}
                  {...register('confirm')}
                />
                {errors.confirm && (
                  <p className="text-sm font-medium text-destructive">
                    {String(errors.confirm.message)}
                  </p>
                )}
              </div>

              {errorMessage && (
                <p className="text-sm font-medium text-destructive">{errorMessage}</p>
              )}
              {info && <p className="text-sm text-muted-foreground">{info}</p>}

              <div className="flex flex-col gap-3">
                <Button type="submit" className={`w-full ${ctaBtn}`} disabled={isSubmitting}>
                  {isSubmitting ? 'Working...' : 'Update password'}
                </Button>
              </div>

              <div className="mt-2 text-center text-sm">
                Remembered your password?{' '}
                <button
                  type="button"
                  className={`${linkish} hover:text-[var(--secondary-main)]`}
                  onClick={async () => {
                    await supabase.auth.signOut();
                    setRecovery(false);
                    setUser(null);
                    navigate('/', { replace: false });
                  }}
                >
                  Back to sign in
                </button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
