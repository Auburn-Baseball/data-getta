import { Navigate, Outlet, useLocation } from 'react-router';
import { useAuth } from '@/utils/supabase/context';

export default function PublicOnly() {
  const { user, recovery, loading } = useAuth();
  if (loading) return <div style={{ padding: 24 }}>Checking session…</div>;

  const location = useLocation();
  const { pathname } = location;
  if (pathname === '/reset-password' && recovery) {
    console.log('reset password made it here');
    return <Outlet />;
  }

  if (user) {
    return <Navigate to="/conferences" replace />;
  }

  return <Outlet />;
}
