"""
Belon Backend — FastAPI Application
AI-Powered CRM Pipeline Automation
Version: 2.0 | April 2026
"""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from supabase import create_client

from config import settings
from routers import (
    signals_router, workflows_router, integrations_router,
    billing_router, ai_router, deals_router,
)
from services.signal_engine import SignalEngine
from services.workflow_engine import WorkflowEngine
from services.ai_service import ai_service
from services.email_service import email_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_signal_engine_for_all_users():
    """Background task: run signal engine for every active subscriber."""
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        # Get all active/trialing users
        resp = (
            supabase.table("subscriptions")
            .select("user_id")
            .in_("status", ["active", "trialing"])
            .execute()
        )
        users = resp.data or []
        engine = SignalEngine(supabase)
        total = 0
        for u in users:
            try:
                count = await engine.run_for_user(u["user_id"])
                total += count
            except Exception as e:
                logger.error(f"Signal engine failed for {u['user_id']}: {e}")
        logger.info(f"Signal engine complete: {total} signals across {len(users)} users")
    except Exception as e:
        logger.error(f"Signal engine background task failed: {e}")


async def run_scheduled_workflows_for_all_users():
    """Background task: execute scheduled workflows."""
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        resp = (
            supabase.table("subscriptions")
            .select("user_id")
            .in_("status", ["active", "trialing"])
            .execute()
        )
        users = resp.data or []
        wf_engine = WorkflowEngine(supabase, ai_service, email_service)
        for u in users:
            try:
                await wf_engine.run_scheduled_workflows(u["user_id"])
            except Exception as e:
                logger.error(f"Workflow scheduler failed for {u['user_id']}: {e}")
    except Exception as e:
        logger.error(f"Workflow background task failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background schedulers
    scheduler.add_job(
        run_signal_engine_for_all_users,
        "interval",
        minutes=settings.SIGNAL_ENGINE_INTERVAL_MINUTES,
        id="signal_engine",
        replace_existing=True,
    )
    scheduler.add_job(
        run_scheduled_workflows_for_all_users,
        "interval",
        minutes=30,
        id="workflow_scheduler",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Belon backend started. Signal engine every {settings.SIGNAL_ENGINE_INTERVAL_MINUTES}min.")
    yield
    scheduler.shutdown(wait=False)
    logger.info("Belon backend shutting down.")


app = FastAPI(
    title="Belon API",
    description="AI-Powered CRM Pipeline Automation — 100+ Signal Engine, 6 Workflow Templates",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(signals_router)
app.include_router(workflows_router)
app.include_router(integrations_router)
app.include_router(billing_router)
app.include_router(ai_router)
app.include_router(deals_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "signal_engine": f"every {settings.SIGNAL_ENGINE_INTERVAL_MINUTES}min",
    }


@app.get("/")
async def root():
    return {"name": "Belon API", "version": "2.0.0"}
