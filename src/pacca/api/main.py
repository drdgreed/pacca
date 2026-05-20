"""
PACCA FastAPI application — v2.2.0

Application startup, middleware configuration, and core auth endpoints.

Architecture notes:
  - All database operations use the async session from db/session.py.
    The legacy sync session from api/database.py is retained only for
    table creation at startup (SQLAlchemy Base.metadata.create_all).
    All route handlers are fully async.

  - JWT authentication uses SECRET_KEY loaded from the environment.
    The application validates SECRET_KEY at startup and refuses to start
    if it is missing or too short (< 32 characters).

  - OpenTelemetry is configured at startup via the lifespan context manager.
    Spans are exported to OTEL_ENDPOINT if set, otherwise printed to console.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import select

# Observability
from ..config.settings import get_settings
from ..config.tracing import configure_tracing

# Production async database session — all route handlers use this
from ..db.session import AsyncSession, get_session, init_database

# Auth helpers — SECRET_KEY, ALGORITHM, and token expiry come from environment
from .auth import (
    ALGORITHM,
    SECRET_KEY,
    TOKEN_EXPIRE_MINUTES,
    get_password_hash,
    validate_secret_key,
    verify_password,
    verify_token,
)

# Legacy sync setup — used ONLY for Base.metadata.create_all at startup
# All runtime database operations use the async session below
from .database import Base
from .database import engine as sync_engine
from .models import User as SyncUser  # SQLAlchemy model for the users table

# Route modules
from .routes import admin, authorizations

# =============================================================================
# Application lifespan — startup and shutdown
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan — runs startup logic before serving requests.

    Startup sequence:
      1. Validate SECRET_KEY (fail fast if misconfigured)
      2. Configure OpenTelemetry tracing
      3. Initialize database tables (both sync User table and async PACCA tables)

    Teaching note: failing fast on misconfiguration is a production discipline.
    Better to crash at startup with a clear error than to serve requests with
    a broken security configuration and discover it during an audit.
    """
    # ── 1. Security validation ────────────────────────────────────────────────
    # This raises RuntimeError if SECRET_KEY is missing or too short.
    # In development, this means you MUST have SECRET_KEY set in your .env file.
    # In production, this catches deployment misconfiguration before any
    # requests are served.
    #
    # Note: we skip validation if SECRET_KEY is the test sentinel value,
    # allowing unit tests to run without a real key.
    settings = get_settings()
    if settings.app_env != "test":
        validate_secret_key()

    # ── 2. OpenTelemetry ──────────────────────────────────────────────────────
    configure_tracing(
        service_name=settings.otel_service_name,
        endpoint=settings.otel_endpoint,
        enabled=settings.otel_enabled,
    )

    # ── 3. Database initialization ────────────────────────────────────────────
    # Create the User table (sync schema, managed by api/models.py + api/database.py)
    # This is the legacy auth table — only the User model lives here.
    # All other PACCA tables are managed by db/models.py via the async engine.
    Base.metadata.create_all(bind=sync_engine)

    # Initialize the PACCA data tables via the async engine
    # (authorization_requests, authorization_decisions, audit_logs, etc.)
    await init_database()

    yield  # Server is running

    # Shutdown: close async database connections
    from ..db.session import close_database

    await close_database()


# =============================================================================
# FastAPI application
# =============================================================================

app = FastAPI(
    title="PACCA — Prior Authorization & Care Coordination Agent Platform",
    version="2.2.0",
    description=(
        "Multi-agent AI system for healthcare prior authorization. "
        "Features: hierarchical escalation tree, dual-collection RAG, "
        "HIPAA-compliant audit trail, OpenTelemetry observability, "
        "and governed policy evolution (Level 5 architecture)."
    ),
    lifespan=lifespan,
)

# ── CORS middleware ───────────────────────────────────────────────────────────
# In production, replace allow_origins=["*"] with explicit frontend origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route registration ────────────────────────────────────────────────────────
app.include_router(
    authorizations.router,
    prefix="/api/v1/authorizations",
    dependencies=[Depends(verify_token)],
    tags=["Authorizations"],
)
app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    dependencies=[Depends(verify_token)],
    tags=["Admin — Configuration & Operations"],
)


# =============================================================================
# User registration and login — async database operations
#
# Teaching note — why these routes are here, not in a dedicated route module:
#   These are the only routes that touch the User table (the legacy sync
#   SQLAlchemy model in api/models.py). Keeping them in main.py avoids
#   creating a route module that mixes the legacy and production database
#   sessions. Week 6 consolidation note: a full migration would move User
#   to the async db/models.py schema. That is the production next step.
# =============================================================================


class UserCreate(BaseModel):
    """Request body for user registration."""

    username: str
    password: str


class LoginRequest(BaseModel):
    """Request body for login."""

    username: str
    password: str


@app.post(
    "/api/v1/register/",
    summary="Register a new provider account",
    tags=["Authentication"],
)
async def register_user(
    user: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Register a new user account.

    Checks for duplicate usernames and hashes the password with bcrypt
    before storage. The hash is salted — two identical passwords produce
    different hashes.

    Args:
        user:    Username and plaintext password
        session: Async database session (injected by FastAPI)
    """
    # Check if username already exists — async query
    result = await session.execute(select(SyncUser).where(SyncUser.username == user.username))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    hashed_password = get_password_hash(user.password)
    new_user = SyncUser(username=user.username, hashed_password=hashed_password)
    session.add(new_user)
    # session is committed automatically when the request ends (get_session handles this)

    return {"message": "User created successfully. You can now log in."}


@app.post(
    "/api/v1/login/",
    summary="Authenticate and receive a JWT token",
    tags=["Authentication"],
)
async def login(
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Authenticate a user and return a JWT Bearer token.

    The token expires after TOKEN_EXPIRE_MINUTES (default 30 minutes).
    Include it in subsequent requests as: Authorization: Bearer <token>

    Args:
        credentials: Username and plaintext password
        session:     Async database session (injected by FastAPI)

    Returns:
        access_token and token_type for use in Authorization header

    Raises:
        HTTPException(401): If credentials are invalid
    """
    # Look up user — async query
    result = await session.execute(
        select(SyncUser).where(SyncUser.username == credentials.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Build JWT with expiry
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": user.username, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return {"access_token": access_token, "token_type": "bearer"}


# =============================================================================
# Health check
# =============================================================================


@app.get("/health", tags=["Operations"], summary="Service health check")
async def health():
    """
    Simple health check endpoint.

    Returns 200 OK when the service is running.
    Used by Docker healthcheck and load balancers.
    """
    return {"status": "ok", "version": app.version}
