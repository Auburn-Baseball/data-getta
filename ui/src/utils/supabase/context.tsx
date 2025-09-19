import { createContext, useContext, useEffect, useState } from 'react';
import type { User } from '@supabase/supabase-js';
import { supabase } from '@/utils/supabase/client';

type AuthCtx = { user: User | null; loading: boolean };
const Ctx = createContext<AuthCtx>({ user: null, loading: true });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    supabase.auth.getSession().then(({ data }) => {
      if (!isMounted) return;
      setUser(data.session?.user ?? null);
      setLoading(false);
    });

    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => {
      isMounted = false;
      sub.subscription.unsubscribe();
    };
  }, []);

  return <Ctx.Provider value={{ user, loading }}>{children}</Ctx.Provider>;
}

export function useAuth() {
  return useContext(Ctx);
}
