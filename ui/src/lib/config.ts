const config = {
  supabaseUrl: import.meta.env.VITE_SUPABASE_PROJECT_URL ?? '',
  supabaseApiKey: import.meta.env.VITE_SUPABASE_API_KEY ?? '',
};

if (!config.supabaseUrl || !config.supabaseApiKey) {
  throw new Error('Missing Supabase environment variables');
}

export default config;
