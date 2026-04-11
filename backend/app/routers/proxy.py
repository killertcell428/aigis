"""Proxy router: OpenAI-compatible proxy endpoint + dashboard test endpoint."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.enforcement import check_request_quota
from app.config import settings
from app.db.session import get_db
from app.dependencies import get_current_user, resolve_tenant_from_api_key
from app.models.tenant import Tenant
from app.models.user import User
from app.proxy.handler import handle_proxy_request

router = APIRouter(prefix="/api/v1/proxy", tags=["proxy"])


@router.post("/chat/completions")
async def proxy_chat_completions(
    request: Request,
    tenant_user: Annotated[tuple[Tenant, User], Depends(resolve_tenant_from_api_key)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """OpenAI-compatible chat completions proxy.

    Drop-in replacement for `POST /v1/chat/completions`.
    All requests are filtered before being forwarded to the upstream LLM.
    """
    tenant, user = tenant_user
    body: dict[str, Any] = await request.json()
    client_ip = request.client.host if request.client else None

    # Check request quota before forwarding
    await check_request_quota(tenant, db)

    response_body, status_code = await handle_proxy_request(
        db=db,
        tenant=tenant,
        request_body=body,
        client_ip=client_ip,
        upstream_api_key=settings.openai_api_key,
    )
    return JSONResponse(content=response_body, status_code=status_code)


@router.post("/test")
async def test_proxy(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """Dashboard test endpoint — send a prompt through the full proxy flow.

    Uses JWT auth (dashboard login) instead of API key auth.
    This allows the Playground page to test prompts without needing an API key.
    """
    body: dict[str, Any] = await request.json()
    client_ip = request.client.host if request.client else None

    # Resolve tenant from user
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        return JSONResponse(
            content={"error": {"message": "Tenant not found"}},
            status_code=403,
        )

    response_body, status_code = await handle_proxy_request(
        db=db,
        tenant=tenant,
        request_body=body,
        client_ip=client_ip,
        upstream_api_key=settings.openai_api_key,
    )
    return JSONResponse(content=response_body, status_code=status_code)
