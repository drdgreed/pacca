# SME Case Authoring Web UI — Deployment Guide

> Audience: PACCA platform engineers responsible for production deployment.

This doc covers the production-deployment story for the SME Case Authoring Web UI (PR #13–#17). For developer workstation usage, see [`SME_CASE_AGENT_USER_MANUAL.md` § 11](./SME_CASE_AGENT_USER_MANUAL.md#11-the-web-ui).

---

## Topology

```
                ┌────────────────────────┐
   browser ──→  │  nginx / CloudFront    │  TLS termination + static SPA
                └───────────┬────────────┘
                            │  /api/v1/* + /api/v1/sme-authoring/* + /ws
                            ▼
                ┌────────────────────────┐
                │  FastAPI (uvicorn)     │  Backend on port 8000
                │  pacca.api.main:app    │
                └───────────┬────────────┘
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
         PostgreSQL     Redis        Anthropic API
```

Single deployment artifact:
- Build the React SPA → `frontend/dist/`
- Serve `frontend/dist/` from your edge (nginx, CloudFront, Vercel, etc.)
- Proxy `/api/*` and `/api/v1/sme-authoring/*/draft-stream` (WebSocket) to the FastAPI backend

---

## Environment variables — required for production

| Variable | Required | Example | Notes |
|---|---|---|---|
| `APP_ENV` | yes | `production` | Strict CSP + HSTS only enabled when `!= "development"` |
| `SECRET_KEY` | yes | (32+ chars random) | JWT signing key. App refuses to start if < 32 chars |
| `ANTHROPIC_API_KEY` | yes | `sk-ant-...` | LLM agent calls |
| `CORS_ORIGINS` | yes | `https://sme.example.com` | Comma-separated. **`*` is rejected** in non-development environments |
| `DATABASE_URL` | yes | `postgresql+asyncpg://...` | SQLite default is for dev only |
| `REDIS_URL` | optional | `redis://...` | Required if you enable session affinity |
| `VITE_VERSION` | optional | `v1.1.0` | Renders in the editorial footer |
| `OTEL_ENDPOINT` | optional | `https://otel.example.com` | If unset, spans print to console |

CLAUDE.md rules that bite in production:
- `.env` must **not contain inline comments** — they break Pydantic settings parsing.
- `CORS_ORIGINS` must be a comma-separated string of full origins (`https://app.example.com`), not a JSON array.

---

## Security headers

The `SecurityHeadersMiddleware` (`src/pacca/api/middleware/security_headers.py`) adds these on every response:

| Header | Value | Purpose |
|---|---|---|
| `Content-Security-Policy` | strict allowlist | Blocks third-party scripts / fonts not in the policy |
| `X-Frame-Options` | `DENY` | Clickjacking protection |
| `X-Content-Type-Options` | `nosniff` | MIME-sniffing protection |
| `Referrer-Policy` | `same-origin` | Never leaks SME-authoring URLs to third parties |
| `Permissions-Policy` | camera / mic / geo disabled | Surface needs none of these |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Production only |

The CSP allowlist includes `https://fonts.googleapis.com` (stylesheet) and `https://fonts.gstatic.com` (font files) because the Editorial-Clinical aesthetic loads three Google Fonts. If you self-host the fonts, tighten the policy by removing those hosts from `_PROD_CSP` in `security_headers.py`.

If a new vendor dependency is added (e.g., a chart library that loads from a CDN), the CSP **will block it** and the failure will appear in the browser console. That's the intended behavior — add the host explicitly to the policy and ship a follow-up deployment.

---

## Build + deploy steps

### 1. Build the frontend bundle

```bash
make sme-author-web-build
# or:
cd frontend && npm install && npm run build
```

Produces `frontend/dist/` (gitignored). Bundle size at v1.1: ~250 KB JS (~75 KB gzipped) + 32 KB CSS (~6.5 KB gzipped).

### 2. Build the backend image

```bash
docker build -t pacca-api:latest .
```

Existing `Dockerfile` builds the FastAPI app; no changes needed for the Web UI surface.

### 3. Serve the static SPA from your edge

**nginx example:**

```nginx
server {
  listen 443 ssl http2;
  server_name sme.example.com;

  ssl_certificate     /etc/ssl/certs/sme.crt;
  ssl_certificate_key /etc/ssl/private/sme.key;

  # Static SPA
  root /srv/pacca-frontend/dist;
  index index.html;

  # SPA fallback — every unknown route → index.html (React Router handles it)
  location / {
    try_files $uri $uri/ /index.html;
  }

  # REST proxy → uvicorn
  location /api/ {
    proxy_pass http://pacca-api:8000/api/;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  # WebSocket proxy — required for the wizard's live drafting stream
  location ~ ^/api/v1/sme-authoring/sessions/.+/draft-stream$ {
    proxy_pass http://pacca-api:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade    $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host       $host;
    proxy_read_timeout 300s;       # LLM drafts can take 5–15s; allow headroom
  }
}
```

**CloudFront example:** route `/api/*` to your ALB/origin; route everything else to the S3 bucket holding `frontend/dist/`. For WebSocket support, the ALB origin must have HTTP/2 + WebSocket enabled.

### 4. Smoke test

```bash
curl -sf https://sme.example.com/api/v1/sme-authoring/status -H "Authorization: Bearer $TOKEN" | jq .
# Should return: {"kind": "status", "total_cases": N, ...}
```

In a browser:
1. Navigate to `https://sme.example.com/sme-author`
2. DevTools → Network: confirm no failed font / script requests (CSP violations show as red rows)
3. DevTools → Application → Local Storage: only `token` key should exist; the wizard never persists case content

---

## HIPAA-relevant considerations

| Concern | Where it's handled |
|---|---|
| PHI in URLs | Wizard state is never serialized to URL; sessions reference by short ID only |
| PHI in localStorage | `safeLogout()` scrubs all unexpected keys at logout; dev-mode warns if any contain PHI patterns |
| PHI in browser history | Story headers carry no PHI; routes are static (`/sme-author/sessions/abc123`) |
| TLS only | HSTS header enforces HTTPS for 1 year once set |
| Audit trail | All commits go through the same `provenance_writer` as CLI commits — no separate audit path |
| CORS | Production-mode wildcard origin is rejected at startup |

---

## Rollback

PR-WUI-1 through PR-WUI-5 are independent of the existing Provider / Director / Admin surfaces. To disable the SME Web UI without redeploying:

1. Remove the `/sme-author/*` nav link from the existing dashboard (App.tsx).
2. (Optionally) remove the `sme_authoring` router include from `main.py`.

The CLI (`pacca sme-author ...`) continues to work independently — same backend modules, no shared state.

---

## Observability

- OTel spans named `agent.sme_authoring.*` appear alongside the `DecisionSupportAgent` traces.
- WebSocket connections log `connection opened`, `auth ok`, `done`, `closed` events through `structlog`.
- The Web UI surface adds no new metrics — request count + latency are picked up by the existing FastAPI auto-instrumentation.

For per-SME usage analytics, query the `audit_logs` table for actor records with `sme_authoring_*` event types.
