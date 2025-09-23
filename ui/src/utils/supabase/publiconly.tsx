import { Navigate, Outlet, useLocation } from 'react-router';
import { useAuth } from '@/utils/supabase/useauth';

export default function PublicOnly() {
  const { user, recovery, loading } = useAuth();
  const { pathname } = useLocation();

  if (loading) return <div style={{ padding: 24 }}>Checking session…</div>;

  console.log('PublicOnly', { user, recovery, pathname });
  if (recovery && pathname !== '/reset-password') {
    console.log('redirecting to reset-password');
    return <Navigate to="/reset-password" replace />;
  }

  if (user && !recovery) {
    return <Navigate to="/conferences" replace />;
  }

  if (!user && !recovery && pathname !== '/') {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
