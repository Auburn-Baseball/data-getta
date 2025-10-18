import { useEffect, useState } from 'react';
import type { User } from '@supabase/supabase-js';

import { supabase } from '@/lib/supabaseClient';
import { AuthContext } from './AuthContext';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [recovery, setRecovery] = useState(false);

  useEffect(() => {
    let isMounted = true;

    try {
      const href = typeof window !== 'undefined' ? window.location.href : '';
      const url = new URL(href);
      const qs = new URLSearchParams(url.search);
      const hs = new URLSearchParams(url.hash.startsWith('#') ? url.hash.slice(1) : url.hash);
      const type = qs.get('type') || hs.get('type');
      if (type === 'recovery') setRecovery(true);
    } catch (error) {
      console.error('Failed to parse auth recovery status from URL:', error);
    }

    supabase.auth.getSession().then(({ data }) => {
      if (!isMounted) return;
      setUser(data.session?.user ?? null);
      setLoading(false);
    });

    const { data: sub } = supabase.auth.onAuthStateChange((event, session) => {
      if (!isMounted) return;

      if (event === 'SIGNED_OUT') {
        setUser(null);
        setRecovery(false);
        setLoading(false);
        return;
      }

      if (
        event === 'INITIAL_SESSION' ||
        event === 'SIGNED_IN' ||
        event === 'TOKEN_REFRESHED' ||
        event === 'USER_UPDATED'
      ) {
        setUser(session?.user ?? null);
        setLoading(false);
        return;
      }
    });

    return () => {
      isMounted = false;
      sub.subscription.unsubscribe();
    };
  }, []);

  return (
    <AuthContext.Provider value={{ user, recovery, loading, setUser, setRecovery }}>
      {children}
    </AuthContext.Provider>
  );
}
