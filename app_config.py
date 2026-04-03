import os
import json
from pathlib import Path


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_env_file(path: Path):
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_json_dict(value: str | None) -> dict[str, str]:
    if not value:
        return {}

    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return {}

    if not isinstance(payload, dict):
        return {}

    result: dict[str, str] = {}
    for key, raw in payload.items():
        if not isinstance(key, str) or not isinstance(raw, str):
            continue
        cleaned = raw.strip()
        if cleaned:
            result[key.strip()] = cleaned
    return result


def load_app_config(env_file: str = ".env", skip_dotenv: bool = False) -> dict:
    if not skip_dotenv:
        _load_env_file(Path(env_file))

    llm_provider = os.getenv("LLM_PROVIDER", "").strip()
    llm_api_token = os.getenv("LLM_API_TOKEN", "").strip()
    llm_base_url = os.getenv("LLM_BASE_URL", "").strip() or None

    if not llm_provider or not llm_api_token:
        raise ValueError("LLM_PROVIDER and LLM_API_TOKEN are required in .env")

    llm_config = {
        "provider": llm_provider,
        "api_token": llm_api_token,
    }
    if llm_base_url:
        llm_config["base_url"] = llm_base_url

    redis_bloom_config = {
        "enabled": _to_bool(os.getenv("REDIS_BLOOM_ENABLED"), default=False),
        "host": os.getenv("REDIS_HOST", "127.0.0.1"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "db": int(os.getenv("REDIS_DB", "0")),
        "password": os.getenv("REDIS_PASSWORD") or None,
        "key_prefix": os.getenv("REDIS_BLOOM_KEY_PREFIX", "crawl:detail"),
        "error_rate": float(os.getenv("REDIS_BLOOM_ERROR_RATE", "0.001")),
        "capacity": int(os.getenv("REDIS_BLOOM_CAPACITY", "100000")),
        "socket_timeout": float(os.getenv("REDIS_SOCKET_TIMEOUT", "3")),
    }

    meili_url = os.getenv("MEILI_URL", "").strip()
    meili_api_key = os.getenv("MEILI_API_KEY", "").strip()
    meilisearch_config: dict = {
        "url": meili_url,
        "api_key": meili_api_key,
    }

    meili_hybrid_enabled = _to_bool(os.getenv("MEILI_HYBRID_ENABLED"), default=False)
    if meili_hybrid_enabled:
        document_templates = _parse_json_dict(
            os.getenv("MEILI_HYBRID_DOCUMENT_TEMPLATES")
        )
        meilisearch_config["hybrid_search"] = {
            "enabled": True,
            "embedder_name": os.getenv("MEILI_HYBRID_EMBEDDER_NAME", "openai-emb"),
            "endpoint": os.getenv(
                "MEILI_HYBRID_ENDPOINT", "https://api.openai.com/v1/embeddings"
            ),
            "api_key": os.getenv("MEILI_HYBRID_API_KEY", "").strip(),
            "model": os.getenv("MEILI_HYBRID_MODEL", "text-embedding-3-small"),
            "dimensions": int(os.getenv("MEILI_HYBRID_DIMENSIONS", "1536")),
            "indexes": _split_csv(os.getenv("MEILI_HYBRID_INDEXES"))
            or ["industry_news", "competitor_news", "trade_shows"],
            "document_template": os.getenv(
                "MEILI_HYBRID_DOCUMENT_TEMPLATE",
                "{{doc.title}}\n{{doc.summary}}\n{{doc.cleaned_content}}",
            ),
            "document_templates": document_templates,
        }

    return {
        "llm_config": llm_config,
        "redis_bloom_config": redis_bloom_config,
        "meilisearch_config": meilisearch_config,
    }
