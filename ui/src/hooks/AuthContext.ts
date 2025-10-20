import { createContext } from 'react';
import type { User } from '@supabase/supabase-js';

export type AuthCtx = {
  user: User | null;
  recovery: boolean;
  loading: boolean;
  setUser: (u: User | null) => void;
  setRecovery: (v: boolean) => void;
};

const noop = () => undefined;

export const AuthContext = createContext<AuthCtx>({
  user: null,
  recovery: false,
  loading: true,
  setUser: noop,
  setRecovery: noop,
});
