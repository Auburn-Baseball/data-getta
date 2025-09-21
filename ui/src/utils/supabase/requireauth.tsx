import { Navigate, Outlet, useLocation } from 'react-router';
import { useAuth } from '@/utils/supabase/useauth';

export default function RequireAuth() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div style={{ padding: 24 }}>Checking session…</div>;
  }
  if (!user) {
    return <Navigate to="/" replace state={{ from: location }} />;
  }
  return <Outlet />;
}
