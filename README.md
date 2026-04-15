# Belon — AI-Powered CRM Pipeline Automation

> **100% Autonomous CRM Pipeline Decryption with 99% Accuracy**  
> Version: 2.0 | April 2026

## Overview

Belon is a full-stack B2B SaaS automation platform that runs an always-on AI agent over your CRM pipeline. It detects 100+ signal types, executes 6 pre-built automation workflows, and surfaces Next Best Actions — all in real time.

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS |
| Visual Builder | React Flow (`@xyflow/react`) |
| Backend | Python FastAPI |
| Database + Auth | Supabase (PostgreSQL + Supabase Auth) |
| AI Engine | Hugging Face Inference (Falcon-7B default) |
| Payments | Stripe (5-day trial → $1,000/year) |
| Email | Resend.com |
| Frontend Deploy | Vercel |
| Backend Deploy | Railway |

---

## Project Structure

```
belon/
├── frontend/          # Next.js 14 internal app
│   ├── app/
│   │   ├── (auth)/    # login, signup
│   │   ├── (protected)/
│   │   │   ├── control-center/    # Automation Control Center
│   │   │   ├── workflow-builder/  # Visual Workflow Builder
│   │   │   ├── signals/           # Signal Intelligence Feed
│   │   │   ├── integrations/      # Integrations Hub
│   │   │   └── billing/           # Subscription management
│   │   └── layout.tsx
│   ├── components/
│   │   ├── layout/    # Sidebar, Header
│   │   └── ui/        # Sonner toast
│   ├── lib/           # supabase.ts, api.ts, utils.ts
│   └── middleware.ts  # Auth protection
├── backend/           # FastAPI
│   ├── main.py        # App entry + scheduler
│   ├── config.py      # Settings (pydantic-settings)
│   ├── dependencies.py # JWT auth, Supabase client
│   ├── models/
│   │   └── schemas.py # Pydantic models
│   ├── routers/       # signals, workflows, integrations, billing, ai, deals
│   └── services/      # signal_engine, workflow_engine, ai_service, hubspot, stripe, email
├── supabase/
│   └── schema.sql     # Full schema + RLS + functions + indexes
└── README.md
```

---

## Local Development

### Prerequisites

- Node.js 20+ / pnpm or npm
- Python 3.11+
- Supabase CLI (`npm i -g supabase`)
- A Supabase project (free tier works)
- Stripe account
- Hugging Face account (free tier works)
- Resend account (free tier works)

---

### 1. Supabase Setup

```bash
# In your Supabase project dashboard → SQL Editor → run:
# Copy-paste the contents of supabase/schema.sql and execute it.

# OR using Supabase CLI:
supabase db push --db-url postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres < supabase/schema.sql
```

Enable **Realtime** for the `signals` and `workflow_runs` tables in the Supabase dashboard under `Database → Replication`.

---

### 2. Backend Setup

```bash
cd belon/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Fill in all values in .env

# Run
uvicorn main:app --reload --port 8000
```

The API will be live at `http://localhost:8000`  
Docs at `http://localhost:8000/docs`

---

### 3. Frontend Setup

```bash
cd belon/frontend

# Install dependencies
npm install
# or: pnpm install

# Configure environment
cp .env.example .env.local
# Fill in all values in .env.local

# Run
npm run dev
```

App runs at `http://localhost:3000`

---

### 4. Stripe Setup

```bash
# Install Stripe CLI for local webhooks
stripe listen --forward-to localhost:8000/billing/webhook

# Create the $1,000/year price in Stripe Dashboard:
# Products → Create Product → "Belon Pro" → $1,000/year recurring
# Copy the price_xxxx ID into backend/.env STRIPE_PRICE_ID
```

---

## Deployment

### Frontend → Vercel

```bash
cd belon/frontend
vercel --prod

# Environment variables to set in Vercel:
# NEXT_PUBLIC_SUPABASE_URL
# NEXT_PUBLIC_SUPABASE_ANON_KEY
# NEXT_PUBLIC_API_URL  (your Railway backend URL)
# NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
```

