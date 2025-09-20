// components/ResetPasswordForm.tsx
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
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = React.useState('');
  const [info, setInfo] = React.useState<string>('');

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
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (values: Values) => {
    setErrorMessage('');
    setInfo('');
    const { error } = await supabase.auth.updateUser({ password: values.password });
    if (error) {
      setErrorMessage(error.message);
      return;
    }
    setInfo('Password updated. You can sign in with your new password.');
    setTimeout(() => navigate('/', { replace: true }), 1000);
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Reset your password</CardTitle>
        <CardDescription>Enter a new password for your account</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="flex flex-col gap-6">
            <div className="grid gap-3">
              <Label htmlFor="password">New password</Label>
              <Input id="password" type="password" {...register('password')} />
              {errors.password && (
                <p className="text-sm font-medium text-destructive">
                  {String(errors.password.message)}
                </p>
              )}
            </div>

            <div className="grid gap-3">
              <Label htmlFor="confirm">Confirm password</Label>
              <Input id="confirm" type="password" {...register('confirm')} />
              {errors.confirm && (
                <p className="text-sm font-medium text-destructive">
                  {String(errors.confirm.message)}
                </p>
              )}
            </div>

            {errorMessage && <p className="text-sm font-medium text-destructive">{errorMessage}</p>}
            {info && <p className="text-sm text-muted-foreground">{info}</p>}

            <div className="flex flex-col gap-3">
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? 'Working...' : 'Update password'}
              </Button>
            </div>

            <div className="mt-2 text-center text-sm">
              Remembered your password?{' '}
              <button
                type="button"
                className="underline underline-offset-4"
                onClick={() => navigate('/', { replace: true })}
              >
                Back to sign in
              </button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
