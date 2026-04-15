// Auto-generated types for Supabase tables
export type Json = string | number | boolean | null | { [key: string]: Json } | Json[];

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          email: string;
          full_name: string | null;
          company_name: string | null;
          role: string;
          onboarded: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: Omit<Database["public"]["Tables"]["profiles"]["Row"], "created_at" | "updated_at">;
        Update: Partial<Database["public"]["Tables"]["profiles"]["Insert"]>;
      };
      subscriptions: {
        Row: {
          id: string;
          user_id: string;
          stripe_customer_id: string | null;
          stripe_subscription_id: string | null;
          status: string;
          trial_end: string | null;
          current_period_end: string | null;
          cancel_at_period_end: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: Partial<Database["public"]["Tables"]["subscriptions"]["Row"]>;
        Update: Partial<Database["public"]["Tables"]["subscriptions"]["Row"]>;
      };
      signals: {
        Row: {
          id: string;
          user_id: string;
          signal_type: string;
          category: string;
          severity: string;
          title: string;
          description: string | null;
          entity_type: string | null;
          entity_name: string | null;
          deal_value: number | null;
          action_label: string | null;
          action_type: string | null;
          status: string;
          source: string;
          created_at: string;
          updated_at: string;
        };
        Insert: Omit<Database["public"]["Tables"]["signals"]["Row"], "id" | "created_at" | "updated_at">;
        Update: Partial<Database["public"]["Tables"]["signals"]["Insert"]>;
      };
      workflows: {
        Row: {
          id: string;
          user_id: string;
          name: string;
          description: string | null;
          status: string;
          trigger_type: string;
          trigger_config: Json;
          nodes: Json;
          edges: Json;
          run_count: number;
          success_count: number;
          fail_count: number;
          last_run_at: string | null;
          template_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: Omit<Database["public"]["Tables"]["workflows"]["Row"], "id" | "run_count" | "success_count" | "fail_count" | "created_at" | "updated_at">;
        Update: Partial<Database["public"]["Tables"]["workflows"]["Insert"]>;
      };
      deals: {
        Row: {
          id: string;
          user_id: string;
          name: string;
          company_name: string | null;
          value: number;
          stage: string;
          health_score: number;
          owner_name: string | null;
          days_in_stage: number;
          source: string;
          created_at: string;
        };
        Insert: Omit<Database["public"]["Tables"]["deals"]["Row"], "id" | "created_at">;
        Update: Partial<Database["public"]["Tables"]["deals"]["Insert"]>;
      };
      integrations: {
        Row: {
          id: string;
          user_id: string;
          provider: string;
          status: string;
          account_name: string | null;
          last_sync_at: string | null;
          records_synced: number;
        };
        Insert: Partial<Database["public"]["Tables"]["integrations"]["Row"]>;
        Update: Partial<Database["public"]["Tables"]["integrations"]["Row"]>;
      };
    };
  };
}
