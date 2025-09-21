import { Navigate, Outlet } from 'react-router';
import { useAuth } from '@/utils/supabase/useauth';

export default function AuthGuard() {
  const { user, recovery, loading } = useAuth();

  if (loading) return <div style={{ padding: 24 }}>Checking session…</div>;

  if (recovery) {
    return <Navigate to="/reset-password" replace />;
  }

  if (user) {
    return <Navigate to="/conferences" replace />;
  }

  return <Outlet />;
}
