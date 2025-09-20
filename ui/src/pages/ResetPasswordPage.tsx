import AuthShell from '@/components/AuthShell';
import { ResetPasswordForm } from '@/components/ResetPasswordForm';

export default function ResetPasswordPage() {
  return (
    <AuthShell>
      <ResetPasswordForm className="w-96" />
    </AuthShell>
  );
}
