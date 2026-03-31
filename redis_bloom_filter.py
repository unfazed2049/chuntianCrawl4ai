"""Redis Bloom filter helpers for detail-page recrawl control."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


def normalize_urls(urls: list[str]) -> list[str]:
    """Remove blanks and duplicates while preserving order."""
    seen: set[str] = set()
    normalized: list[str] = []
    for url in urls:
        candidate = (url or "").strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return normalized


def url_fingerprint(url: str) -> str:
    """Generate stable compact fingerprint for URL."""
    return hashlib.md5(url.encode("utf-8")).hexdigest()


@dataclass
class RedisBloomDetailFilter:
    """Use RedisBloom to skip already-crawled detail URLs."""

    client: Any
    key: str
    error_rate: float = 0.001
    capacity: int = 100_000
    _initialized: bool = field(default=False, init=False)

    def _ensure_filter(self):
        if self._initialized:
            return
        try:
            self.client.execute_command(
                "BF.RESERVE", self.key, self.error_rate, self.capacity
            )
        except Exception as exc:  # pragma: no cover - depends on Redis response text
            if "exists" not in str(exc).lower():
                raise
        self._initialized = True

    def filter_new_urls(self, urls: list[str]) -> list[str]:
        candidates = normalize_urls(urls)
        if not candidates:
            return []

        self._ensure_filter()
        fingerprints = [url_fingerprint(url) for url in candidates]
        exists = self.client.execute_command("BF.MEXISTS", self.key, *fingerprints)
        return [url for url, flag in zip(candidates, exists) if int(flag) == 0]

    def mark_crawled(self, urls: list[str]):
        candidates = normalize_urls(urls)
        if not candidates:
            return

        self._ensure_filter()
        fingerprints = [url_fingerprint(url) for url in candidates]
        self.client.execute_command("BF.MADD", self.key, *fingerprints)


def create_detail_filter(
    cfg: dict | None,
    workspace: str,
    site_name: str,
    section_name: str,
) -> RedisBloomDetailFilter | None:
    if not cfg or not cfg.get("enabled", False):
        return None

    try:
        import redis  # type: ignore
    except ImportError:
        print("  [警告] redis 包未安装，跳过 Redis Bloom 过滤")
        return None

    host = cfg.get("host", "127.0.0.1")
    port = int(cfg.get("port", 6379))
    db = int(cfg.get("db", 0))
    password = cfg.get("password")
    timeout = float(cfg.get("socket_timeout", 3))

    key_prefix = cfg.get("key_prefix", "crawl:detail")
    key = cfg.get("key") or ":".join(
        [
            key_prefix,
            workspace,
            site_name.strip().replace(" ", "_"),
            section_name.strip().replace(" ", "_"),
        ]
    )

    error_rate = float(cfg.get("error_rate", 0.001))
    capacity = int(cfg.get("capacity", 100_000))

    try:
        client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            socket_timeout=timeout,
        )
        client.ping()
    except Exception as exc:  # pragma: no cover - depends on runtime env
        print(f"  [警告] Redis 不可用，跳过 Redis Bloom 过滤: {exc}")
        return None

    return RedisBloomDetailFilter(
        client=client,
        key=key,
        error_rate=error_rate,
        capacity=capacity,
    )
