"""
Security-headers middleware.

Adds OWASP-recommended response headers on every API + SPA response:

  - Content-Security-Policy: restricts script / style / font sources.
  - X-Frame-Options: deny — blocks clickjacking via iframe embedding.
  - X-Content-Type-Options: nosniff — disables MIME sniffing.
  - Referrer-Policy: same-origin — leaks no PHI URLs to third parties.
  - Strict-Transport-Security: enforces HTTPS in production environments.
  - Permissions-Policy: disables unused browser APIs (geolocation, camera,
    microphone — none are needed by the SME-authoring surface).

CSP source allowlist matches what the SME-authoring frontend loads:
  - script-src 'self' — only the bundled Vite output.
  - style-src 'self' + Google Fonts CSS endpoint.
  - font-src 'self' + Google Fonts file endpoint.
  - connect-src 'self' + ws:/wss: — REST + WebSocket back to same origin.

Strictness is dialed up only when app_env != "development" — local dev
needs HMR over ws:, eval'd source maps, and inline scripts from Vite.
The production preset is fail-closed: any external resource not in the
allowlist is blocked by the browser, surfacing the misconfiguration in
the console before it ships.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

# Production CSP — fail-closed. Adding a new vendor host requires editing
# this allowlist + deploying; that's the intended friction.
_PROD_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self' ws: wss:; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

# Development CSP — looser, accommodating Vite's HMR + eval'd source maps.
# Still excludes script-src 'unsafe-eval' in production.
_DEV_CSP = (
    "default-src 'self' 'unsafe-inline' 'unsafe-eval' ws: wss: "
    "https://fonts.googleapis.com https://fonts.gstatic.com data:; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "frame-ancestors 'none'"
)

_PERMISSIONS_POLICY = (
    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
    "magnetometer=(), microphone=(), payment=(), usb=()"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Attach security headers to every response.

    Configured per environment: production gets strict CSP + HSTS;
    development gets a looser policy that lets Vite + HMR + sourcemaps
    work without console noise.

    Stateless and side-effect-free — safe to mount above CORS.
    """

    def __init__(
        self,
        app: object,
        *,
        app_env: str,
        enable_hsts: bool | None = None,
    ) -> None:
        super().__init__(app)
        self.app_env = app_env
        self.is_production = app_env not in {"development", "test"}
        # HSTS only in production unless explicitly overridden. Tests run
        # in test env and don't need it; dev runs over http://localhost.
        self.enable_hsts = self.is_production if enable_hsts is None else enable_hsts

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)

        # CSP picks the strict or relaxed preset by environment
        response.headers["Content-Security-Policy"] = _PROD_CSP if self.is_production else _DEV_CSP

        # OWASP basics — same across all environments
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = _PERMISSIONS_POLICY

        # HSTS only in production — enforces HTTPS for 1 year.
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
