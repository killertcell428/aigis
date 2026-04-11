"""Aigis FastAPI application entry point."""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.billing.webhooks import router as webhook_router
from app.routers.admin import router as admin_router
from app.routers.audit import router as audit_router
from app.routers.monitor import router as monitor_router
from app.routers.billing import router as billing_router
from app.routers.gandalf import router as gandalf_router
from app.routers.reports import router as reports_router
from app.routers.policies import router as policies_router
from app.routers.proxy import router as proxy_router
from app.routers.review import router as review_router
from app.routers.settings import router as settings_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup/shutdown lifecycle."""
    logger.info("Aigis starting up", version=settings.app_version)

    # Auto-seed demo data if DEMO_MODE is enabled
    if settings.demo_mode:
        try:
            from scripts.seed_demo import seed
            await seed()
        except Exception as exc:
            logger.warning("Demo seed skipped", error=str(exc))

    # Start background tasks
    sla_task = asyncio.create_task(_sla_watcher())
    retention_task = asyncio.create_task(_retention_cleanup())

    yield

    for task in (sla_task, retention_task):
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    logger.info("Aigis shut down")


async def _sla_watcher() -> None:
    """Background task: periodically handle SLA timeouts."""
    from app.db.session import AsyncSessionLocal
    from app.review.service import handle_sla_timeouts

    while True:
        await asyncio.sleep(60)  # check every minute
        try:
            async with AsyncSessionLocal() as db:
                timed_out = await handle_sla_timeouts(db)
                await db.commit()
                if timed_out:
                    logger.warning(
                        "SLA timeouts processed", count=len(timed_out)
                    )
        except Exception as exc:
            logger.error("SLA watcher error", exc_info=exc)


async def _retention_cleanup() -> None:
    """Background task: delete old requests/audit logs beyond plan retention."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import delete, select

    from app.billing.plans import get_plan_limits
    from app.db.session import AsyncSessionLocal
    from app.models.audit import AuditLog
    from app.models.request import Request
    from app.models.tenant import Tenant

    while True:
        # Run once per hour
        await asyncio.sleep(3600)
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Tenant).where(Tenant.is_active == True)
                )
                tenants = result.scalars().all()

                for tenant in tenants:
                    limits = get_plan_limits(tenant.plan)
                    retention_days = limits.get("retention_days")
                    if retention_days is None or retention_days == 0:
                        continue  # unlimited or no cloud storage

                    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

                    # Delete old requests
                    await db.execute(
                        delete(Request).where(
                            Request.tenant_id == tenant.id,
                            Request.created_at < cutoff,
                        )
                    )
                    # Delete old audit logs
                    await db.execute(
                        delete(AuditLog).where(
                            AuditLog.tenant_id == tenant.id,
                            AuditLog.created_at < cutoff,
                        )
                    )

                await db.commit()
                logger.info("Retention cleanup completed", tenant_count=len(tenants))
        except Exception as exc:
            logger.error("Retention cleanup error", exc_info=exc)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI Security Filter SaaS — OpenAI-compatible proxy with "
        "rule-based filtering, risk scoring, and Human-in-the-Loop review."
    ),
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(proxy_router)
app.include_router(review_router)
app.include_router(policies_router)
app.include_router(audit_router)
app.include_router(admin_router)
app.include_router(gandalf_router)
app.include_router(reports_router)
app.include_router(monitor_router)
app.include_router(billing_router)
app.include_router(webhook_router)
app.include_router(settings_router)


@app.get("/health", tags=["health"])
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "version": settings.app_version})
