import { useContext } from 'react';
import { AuthContext } from './provider';

export function useAuth() {
  return useContext(AuthContext);
}
