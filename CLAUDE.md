# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

The app (**Anom-AI-SaaS / Studio**) is built and deployed live on the VPS as `studio-backend` + `studio-worker` (PM2, port 8006). `build-spec.md` was the original MVP spec; the app has since gone through a production-SaaS transformation (Stages 1–3, see `## Architecture` below) that superseded much of it — treat `build-spec.md` as historical background, and this file's `## Architecture` section as the source of truth for current behavior.

## What is being built

An AI-powered image/3D generation studio (stateless MVP, no auth/DB/quota):
1. **Interior/Exterior Design** — room/building photo → styled variants
2. **Product on Model** — product photo → model wearing/using it
3. **Hyper3D** — product photo → 3D model render, via either **BytePlus Hyper3D** or **Tencent Cloud Hunyuan3D** (user-selectable provider)

Backend: FastAPI (Python 3.11) at `studio-app/backend`, port 8006.
Frontend: React 18 + Vite + TailwindCSS at `studio-app/frontend`.
Image gen and BytePlus 3D gen call the BytePlus ModelArk API directly; Tencent 3D gen (Rapid/Pro/AutoRig) calls Tencent Cloud's `hunyuan` service directly via hand-rolled TC3-HMAC-SHA256 signing (no SDK) — no database, no Redis, no auth as of the original MVP. **A production-SaaS transformation (accounts, credits/subscriptions, an async job queue, storage, admin dashboard) is in progress — see the plan history for the current stage.** The frontend also keeps an in-memory (not persisted) session history of both image-gen and 3D-gen results, plus a Gallery tab of static sample outputs.

## Deployment environment (shared VPS — do not disturb other services)

This app is one of several on a single VPS (43.134.107.159, Tencent Cloud, Ubuntu 22.04, PM2-managed). Existing services on this box must not be touched or reconfigured:

| service | port | path |
|---|---|---|
| nebula-api | 8000 | /root/workspace/nebula-app |
| aura-backend | 8002 | /root/workspace/aura-app |
| boost-backend | 8004 | /root/workspace/boost-app |
| **studio-backend (this app)** | **8006** | **/root/workspace/studio-app** |

Shared infra rules:
- PostgreSQL is shared, but this app needs no database (stateless MVP) — do not create one.
- Redis is shared (Boost=DB2, Nebula=DB0, Aura=DB1); this app needs no Redis for MVP.
- Nginx is shared — only *add* a new `location /studio/` block to the existing config, never replace/edit other blocks.
- BytePlus API key is shared with the Boost app: read it from `/root/workspace/boost-app/backend/.env` (`BYTEPLUS_API_KEY`) rather than provisioning a new one.

## Commands

There is no build system yet since no code exists. Once the backend/frontend from the spec are scaffolded, the expected commands (per spec) are:

```bash
# Backend setup (Python 3.11 explicit — never bare python3/pip)
cd studio-app/backend
./setup.sh                                  # creates venv, installs deps, copies .env.example -> .env
venv/bin/python3.11 -m app.main             # run dev server on port 8006

# Backend deploy
pm2 start ecosystem.config.js
pm2 save
netstat -tlnp | grep -E "8000|8002|8004|8006"   # confirm no port conflicts

# Frontend
cd studio-app/frontend
npm install
npm run dev          # Vite dev server
```

Verify against `TEST CASES` (TC-001..TC-015) in build-spec.md before considering backend/frontend work done — these are manual curl/UI checks, not an automated suite.

## Architecture

