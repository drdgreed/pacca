"""
JWT authentication and password hashing for PACCA.

Security implementation notes:
  - SECRET_KEY is loaded from the environment at runtime — NEVER hardcoded.
    Generate a secure key with: python -c "import secrets; print(secrets.token_hex(32))"
    Set in .env for local development; use a secrets manager in production.

  - bcrypt is used directly (not passlib) for password hashing. bcrypt
    generates a per-password salt automatically and is resistant to
    GPU-based brute-force attacks.

  - JWT tokens expire after TOKEN_EXPIRE_MINUTES (default 30 minutes).
    30 minutes balances security (limits exposure window if a token is
    intercepted) with usability (typical clinical session length).
    Configurable via TOKEN_EXPIRE_MINUTES environment variable.

  - ALGORITHM is HS256 (HMAC-SHA256) — symmetric signing. For a
    multi-service architecture, RS256 (RSA) would be preferred.
    HS256 is appropriate for a single-service deployment.

HIPAA relevance:
  Authentication controls are required by HIPAA Security Rule 164.312(d)
  (Person or Entity Authentication). Token expiry limits the window during
  which a stolen token could be used to access PHI.
"""

import os

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# ── Security constants ────────────────────────────────────────────────────────

# SECRET_KEY must come from the environment.
# Empty string here is a deliberate fail-safe: if no key is set, JWT signing
# will fail immediately rather than silently using an insecure default.
# For local development, set SECRET_KEY in your .env file.
# Generate a secure key: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY: str = os.getenv("SECRET_KEY", "")

# HS256 = HMAC-SHA256 symmetric JWT signing.
ALGORITHM = "HS256"

# Token lifetime in minutes. Configurable via environment.
# Default: 30 minutes (shorter than the original 60 minutes,
# appropriate for a system handling PHI).
TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "30"))

# Tells FastAPI where to direct unauthenticated clients to log in.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/")


# ── Startup validation ────────────────────────────────────────────────────────

def validate_secret_key() -> None:
    """
    Validate that SECRET_KEY is set and has adequate entropy.

    Call this at application startup (in the FastAPI lifespan) to catch
    misconfigured deployments before they serve any requests.

    Raises:
        RuntimeError: If SECRET_KEY is missing or too short to be secure.
    """
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY environment variable is not set. "
            "Generate a secure key with: "
            "python -c \"import secrets; print(secrets.token_hex(32))\" "
            "and set it in your .env file or deployment secrets manager."
        )
    if len(SECRET_KEY) < 32:
        raise RuntimeError(
            f"SECRET_KEY is only {len(SECRET_KEY)} characters. "
            "Minimum 32 characters required for HS256 security. "
            "Generate a secure key with: "
            "python -c \"import secrets; print(secrets.token_hex(32))\""
        )


# ── Password hashing ──────────────────────────────────────────────────────────

def get_password_hash(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    bcrypt generates a unique random salt for each hash automatically,
    so two hashes of the same password will differ. This prevents
    rainbow table attacks.

    Args:
        password: Plaintext password to hash

    Returns:
        bcrypt hash string suitable for database storage
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.

    bcrypt's checkpw is timing-safe — it does not short-circuit on the
    first mismatched character, preventing timing side-channel attacks.

    Args:
        plain_password:  The password the user provided
        hashed_password: The hash stored in the database

    Returns:
        True if the password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        # Malformed hash — treat as mismatch
        return False


# ── JWT token validation ──────────────────────────────────────────────────────

def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    """
    FastAPI dependency that validates a JWT Bearer token.

    Extracts the username from the token's 'sub' claim. Called automatically
    by FastAPI for any route that declares `Depends(verify_token)`.

    Args:
        token: JWT token from the Authorization: Bearer header (injected by FastAPI)

    Returns:
        The authenticated username

    Raises:
        HTTPException(401): If the token is missing, invalid, expired, or
                            has no 'sub' claim
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception
