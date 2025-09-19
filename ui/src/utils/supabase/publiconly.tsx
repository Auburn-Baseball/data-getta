import { Navigate, Outlet } from 'react-router';
import { useAuth } from '@/utils/supabase/context';

export default function PublicOnly() {
  const { user, loading } = useAuth();

  if (loading) return <div style={{ padding: 24 }}>Checking session…</div>;
  if (user) return <Navigate to="/conferences" replace />;

  return <Outlet />;
}
