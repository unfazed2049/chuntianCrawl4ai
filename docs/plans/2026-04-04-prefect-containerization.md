# Prefect Full Containerization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Run Prefect server, deployment registration, and worker fully inside Docker Compose so scheduled crawls execute without host-side processes.

**Architecture:** Add three compose services: `prefect-server` (control plane + UI), `prefect-deploy` (one-shot registration of `prefect.yaml` deployments), and `prefect-worker` (process worker consuming `crawler-pool`). Build a dedicated crawler/worker image containing Prefect + crawl dependencies and mount project files so `prefect_flows.py` and `prefect.yaml` are available in-container. Keep Meilisearch/Redis integration over compose network names.

**Tech Stack:** Docker Compose, Prefect 3, Python 3.12, Crawl4ai, Meilisearch, Redis

### Task 1: Add container image for Prefect crawler worker

**Files:**
- Create: `Dockerfile.prefect`

**Step 1: Write the failing test**

Use config validation as acceptance check after integration (Task 3) because Dockerfile behavior is exercised by compose build.

**Step 2: Run test to verify it fails**

Skip for isolated Dockerfile creation; failure asserted in Task 3 via `docker compose config` before service wiring is complete.

**Step 3: Write minimal implementation**

Create `Dockerfile.prefect` with Python 3.12 base, install required apt libs, install Prefect/crawl dependencies with pip, copy project, set `/app` workdir.

**Step 4: Run test to verify it passes**

Run in Task 3 with compose config/build checks.

**Step 5: Commit**

Commit together with compose wiring in Task 3.

### Task 2: Add Prefect settings for container runtime

**Files:**
- Modify: `.env.example`

**Step 1: Write the failing test**

Acceptance criterion: all env vars referenced in compose exist in `.env.example`.

**Step 2: Run test to verify it fails**

Manual diff check after compose edits if variables missing.

**Step 3: Write minimal implementation**

Add `PREFECT_API_URL`, `PREFECT_WORK_POOL`, and optional `PREFECT_SERVER_PORT` defaults for container stack.

**Step 4: Run test to verify it passes**

Confirm each variable exists in `.env.example` and is referenced consistently in compose.

**Step 5: Commit**

Commit with Task 3 and docs updates.

### Task 3: Wire Prefect server/deploy/worker in compose

**Files:**
- Modify: `docker-compose.yml`

**Step 1: Write the failing test**

Run: `docker compose config`
Expected (before changes): stack has no Prefect services to execute schedules.

**Step 2: Run test to verify it fails**

Observe missing `prefect-server` / `prefect-worker` / `prefect-deploy` services.

**Step 3: Write minimal implementation**

Add:
- `prefect-server` with API URL/env and healthcheck
- `prefect-deploy` one-shot service that waits for server then runs `prefect deploy --all`
- `prefect-worker` service targeting pool from env and depending on deploy + backend health

Keep worker env overrides for `MEILI_URL` and `REDIS_HOST` to internal service names.

**Step 4: Run test to verify it passes**

Run: `docker compose config`
Expected: valid compose output containing all three Prefect services.

**Step 5: Commit**

`git add docker-compose.yml Dockerfile.prefect .env.example`

### Task 4: Update deployment documentation

**Files:**
- Modify: `docs/docker-deployment.md`

**Step 1: Write the failing test**

Acceptance criterion: docs mention Prefect UI, deploy, worker behavior, and expected health checks.

**Step 2: Run test to verify it fails**

Current doc lacks Prefect container steps.

**Step 3: Write minimal implementation**

Document new services, startup sequence, verification commands, and re-deploy command when `prefect.yaml` changes.

**Step 4: Run test to verify it passes**

Read doc to confirm operator can run full stack without host Prefect commands.

**Step 5: Commit**

`git add docs/docker-deployment.md`
