"""Admin router: tenant, user, and API key management."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_keys import generate_api_key
from app.auth.jwt import create_access_token, hash_password, verify_password
from app.billing.enforcement import check_user_limit
from app.db.session import get_db
from app.dependencies import get_admin_user, get_current_user
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class TenantCreateRequest(BaseModel):
    name: str
    slug: str


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "reviewer"  # admin | reviewer


class UserResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ApiKeyResponse(BaseModel):
    api_key: str  # Only shown once
    message: str = "Store this key securely — it will not be shown again."


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@router.post("/auth/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate a user and return a JWT access token."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    token = create_access_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )
    return TokenResponse(access_token=token)


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Return the currently authenticated user."""
    return current_user


# ---------------------------------------------------------------------------
# Tenant endpoints (super-admin only in production; simplified for MVP)
# ---------------------------------------------------------------------------
@router.post("/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant(
    body: TenantCreateRequest,
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Tenant:
    """Create a new tenant. Restricted to super-admin users.

    Only users with role=="superadmin" may create additional tenants.
    """
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super-admin role required")

    result = await db.execute(select(Tenant).where(Tenant.slug == body.slug))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tenant slug already exists")

    tenant = Tenant(id=uuid.uuid4(), name=body.name, slug=body.slug)
    db.add(tenant)
    await db.flush()
    return tenant


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if current_user.tenant_id != tenant.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return tenant


# ---------------------------------------------------------------------------
# User endpoints
# ---------------------------------------------------------------------------
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_admin_user)] = None,
) -> User:
    """Create a user within the admin's tenant."""
    # Check team member limit
    if current_user:
        tenant = await db.get(Tenant, current_user.tenant_id)
        if tenant:
            await check_user_limit(tenant, db)

    # For MVP bootstrap, allow user creation without auth if no admin exists yet
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    tenant_id = current_user.tenant_id if current_user else None
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="tenant_id required")

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    await db.flush()
    return user


@router.post("/users/bootstrap", response_model=UserResponse, status_code=201)
async def bootstrap_admin_user(
    body: UserCreateRequest,
    tenant_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Bootstrap the first admin user for a tenant (no auth required).

    Should be disabled in production after initial setup.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role="admin",
    )
    db.add(user)
    await db.flush()
    return user


# ---------------------------------------------------------------------------
# API Key endpoints
# ---------------------------------------------------------------------------
@router.post("/api-keys/generate", response_model=ApiKeyResponse)
async def generate_user_api_key(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiKeyResponse:
    """Generate a new API key for the authenticated user.

    The raw key is returned once and cannot be retrieved again.
    """
    raw_key, key_hash = generate_api_key()
    current_user.api_key_hash = key_hash
    db.add(current_user)
    return ApiKeyResponse(api_key=raw_key)
