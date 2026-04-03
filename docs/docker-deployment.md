# Docker Compose Deployment

This project now includes a production-oriented Docker Compose stack.

## Services

- `prefect-server`: Prefect API + UI on port `4200`
- `prefect-deploy`: one-shot service that registers `prefect.yaml` deployments
- `prefect-worker`: runs scheduled/queued crawl flows from Prefect work pool
- `frontend`: Nginx serves built React app on port `80`
- `api`: FastAPI server on port `8000`
- `meilisearch`: search engine on port `7700`
- `redis`: Redis cache on port `6379`

## Prerequisites

1. Copy and edit env file:

```bash
cp .env.example .env
```

2. Ensure required values in `.env` are set, especially:

- `LLM_PROVIDER`
- `LLM_API_TOKEN`
- `MEILI_API_KEY`
- `PREFECT_API_URL`
- `PREFECT_WORK_POOL`

## Start

```bash
docker compose up -d --build
```

## Check

```bash
docker compose ps
curl http://localhost:4200/api/health   # prefect
curl http://localhost/          # frontend
curl http://localhost:8000/health
curl http://localhost:7700/health
```

Verify deployment registration and schedules in Prefect UI:

- Open `http://localhost:4200`
- Check Deployments: `crawl-hpp-12h`, `crawl-hpp-company-daily`
- Check Workers page: one worker online in pool `crawler-pool`

## Re-deploy after changing prefect.yaml

When you edit `prefect.yaml`, re-run deployment registration:

```bash
docker compose run --rm prefect-deploy
```

## Stop

```bash
docker compose down
```
