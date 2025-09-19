import { useMemo, useState } from 'react';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm, useWatch } from 'react-hook-form';
import { useNavigate } from 'react-router';
import { login, signup } from '@/utils/supabase/auth';
import { supabase } from '@/utils/supabase/client';
import IconButton from '@mui/material/IconButton';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

type FormType = 'sign-in' | 'sign-up';

const signInSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6).max(100),
});

const signUpSchema = signInSchema
  .extend({ confirmPassword: z.string().min(6).max(100) })
  .refine((data) => data.password === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'Passwords do not match',
  });

type SignInValues = z.infer<typeof signInSchema>;
type SignUpValues = z.infer<typeof signUpSchema>;
type AuthValues = SignInValues | SignUpValues;

export default function AuthForm({ initialType = 'sign-in' }: { initialType?: FormType }) {
  const [mode, setMode] = useState<FormType>(initialType);
  const [showPw, setShowPw] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const [banner, setBanner] = useState<{ kind: 'info' | 'warn' | null; text: string }>({
    kind: null,
    text: '',
  });
  const [errorMessage, setErrorMessage] = useState('');

  const navigate = useNavigate();
  const title = useMemo(() => (mode === 'sign-in' ? 'Sign In' : 'Sign Up'), [mode]);
  const resolver = useMemo(
    () => zodResolver(mode === 'sign-in' ? signInSchema : signUpSchema),
    [mode],
  );

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<AuthValues>({
    resolver,
    defaultValues:
      mode === 'sign-in'
        ? ({ email: '', password: '' } as any)
        : ({ email: '', password: '', confirmPassword: '' } as any),
  });

  const password = useWatch({ control, name: 'password' as const });
  const confirmPassword = useWatch({ control, name: 'confirmPassword' as any });
  const mismatch = mode === 'sign-up' && !!confirmPassword && password !== confirmPassword;

  const sendReset = async (email: string) => {
    await supabase.auth.resetPasswordForEmail(
      email /* , { redirectTo: `${window.location.origin}/reset-password` } */,
    );
    setBanner({
      kind: 'info',
      text: "If an account exists for that email, we've sent a password reset link.",
    });
  };

  const onSubmit = async (values: AuthValues) => {
    setIsLoading(true);
    setErrorMessage('');
    setBanner({ kind: null, text: '' });

    try {
      if (mode === 'sign-in') {
        const v = values as SignInValues;
        await login(v.email, v.password);
        navigate('/conferences');
        return;
      }

      const v = values as SignUpValues;
      const result = await signup(v.email, v.password);

      let isLikelyExisting = false;
      try {
        const user = (result as any)?.data?.user ?? (await supabase.auth.getUser()).data.user;
        if (
          user &&
          Array.isArray((user as any).identities) &&
          (user as any).identities.length === 0
        ) {
          isLikelyExisting = true;
        }
      } catch {}

      if (isLikelyExisting) {
        setBanner({
          kind: 'warn',
          text: 'That email may already have an account. Try signing in, or request a password reset.',
        });
      } else {
        setBanner({
          kind: 'info',
          text: 'Check your email to confirm your account. If you don’t see it, check spam.',
        });
      }
    } catch (e: any) {
      setErrorMessage(e?.message || 'Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const InlineBanner = ({
    children,
    kind,
  }: {
    children: React.ReactNode;
    kind: 'info' | 'warn';
  }) => (
    <p className={`text-sm ${kind === 'warn' ? 'text-destructive' : 'text-gray-200'}`}>
      {children}
    </p>
  );

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="auth-form max-w-sm space-y-4 bg-gray-500 p-4 rounded-lg"
    >
      <h1 className="text-xl font-semibold mb-2 text-[#0c2340]">{title}</h1>

      <div className="space-y-1">
        <label htmlFor="email" className="shad-form-label">
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="Enter your email"
          className="shad-input"
          {...register('email')}
        />
        {errors.email && (
          <p className="text-sm font-medium text-destructive">{String(errors.email.message)}</p>
        )}
      </div>

      <div className="space-y-1">
        <label htmlFor="password" className="shad-form-label">
          Password
        </label>
        <div className="relative">
          <input
            id="password"
            type={showPw ? 'text' : 'password'}
            autoComplete={mode === 'sign-in' ? 'current-password' : 'new-password'}
            placeholder="Enter your password"
            className="shad-input pr-10"
            {...register('password')}
          />
          <IconButton
            aria-label={showPw ? 'Hide password' : 'Show password'}
            onClick={() => setShowPw((s) => !s)}
            size="small"
            className="!absolute right-1 top-1/2 -translate-y-1/2"
          >
            {showPw ? <VisibilityOff /> : <Visibility />}
          </IconButton>
        </div>
        {errors.password && (
          <p className="text-sm font-medium text-destructive">{String(errors.password.message)}</p>
        )}

        {mode === 'sign-in' && banner.kind && (
          <InlineBanner kind={banner.kind}>{banner.text}</InlineBanner>
        )}
      </div>

      {mode === 'sign-up' && (
        <div className="space-y-1">
          <label htmlFor="confirmPassword" className="shad-form-label">
            Confirm Password
          </label>
          <div className="relative">
            <input
              id="confirmPassword"
              type={showConfirm ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="Re-enter your password"
              className="shad-input pr-10"
              {...register('confirmPassword' as any)}
            />
            <IconButton
              aria-label={showConfirm ? 'Hide password' : 'Show password'}
              onClick={() => setShowConfirm((s) => !s)}
              size="small"
              className="!absolute right-1 top-1/2 -translate-y-1/2"
            >
              {showConfirm ? <VisibilityOff /> : <Visibility />}
            </IconButton>
          </div>

          {(errors as any).confirmPassword && (
            <p className="text-sm font-medium text-destructive">
              {String((errors as any).confirmPassword?.message)}
            </p>
          )}
          {!(errors as any).confirmPassword && mismatch && (
            <p className="text-sm font-medium text-destructive">Passwords do not match!</p>
          )}

          {banner.kind && (
            <>
              <InlineBanner kind={banner.kind}>{banner.text}</InlineBanner>
              {banner.kind === 'warn' && (
                <div className="mt-1 flex gap-3 text-sm">
                  <button
                    type="button"
                    className="underline text-[#e87722]"
                    onClick={() => setMode('sign-in')}
                  >
                    Sign in
                  </button>
                  <button
                    type="button"
                    className="underline text-[#e87722]"
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
      )}

      <button
        type="submit"
        className="bg-[#e87722] text-white w-full rounded-full my-2 h-10 px-4 py-2 disabled:opacity-50"
        disabled={isLoading || (mode === 'sign-up' && mismatch)}
      >
        {isLoading ? 'Working...' : title}
      </button>

      {errorMessage && <p className="error-message">* {errorMessage}</p>}

      <div className="text-center text-sm">
        {mode === 'sign-in' ? (
          <button
            type="button"
            className="font-medium text-[#e87722] underline underline-offset-4"
            onClick={() => setMode('sign-up')}
          >
            Don't have an account? Sign Up!
          </button>
        ) : (
          <button
            type="button"
            className="font-medium text-[#e87722] underline underline-offset-4"
            onClick={() => setMode('sign-in')}
          >
            Already have an account? Sign In!
          </button>
        )}
      </div>
    </form>
  );
}
