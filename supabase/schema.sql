-- ============================================================
-- BELON — Complete Supabase Schema
-- Version: 2.0 | April 2026
-- ============================================================

-- Enable extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ============================================================
-- TABLES
-- ============================================================

-- Profiles (extends auth.users)
create table public.profiles (
  id uuid references auth.users(id) on delete cascade primary key,
  email text not null,
  full_name text,
  company_name text,
  avatar_url text,
  role text default 'user' check (role in ('user', 'admin')),
  onboarded boolean default false,
  timezone text default 'UTC',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Subscriptions
create table public.subscriptions (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null unique,
  stripe_customer_id text unique,
  stripe_subscription_id text unique,
  stripe_price_id text,
  status text not null default 'trialing'
    check (status in ('trialing','active','canceled','past_due','incomplete','incomplete_expired','unpaid')),
  trial_start timestamptz default now(),
  trial_end timestamptz default (now() + interval '5 days'),
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Signals (100+ signal types engine)
create table public.signals (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  -- Signal classification
  signal_type text not null,
  category text not null check (category in (
    'deal_health','engagement','churn_risk','buying_signal',
    'rep_performance','pipeline_health','sequence','enrichment','ai_insight'
  )),
  severity text not null default 'medium'
    check (severity in ('critical','high','medium','low','info')),
  -- Display
  title text not null,
  description text,
  -- Entity context
  entity_type text check (entity_type in ('deal','contact','company','rep','pipeline')),
  entity_id text,
  entity_name text,
  deal_value numeric,
  -- Next Best Action
  action_label text,
  action_type text check (action_type in ('email','task','call','crm_update','workflow','ai_draft','schedule')),
  action_payload jsonb default '{}',
  -- Lifecycle
  status text default 'pending' check (status in ('pending','actioned','dismissed','snoozed')),
  actioned_at timestamptz,
  snoozed_until timestamptz,
  -- Source
  source text default 'ai' check (source in ('ai','hubspot','gmail','linkedin','slack','zoom','manual','stripe')),
  metadata jsonb default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Workflows
create table public.workflows (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  name text not null,
  description text,
  status text default 'active' check (status in ('active','paused','draft','archived')),
  template_id text, -- references a built-in template slug
  trigger_type text not null check (trigger_type in (
    'deal_stage_change','signal_fired','schedule','manual','webhook','contact_created','deal_created'
  )),
  trigger_config jsonb default '{}',
  nodes jsonb default '[]',
  edges jsonb default '[]',
  run_count integer default 0,
  success_count integer default 0,
  fail_count integer default 0,
  last_run_at timestamptz,
  next_run_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Workflow executions
create table public.workflow_runs (
  id uuid default uuid_generate_v4() primary key,
  workflow_id uuid references public.workflows(id) on delete cascade not null,
  user_id uuid references public.profiles(id) on delete cascade not null,
  status text default 'running' check (status in ('running','completed','failed','canceled')),
  trigger_data jsonb default '{}',
  result jsonb default '{}',
  nodes_executed integer default 0,
  error_message text,
  started_at timestamptz default now(),
  completed_at timestamptz,
  duration_ms integer
);

-- Integrations
create table public.integrations (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  provider text not null check (provider in ('hubspot','salesforce','gmail','slack','zoom','linkedin','pipedrive')),
  status text default 'disconnected' check (status in ('connected','disconnected','error','syncing','pending_auth')),
  access_token text,
  refresh_token text,
  token_expires_at timestamptz,
  account_id text,
  account_name text,
  scopes text[],
  config jsonb default '{}',
  last_sync_at timestamptz,
  next_sync_at timestamptz,
  sync_error text,
  records_synced integer default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(user_id, provider)
);

-- Deals (synced from CRM + manual)
create table public.deals (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  external_id text,
  source text default 'manual' check (source in ('hubspot','salesforce','pipedrive','manual')),
  name text not null,
  company_name text,
  contact_name text,
  contact_email text,
  value numeric default 0,
  stage text not null default 'discovery',
  health_score integer default 50 check (health_score >= 0 and health_score <= 100),
  health_factors jsonb default '{}',
  owner_name text,
  owner_email text,
  days_in_stage integer default 0,
  last_activity_at timestamptz,
  last_contact_at timestamptz,
  expected_close_date date,
  probability integer default 20 check (probability >= 0 and probability <= 100),
  notes text,
  tags text[],
  metadata jsonb default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(user_id, external_id, source)
);

-- Contacts
create table public.contacts (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  external_id text,
  source text default 'manual',
  first_name text,
  last_name text,
  email text,
  phone text,
  company_name text,
  title text,
  linkedin_url text,
  lead_score integer default 0 check (lead_score >= 0 and lead_score <= 100),
  status text default 'lead' check (status in ('lead','prospect','customer','churned','unqualified')),
  last_contacted_at timestamptz,
  engagement_score integer default 0,
  metadata jsonb default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- AI actions log
create table public.ai_actions (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  signal_id uuid references public.signals(id) on delete set null,
  workflow_run_id uuid references public.workflow_runs(id) on delete set null,
  action_type text not null check (action_type in (
    'email_draft','lead_score','deal_analysis','sequence_generate',
    'churn_prediction','pipeline_forecast','re_engagement','enrichment'
  )),
  input_context jsonb default '{}',
  model_used text default 'falcon-7b',
  output text,
  tokens_used integer,
  latency_ms integer,
  quality_score numeric,
  status text default 'completed' check (status in ('pending','completed','failed')),
  created_at timestamptz default now()
);

-- HubSpot sync log
create table public.hubspot_sync_log (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  sync_type text not null check (sync_type in ('full','incremental','webhook')),
  direction text not null check (direction in ('pull','push','bidirectional')),
  entity_type text not null check (entity_type in ('contacts','deals','companies','activities')),
  records_processed integer default 0,
  records_created integer default 0,
  records_updated integer default 0,
  records_failed integer default 0,
  error_details jsonb default '[]',
  started_at timestamptz default now(),
  completed_at timestamptz,
  status text default 'running' check (status in ('running','completed','failed'))
);

-- Waitlist (for landing page)
create table public.waitlist (
  id uuid default uuid_generate_v4() primary key,
  email text unique not null,
  name text,
  company text,
  use_case text,
  source text default 'landing',
  stripe_payment_intent_id text,
  paid boolean default false,
  status text default 'waiting' check (status in ('waiting','invited','converted','refunded')),
  invited_at timestamptz,
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

-- Audit log
create table public.audit_log (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete set null,
  action text not null,
  resource_type text,
  resource_id text,
  old_values jsonb,
  new_values jsonb,
  ip_address inet,
  user_agent text,
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

alter table public.profiles enable row level security;
alter table public.subscriptions enable row level security;
alter table public.signals enable row level security;
alter table public.workflows enable row level security;
alter table public.workflow_runs enable row level security;
alter table public.integrations enable row level security;
alter table public.deals enable row level security;
alter table public.contacts enable row level security;
alter table public.ai_actions enable row level security;
alter table public.hubspot_sync_log enable row level security;
alter table public.waitlist enable row level security;
alter table public.audit_log enable row level security;

-- Profiles
create policy "profiles_select_own" on public.profiles for select using (auth.uid() = id);
create policy "profiles_update_own" on public.profiles for update using (auth.uid() = id);
create policy "profiles_insert_own" on public.profiles for insert with check (auth.uid() = id);

-- Subscriptions
create policy "subscriptions_select_own" on public.subscriptions for select using (auth.uid() = user_id);
create policy "subscriptions_service_all" on public.subscriptions using (auth.role() = 'service_role');

-- Signals (full CRUD for authenticated user)
create policy "signals_all_own" on public.signals for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Workflows
create policy "workflows_all_own" on public.workflows for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Workflow runs
create policy "workflow_runs_select_own" on public.workflow_runs for select using (auth.uid() = user_id);
create policy "workflow_runs_service_all" on public.workflow_runs using (auth.role() = 'service_role');

-- Integrations
create policy "integrations_all_own" on public.integrations for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Deals
create policy "deals_all_own" on public.deals for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Contacts
create policy "contacts_all_own" on public.contacts for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- AI Actions
create policy "ai_actions_select_own" on public.ai_actions for select using (auth.uid() = user_id);
create policy "ai_actions_service_all" on public.ai_actions using (auth.role() = 'service_role');

-- HubSpot sync log
create policy "hubspot_sync_select_own" on public.hubspot_sync_log for select using (auth.uid() = user_id);
create policy "hubspot_sync_service_all" on public.hubspot_sync_log using (auth.role() = 'service_role');

-- Waitlist
create policy "waitlist_insert_anon" on public.waitlist for insert with check (true);
create policy "waitlist_service_all" on public.waitlist using (auth.role() = 'service_role');

-- Audit log
create policy "audit_select_own" on public.audit_log for select using (auth.uid() = user_id);
create policy "audit_service_all" on public.audit_log using (auth.role() = 'service_role');

-- ============================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================

-- Auto-create profile + trial subscription on signup
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email, full_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1))
  );

  insert into public.subscriptions (user_id, status, trial_start, trial_end)
  values (
    new.id,
    'trialing',
    now(),
    now() + interval '5 days'
  );

  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Update updated_at helper
create or replace function public.update_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger trg_profiles_updated_at before update on public.profiles for each row execute procedure public.update_updated_at();
create trigger trg_subscriptions_updated_at before update on public.subscriptions for each row execute procedure public.update_updated_at();
create trigger trg_signals_updated_at before update on public.signals for each row execute procedure public.update_updated_at();
create trigger trg_workflows_updated_at before update on public.workflows for each row execute procedure public.update_updated_at();
create trigger trg_integrations_updated_at before update on public.integrations for each row execute procedure public.update_updated_at();
create trigger trg_deals_updated_at before update on public.deals for each row execute procedure public.update_updated_at();
create trigger trg_contacts_updated_at before update on public.contacts for each row execute procedure public.update_updated_at();

-- Auto-compute deal health score
create or replace function public.compute_deal_health(
  p_days_in_stage integer,
  p_last_activity_at timestamptz,
  p_stage text,
  p_days_since_contact integer default null
)
returns integer
language plpgsql
as $$
declare
  score integer := 100;
  days_stale integer;
begin
  days_stale := coalesce(p_days_since_contact, extract(day from now() - coalesce(p_last_activity_at, now() - interval '30 days'))::integer);

  -- Penalize by days stale
  score := score - least(days_stale * 3, 40);

  -- Penalize by days in stage (stage-relative)
  case p_stage
    when 'discovery' then score := score - least(p_days_in_stage * 2, 20);
    when 'qualification' then score := score - least(p_days_in_stage * 2, 25);
    when 'proposal' then score := score - least(p_days_in_stage * 3, 30);
    when 'negotiation' then score := score - least(p_days_in_stage * 4, 35);
    else score := score - least(p_days_in_stage * 2, 20);
  end case;

  return greatest(score, 0);
end;
$$;

-- Realtime: enable for signals and workflow_runs
alter publication supabase_realtime add table public.signals;
alter publication supabase_realtime add table public.workflow_runs;

-- ============================================================
-- INDEXES
-- ============================================================

create index idx_signals_user_status on public.signals(user_id, status);
create index idx_signals_severity on public.signals(severity);
create index idx_signals_category on public.signals(category);
create index idx_signals_created_desc on public.signals(created_at desc);
create index idx_signals_entity on public.signals(entity_type, entity_id);

create index idx_workflows_user_status on public.workflows(user_id, status);
create index idx_workflow_runs_workflow on public.workflow_runs(workflow_id);
create index idx_workflow_runs_user on public.workflow_runs(user_id);
create index idx_workflow_runs_started on public.workflow_runs(started_at desc);

create index idx_deals_user_stage on public.deals(user_id, stage);
create index idx_deals_health on public.deals(health_score);
create index idx_deals_value on public.deals(value desc);

create index idx_contacts_user_status on public.contacts(user_id, status);
create index idx_contacts_email on public.contacts(email);

create index idx_audit_user_created on public.audit_log(user_id, created_at desc);

-- ============================================================
-- SEED: Built-in Workflow Templates (stored as reference data)
-- ============================================================

create table public.workflow_templates (
  id text primary key,
  name text not null,
  description text,
  category text,
  trigger_type text not null,
  nodes jsonb default '[]',
  edges jsonb default '[]',
  icon text default 'zap',
  created_at timestamptz default now()
);

insert into public.workflow_templates (id, name, description, category, trigger_type, icon) values
  ('stalled-deal-recovery', 'Stalled Deal Recovery', 'Detect stalled deals, draft AI re-engagement email, notify rep', 'deal_health', 'deal_stage_change', 'clock'),
  ('lead-qualification', 'Instant Lead Qualification', 'Score new leads with AI, update CRM, create follow-up tasks', 'pipeline', 'contact_created', 'user-check'),
  ('churn-risk-alert', 'Churn Risk Alert', 'Detect renewal risk signals, identify champion, trigger save playbook', 'churn_risk', 'signal_fired', 'alert-triangle'),
  ('deal-velocity', 'Deal Velocity Optimizer', 'Monitor deals stalling between stages, auto-advance or escalate', 'pipeline', 'schedule', 'trending-up'),
  ('buying-signal-outreach', 'Buying Signal Fast-Track', 'Detect intent signals, draft personalised outreach, schedule call', 'engagement', 'signal_fired', 'zap'),
  ('pipeline-health-check', 'Daily Pipeline Health Check', 'Nightly sweep of all deals, compute health scores, surface critical actions', 'pipeline', 'schedule', 'activity');