**As of the production-SaaS transformation (in progress — see `studio-app/today-task.md` and the project's plan history), the backend is a modular package, not flat files.** Backend (`studio-app/backend/app/`):
- `main.py` — FastAPI app entrypoint (run via `python3.11 -m app.main`, port 8006)
- `core/config.py` — settings loaded from `.env` via pydantic-settings
- `api/routes/generation.py` — all current generation endpoints (`/studio/generate-images`, `/studio/generate-3d`, `/studio/animate-3d`, `/studio/styles`, `/studio/health`, `/studio/proxy-model`)
- `services/image_gen.py` — BytePlus Seedream (sync image) calls; 3 variants generated via `asyncio.gather` in parallel
- `services/gen_3d.py` — BytePlus Hyper3D calls: submit async task → poll `GET .../tasks/{task_id}` every 15s until `succeeded`/`failed` (max 1200s)
- `services/gen_3d_tencent.py` — Tencent Cloud Hunyuan3D calls, **hand-rolled TC3-HMAC-SHA256 request signing** (no SDK — the `ai3d.tencentcloudapi.com` service/SDK does not work for international accounts; verified working host is `hunyuan.intl.tencentcloudapi.com`, service `hunyuan`, version `2023-09-01`). Three job types: `generate_3d_tencent` (Rapid job, fast, explicit `ResultFormat`), `generate_3d_tencent_pro` (Pro job, supports up to 3 `MultiViewImages`, no format param but returns both an OBJ bundle and a native GLB — picks the GLB), `animate_3d_tencent` (AutoRigging — converts the source to FBX via the synchronous `Convert3DFormat` action first, since AutoRigging only accepts bare FBX/OBJ, then submits/polls `SubmitAutoRiggingJob`/`DescribeAutoRiggingJob`; output is FBX-only, not browser-previewable). Requires `TENCENT_SECRET_ID`/`TENCENT_SECRET_KEY` in `.env` (returns a 503 with an actionable detail, including the real Tencent error code, if unset or if the call fails).
- `api/routes/generation.py`'s `/generate-3d` dispatches to the right service based on `Generate3DRequest.provider` (`"byteplus_hyper3d"` default, `"tencent_hunyuan3d"`, or `"tencent_hunyuan3d_pro"`); `proxy-model`'s host whitelist covers all providers' CDN domains (`.volces.com`, `.tencentcos.cn`, `.myqcloud.com`)
- `services/prompts.py` — per-niche prompt templates + per-style prompt additions + per-variant angle suffixes (wide/medium/close) that make the 3 parallel generations genuinely different rather than near-duplicates
- `schemas/generation.py` — Pydantic request/response models, including `Generate3DResponse.model_type` (tells the frontend whether a result is GLB-previewable or download-only)

Persistence has landed: `studio_db` (own database on the VPS's shared Postgres server) via SQLAlchemy async + Alembic (`app/db/`, `app/models/` — `User`, `Project`, `AIJob`, `GeneratedImage`, `Notification`, `AuditLog`, `Subscription`). All instant-in-time columns are `timestamptz` (`DateTime(timezone=True)`) — do not add a naive `DateTime` column, asyncpg rejects mixing timezone-aware Python datetimes into a naive column (hit this once, fixed via migration `b5eabc3a89fb`). Auth also landed: `app/core/security.py` (bcrypt password hashing, JWT via `pyjwt`), `app/api/deps.py`'s `get_current_user` dependency (reads the `studio_session` httpOnly cookie), `app/api/routes/auth.py` (`/studio/auth/register|login|logout|me`). Frontend gained `react-router-dom` (`/login`, `/register`, `/` protected via `pages/ProtectedRoute.jsx`) and `AuthContext.jsx`.

**Generation is now an async job queue, not synchronous request/response.** `/generate-images`, `/generate-3d`, `/animate-3d` require a logged-in user, validate input, create an `AIJob` row (`status=pending`, full request payload in `AIJob.input_data` JSONB — *not* passed through Redis, since input images are base64 and can be multi-MB), enqueue via `arq` (`app/workers/queue.py`), and return `202` immediately with the job (`app/schemas/job.py:JobOut`). A separate `studio-worker` PM2 process (`app/workers/generation_worker.py`, `arq app.workers.generation_worker.WorkerSettings`) picks jobs off Redis DB3, calls the *same* unchanged `services/` functions, and writes `GeneratedImage` row(s) + updates `AIJob.status`/`error_message`. Poll `GET /studio/jobs/{id}` (owner-only, 404 not 403 for other users' jobs) until `status` is `completed`/`failed`. `job_timeout=1500s` in `WorkerSettings` (BytePlus Hyper3D alone can poll up to 1200s). Frontend's `api.js:pollJob()` handles the poll loop. `/health`, `/styles`, `/proxy-model` remain public. Still no credit/quota *enforcement* (`User.credits_balance` column exists but isn't checked before a job is created — Stage 2).

**Testing this without real provider calls**: stub the relevant `app.workers.generation_worker.generate_*`/`animate_3d_tencent` function via `unittest.mock.patch` and call the `run_*` worker function directly (bypasses Redis/arq entirely, exercises the real DB-write logic) — this is how the job-queue plumbing was verified end-to-end without spending API credits. For storage/signed-URL testing specifically, point the stubbed result at a local `python3 -m http.server` instead of a real provider URL so `save_from_url`'s actual HTTP download path gets exercised too — never enqueue a real job through the live Redis queue for testing, since the real `studio-worker` PM2 process consumes it and *will* make a real paid API call.

**Stage 2 (SaaS features) has landed**: `app/services/credits.py:CREDIT_COSTS` (image=10, 3d=20, animate=15, tunable) — `check_and_consume_credits` runs inside the same transaction as job creation in `_create_and_enqueue_job` (`app/api/routes/generation.py`), so a request that can't afford a job never creates one (402, no partial state). Simulated subscriptions (`app/api/routes/admin.py`, gated by `app/api/deps.py:require_admin`) — no real Stripe yet, an admin sets `role`/`credits_balance`/`plan` directly via `PATCH /studio/admin/users/{id}`; also `GET /studio/admin/jobs` and `GET /studio/admin/stats` (users/jobs/credits aggregates — this doubles as basic BI). `app/api/routes/projects.py` (basic CRUD, `Project.user_id`-scoped) and `app/api/routes/account.py` (`GET /studio/me/account` — user + subscription combined) round out the user-facing side. `GET /studio/jobs` (no id) lists the current user's job history — the frontend's History tab is now backed by this (real DB-backed, persists across reloads) instead of in-memory session state; `App.jsx`'s `historyJobs`/`refreshHistory()` fetch+flatten completed jobs' `results[]` into the same flat shape `HistoryPanel` already expected, so nothing else about that component changed. Frontend gained `/account` and `/admin` routes (`pages/Account.jsx`, `pages/Admin.jsx`, `pages/AdminRoute.jsx` — client-side role gate, server-side `require_admin` is the actual enforcement).

**Testing gotcha hit twice this stage, now standard practice**: any test that calls the real `/generate-images`/`/generate-3d`/`/animate-3d` endpoints (even incidentally, e.g. testing credit deduction) enqueues into the *real* shared Redis queue that the live `studio-worker` consumes — it will make a real paid provider call. Always launch a throwaway test server with `REDIS_URL=redis://127.0.0.1:6379/15` (or any DB index no worker listens on) so accidentally-created jobs just sit there harmlessly instead of being processed. Also: when testing admin actions (`PATCH /studio/admin/users/{id}`), use a dedicated test account, never a real user found via `GET /studio/admin/users` — hit this too (accidentally changed a real user's plan/credits mid-test, had to revert via direct SQL).

Storage has landed: `app/services/storage.py:StorageService` downloads each provider result once (worker-side) and persists it to local disk (`STORAGE_PATH`, default `./storage`, layout `{user_id}/{job_id}/{filename}`) — fixes Tencent's ~24h URL expiry as a side effect. `GeneratedImage.file_path`/`.preview_url` store the *relative* path only; `GET /studio/jobs/{id}` signs fresh URLs on every response via `app/core/security.py:sign_file_path`/`verify_file_signature` (HMAC-SHA256 over path+expiry, `FILE_URL_EXPIRY_SECONDS`=24h) — **not** session-cookie auth, because `<model-viewer>`'s internal `fetch()` and plain `<img>`/`<a>` tags don't reliably send cookies cross-origin. `GET /studio/files/{user_id}/{job_id}/{filename}?exp=...&sig=...` (`app/api/routes/files.py`) validates the signature instead. The old `/studio/proxy-model` CORS-bypass route and frontend `proxyModelUrl()` are gone — no longer needed now that results are served from our own origin. `PUBLIC_BASE_URL` (used to build these signed URLs) **must be genuinely reachable from Tencent's servers, not just the browser**, for the AutoRig flow specifically (it hands a stored model URL back to Tencent's `Convert3DFormat` action) — fine on the real VPS with a public IP/domain, but this exact path can't be exercised from a sandbox with no public endpoint.

**Stage 3 (business operations) has landed**: `app/services/email.py:send_email` — best-effort transactional email via the Resend API (`RESEND_API_KEY`; empty/unset in `.env` by default since a real key was never provisioned — sends simply no-op and log a warning rather than raising, so email is never on the critical path of any user-facing flow). Template functions for verification, password reset, job-completed, and low-credit-warning emails. Auth gained `POST /studio/auth/verify-email`, `/forgot-password` (deliberately returns the same response whether or not the email exists — no email-enumeration), and `/reset-password`, all using `app/core/security.py:create_action_token`/`decode_action_token` (short-lived, action-scoped JWTs distinct from the session cookie JWT). `User.email_verified` (migration `add user email_verified`, `server_default=sa.false()` — needed because the column was added NOT NULL against a table with existing real rows). `app/services/notifications.py:create_notification` writes `Notification` rows for job-completed and low-credit-warning events (`app/workers/generation_worker.py`'s `_mark_completed`/`_mark_failed`, and `_create_and_enqueue_job`'s low-credit check) — surfaced via `GET/PATCH /studio/notifications` and the frontend's `components/NotificationBell.jsx` (30s poll, unread badge, click-outside-to-close). `AuditLog` rows now also cover registration, login, email verification, password reset, and admin user edits (`user_id` is nullable with `ondelete=SET NULL` so the log survives user deletion), viewable via `GET /studio/admin/audit-logs`. `GET /studio/admin/stats` expanded: `active_users_7d`, `new_registrations_7d`, `users_by_plan`, `jobs_by_status`/`jobs_by_type`, `queue_depth`, `failure_rate`, `avg_generation_seconds` (via `func.extract("epoch", completed_at - created_at)`), `total_credits_consumed` — `pages/Admin.jsx` renders these as three stat-tile groups (Users/AI Usage/System) plus Users/Recent-Jobs/Audit-Log tables. Frontend gained `/verify-email`, `/forgot-password`, `/reset-password` routes.

**Testing gotcha for Stage 3 specifically**: notification/email code paths were verified two ways — real calls for anything that doesn't touch a paid provider (registration → verification email, low-credit-warning notification triggered by a real `check_and_consume_credits` call), and `unittest.mock.patch` stubs for anything that would otherwise enqueue a real generation job (job-completed notification/email), following the same "never let a test reach the real Redis queue or a paid provider" rule as Stage 1/2.

Frontend (`studio-app/frontend/src/`):
- `api.js` — all backend calls in one place, `credentials: "include"` on every request, plus `pollJob()` helper
- `components/` — `NichePicker`, `StylePicker` (options fetched from `GET /studio/styles`), `ImageUploader` (base64-encodes via `FileReader`, supports native `<input type="file" capture="environment">` for mobile camera — no library needed), `PromptInput`, `GenerateButton`, `ResultsGrid`, `ImageCard`, `ThreeDViewer` (uses `<model-viewer>` web component for `.glb`), `ProviderPicker` (BytePlus Hyper3D vs. Tencent Hunyuan3D, for the 3D-gen section), `HistoryPanel` (renders `App.jsx`'s `historyJobs`, DB-backed via `GET /studio/jobs` and `refreshHistory()` — persists across reloads, replaced the original session-only in-memory version in Stage 2), `NotificationBell` (Stage 3)
- `pages/` — `Login`, `Register`, `Account`, `Admin`, `VerifyEmail`, `ForgotPassword`, `ResetPassword`, `ProtectedRoute`, `AdminRoute`

### Critical backend conventions (from prior-app postmortems — apply to every file)
- Python 3.11 explicit everywhere in `setup.sh`: `python3.11 -m pip`, `python3.11 main.py` — never bare `python3`/`pip`.
- Every `HTTPException` must carry a specific, actionable `detail` string (e.g. `"Seedream image generation failed. Please retry."`) — never a generic `"Error"`.
- Every BytePlus HTTP call is wrapped in try/except with full error logging: `logger.error(f"[BytePlus] HTTP {status}: {body[:500]}")`.
- `.env.example` must match what `setup.sh` actually writes/expects, exactly.
- `ecosystem.config.js` `cwd` must use a variable, never a hardcoded absolute path.
- Frontend errors are shown inline in the UI — never `alert()`.

### BytePlus API quirks (verified, easy to get wrong)
- Image gen (Seedream) is **synchronous**: `POST /api/v3/images/generations` returns the result immediately; `image` field is an **array** of data-URI strings; `size` must be the literal string `"2K"` or `"4K"` (not pixel dimensions).
- 3D gen (Hyper3D) is **asynchronous**: submit a task, then poll for status — do not assume a sync response. Confirm the exact endpoint/model ID against the BytePlus console/docs before coding, per the spec's warning.
- Minimum input image size is 14x14px; validate and reject smaller images with the specific 400 message listed in the spec.
