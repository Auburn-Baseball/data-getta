import { supabase } from '@/utils/supabase/client';

export async function login(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data;
}

export async function signup(email: string, password: string) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  });
  if (error) throw error;
  return data;
}

export async function logout() {
  const { error } = await supabase.auth.signOut();

  if (error) {
    throw error;
  }
}