### Backend → Railway

```bash
# In Railway dashboard:
# 1. New Project → Deploy from GitHub → select belon/backend
# 2. Set root directory to: belon/backend
# 3. Set start command: uvicorn main:app --host 0.0.0.0 --port $PORT
# 4. Add all environment variables from backend/.env.example
# 5. Deploy

# After deployment, update in Stripe Dashboard:
# Webhooks → Add endpoint → https://your-api.railway.app/billing/webhook
# Events: customer.subscription.*, invoice.payment_*
```

---

## Core Features

### 100+ Signal Engine
- **20 Deal Health signals**: stall detection (7d/14d/21d), health drops, missing next steps, close date past
- **20 Buying Signals**: pricing page visits, demo requests, ROI calculator, multi-stakeholder engagement
- **15 Churn Risk signals**: renewal approaching, champion disengaged, usage drop, payment failures
- **15 Rep Performance signals**: activity gaps, quota tracking, response time SLA, forecast gaps
- **15 Pipeline Health signals**: coverage ratio, stale deals, win rate drops, forecast risk
- **10 Engagement signals**: email opens, meeting no-shows, content engagement, event signals
- **5 AI Insights**: ML deal slip prediction, optimal contact time, competitor threats
- Runs automatically every 15 minutes for all active subscribers
- Real-time delivery via Supabase Realtime

### 6 Automation Workflows
1. **Stalled Deal Recovery** — Detect → AI analyze → Generate email → Notify rep
2. **Instant Lead Qualification** — Score with AI → Tag in CRM → Route to rep
3. **Churn Risk Alert** — Detect risk → AI analysis → Save email → CS escalation
4. **Deal Velocity Optimizer** — Daily sweep → Flag stalled → Rep digest
5. **Buying Signal Fast-Track** — Intent detected → Enrich → Personalized outreach → Create deal
6. **Daily Pipeline Health Check** — Nightly AI forecast → Critical alerts → Daily summary

### Visual Workflow Builder
- React Flow canvas with 5 node types: Trigger, Condition, AI Action, CRM Action, Notification
- Drag-and-drop with live edge connections
- Condition branching (Yes/No paths)
- Save to Supabase, run from UI, view run history

### Automation Control Center
- Live signal feed with Next Best Action buttons
- Real-time updates via Supabase Realtime
- Pipeline health stats: health score, active deals, at-risk revenue
- One-click signal actions (actioned/dismissed/snoozed)

### Integrations Hub
- **HubSpot**: Full OAuth 2.0, contacts + deals sync (priority integration)
- Gmail, Slack, Zoom, LinkedIn, Salesforce, Pipedrive (framework ready)

### Auth + Billing
- Supabase Auth (email/password, magic link ready)
- 5-day free trial auto-provisioned on signup
- Stripe Checkout → $1,000/year
- Customer Portal for self-serve management
- Webhook handler for all Stripe subscription events

---

## Environment Variables Reference

### Backend (`backend/.env`)
| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (server-side only) |
| `STRIPE_SECRET_KEY` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `STRIPE_PRICE_ID` | The $1,000/year price ID |
| `HUGGINGFACE_API_TOKEN` | HuggingFace API token |
| `RESEND_API_KEY` | Resend API key |
| `HUBSPOT_CLIENT_ID` | HubSpot app client ID |
| `HUBSPOT_CLIENT_SECRET` | HubSpot app client secret |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |
| `NEXT_PUBLIC_API_URL` | FastAPI backend URL |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key |

---

## Design System

- **Colors**: Orange `#f97316` + Black `#080808` only
- **Font**: Sora (Google Fonts)
- **Icons**: Lucide React
- **UI**: No charts/tables as primary elements — card-first mission control feel
- **Animation**: `belon-enter-up` / `belon-enter-x` CSS animations
- **Never**: use the word "dashboard" anywhere

---

Built with ❤️ using Falcon-7B · Supabase · FastAPI · Next.js 14
