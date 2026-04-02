# Docker Compose Deployment

This project now includes a production-oriented Docker Compose stack.

## Services

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

## Start

```bash
docker compose up -d --build
```

## Check

```bash
docker compose ps
curl http://localhost/          # frontend
curl http://localhost:8000/health
curl http://localhost:7700/health
```

## Stop

```bash
docker compose down
```
