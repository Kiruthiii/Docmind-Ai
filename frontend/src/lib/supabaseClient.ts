import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

if (!supabaseUrl || !supabaseAnonKey || supabaseUrl.includes('demo-project.supabase.co')) {
  console.warn(
    '[DocMind Auth Warning] Supabase environment variables (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY) are missing or using demo placeholders in frontend/.env. Please ensure valid Supabase credentials are set.'
  );
}

export const supabase = createClient(
  supabaseUrl || 'https://demo-project.supabase.co',
  supabaseAnonKey || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.demo'
);

