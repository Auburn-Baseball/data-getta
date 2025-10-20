import { Outlet } from 'react-router';

import AuthShell from '@/components/AuthShell';

export default function AuthLayout() {
  return (
    <AuthShell>
      <Outlet />
    </AuthShell>
  );
}
