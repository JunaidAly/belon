import { createBrowserClient } from "@supabase/ssr";
import type { Database } from "./database.types";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

// Browser client (singleton)
let _client: ReturnType<typeof createBrowserClient<Database>> | null = null;

export function getSupabaseBrowser() {
  if (!_client) {
    _client = createBrowserClient<Database>(supabaseUrl, supabaseAnonKey);
  }
  return _client;
}

// For convenience in components
export const supabase = getSupabaseBrowser();
