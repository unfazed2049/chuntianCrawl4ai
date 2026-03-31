# Meilisearch Indexing Flow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a post-crawl batch indexing flow that reads saved JSON sidecar files and writes to Meilisearch indices.

**Architecture:** During crawl, each page saves a `.json` sidecar (meta + extracted + raw_content) alongside the existing `.md`. After all crawls finish, `index_workspace_flow` scans those JSON files and routes each to the correct Meilisearch index based on `data_type`.

**Tech Stack:** `meilisearch` 0.40.0 (already installed), Prefect 3.x, Python 3.12

---

## Data Type → Meilisearch Index Routing

| `data_type` | Meilisearch index | Notes |
|---|---|---|
| `products` / `cases` / `solutions` / `technologies` | `competitor_profiles` | aggregated upsert per competitor |
| `news` (site has `competitor_id`) | `competitor_news` | one doc per URL |
| `industry_news` | `industry_news` | one doc per URL |
| `trade_show` | `trade_shows` | one doc per URL |
| `None` / unknown | skip | no index written |

## JSON Sidecar Format

```
output/{workspace}/{date}/{site}/{section}/{slug}.json
```

```json
{
  "meta": {
    "workspace": "default",
    "site_name": "Hiperbaric",
    "competitor_id": "hiperbaric",
    "section_name": "产品中心",
    "data_type": "products",
    "url": "https://...",
    "crawled_at": "2026-03-30T12:00:00+00:00"
  },
  "extracted": { "...LLM fields..." },
  "raw_content": "markdown string"
}
```

## Meilisearch Config in workspace JSON

```json
{
  "meilisearch_config": {
    "url": "http://localhost:7700",
    "api_key": "bT8kB0bK9iK0nF5x"
  }
}
```

---

## Task 1: Add `build_meta` and `save_json_task` to `prefect_tasks.py`

**File:** `prefect_tasks.py`

Add after `save_markdown_task`:

```python
from datetime import datetime, timezone

def build_meta(site: dict, section: dict, workspace: str, url: str) -> dict:
    """构建 JSON sidecar 的 meta 字段"""
    return {
        "workspace": workspace,
        "site_name": site["name"],
        "competitor_id": site.get("competitor_id"),
        "section_name": section["name"],
        "data_type": section.get("data_type"),
        "url": url,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
    }


@task(name="save_json", tags=["io"])
def save_json_task(
    output_dir: Path, slug: str, extracted: dict, raw_content: str, meta: dict
) -> str:
    """将提取结果和元数据保存为 JSON sidecar，供后续 index 使用"""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{slug}.json"
    payload = {"meta": meta, "extracted": extracted, "raw_content": raw_content}
    filepath.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return str(filepath)
```

Add `build_meta` and `save_json_task` to the imports list used by `prefect_flows.py`.

---

## Task 2: Create `meilisearch_tasks.py`

**File:** `meilisearch_tasks.py` (new)

```python
"""
Meilisearch indexing tasks for Prefect
将爬取结果写入 Meilisearch 各 index
"""

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import meilisearch
from prefect import flow, task

from prefect_tasks import DEFAULT_WORKSPACE

COMPETITOR_PROFILE_DTYPES = {"products", "cases", "solutions", "technologies"}


# ─── 工具函数 ────────────────────────────────────────────────────────────────

def get_meili_client(config: dict) -> meilisearch.Client:
    url = config.get("url", "http://localhost:7700")
    api_key = config.get("api_key", "")
    return meilisearch.Client(url, api_key)


def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _safe_summary(extracted: dict) -> str:
    """优先取 summary，fallback 到 content 前 500 字"""
    return (extracted.get("summary") or extracted.get("content", ""))[:500]


# ─── 构建文档 ────────────────────────────────────────────────────────────────

def build_competitor_news_doc(meta: dict, extracted: dict, raw_content: str) -> dict:
    return {
        "id": _url_hash(meta["url"]),
        "workspace": meta["workspace"],
        "competitor_id": meta["competitor_id"],
        "competitor_name": meta["site_name"],
        "category": extracted.get("category", "公司动态"),
        "title": extracted.get("title", ""),
        "summary": _safe_summary(extracted),
        "url": meta["url"],
        "published_at": extracted.get("date") or extracted.get("published_at", ""),
        "crawled_at": meta["crawled_at"],
        "source_section": meta["section_name"],
        "tags": extracted.get("tags", []),
        "raw_content": raw_content,
    }


def build_industry_news_doc(meta: dict, extracted: dict, raw_content: str) -> dict:
    return {
        "id": _url_hash(meta["url"]),
        "workspace": meta["workspace"],
        "title": extracted.get("title", ""),
        "summary": _safe_summary(extracted),
        "url": meta["url"],
        "published_at": extracted.get("date") or extracted.get("published_at", ""),
        "crawled_at": meta["crawled_at"],
        "category": extracted.get("category", "行业资讯"),
        "tags": extracted.get("tags", []),
        "raw_content": raw_content,
    }


def build_trade_show_doc(meta: dict, extracted: dict, raw_content: str) -> dict:
    name = extracted.get("name", "")
    year = extracted.get("year") or datetime.now().year
    doc_id = _url_hash(f"{name}{year}")
    return {
        "id": doc_id,
        "workspace": meta["workspace"],
        "name": name,
        "year": year,
        "start_date": extracted.get("start_date", ""),
        "end_date": extracted.get("end_date", ""),
        "location": extracted.get("location", ""),
        "organizer": extracted.get("organizer", ""),
        "website": extracted.get("website", ""),
        "crawled_at": meta["crawled_at"],
        "exhibitors": extracted.get("exhibitors", []),
        "new_products": extracted.get("new_products", []),
        "summary": extracted.get("summary", ""),
        "tags": extracted.get("tags", []),
        "raw_content": raw_content,
    }


def build_profile_item(data_type: str, extracted: dict, url: str, raw_content: str) -> dict:
    """将 extracted 包装为 competitor_profiles 子数组项"""
    item = dict(extracted)
    item["source_url"] = url
    item["raw_content"] = raw_content
    return item


# ─── Index Tasks ─────────────────────────────────────────────────────────────

@task(name="index_simple_docs", tags=["index"])
def index_simple_docs_task(client: meilisearch.Client, index_name: str, docs: list[dict]):
    """批量写入简单 index（competitor_news / industry_news / trade_shows）"""
    if not docs:
        return
    idx = client.index(index_name)
    idx.update_documents(docs)
    print(f"  [index] {index_name}: upserted {len(docs)} docs")


@task(name="upsert_competitor_profiles", tags=["index"])
def upsert_competitor_profiles_task(
    client: meilisearch.Client,
    workspace: str,
    profiles: dict,
):
    """
    profiles: {
      competitor_id: {
        "name": str,
        "products": [...],
        "cases": [...],
        "solutions": [...],
        "technologies": [...],
      }
    }
    先 GET 现有 doc，追加新 item（按 source_url 去重），再 upsert。
    """
    if not profiles:
        return

    idx = client.index("competitor_profiles")
    docs_to_upsert = []

    for competitor_id, data in profiles.items():
        doc_id = f"{workspace}_{competitor_id}"

        # 尝试获取现有 doc
        try:
            existing = idx.get_document(doc_id)
            # meilisearch client 返回 dict-like object，转为普通 dict
            existing_doc = dict(existing)
            for dtype in ("products", "cases", "solutions", "technologies"):
                if dtype not in existing_doc:
                    existing_doc[dtype] = []
        except Exception:
            existing_doc = {
                "id": doc_id,
                "workspace": workspace,
                "competitor_id": competitor_id,
                "name": data.get("name", competitor_id),
                "website": "",
                "country": "",
                "products": [],
                "cases": [],
                "solutions": [],
                "technologies": [],
            }

        # 追加新 item，按 source_url 去重
        for dtype in ("products", "cases", "solutions", "technologies"):
            new_items = data.get(dtype, [])
            if not new_items:
                continue
            existing_urls = {item.get("source_url") for item in existing_doc[dtype]}
            for item in new_items:
                if item.get("source_url") not in existing_urls:
                    existing_doc[dtype].append(item)
                    existing_urls.add(item.get("source_url"))

        existing_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        docs_to_upsert.append(existing_doc)

    if docs_to_upsert:
        idx.update_documents(docs_to_upsert)
        print(f"  [index] competitor_profiles: upserted {len(docs_to_upsert)} profiles")


# ─── Index Flow ────────────────��──────────────────────────────────────────────

@flow(name="index_workspace", log_prints=True)
def index_workspace_flow(
    workspace: str = DEFAULT_WORKSPACE,
    date: str | None = None,
    meili_config: dict | None = None,
):
    """
    扫描 output/{workspace}/{date}/ 下所有 .json sidecar，
    按 data_type 写入对应 Meilisearch index。
    date 默认为今天（格式 YYYYMMDD）。
    """
    from datetime import date as date_cls
    from prefect_tasks import OUTPUT_ROOT

    if not meili_config:
        print("  [跳过] 未配置 meilisearch_config，跳过 indexing")
        return

    if date is None:
        date = date_cls.today().strftime("%Y%m%d")

    scan_root = OUTPUT_ROOT / workspace / date
    if not scan_root.exists():
        print(f"  [跳过] 目录不存在: {scan_root}")
        return

    client = get_meili_client(meili_config)

    # 收集各 index 的文档
    competitor_news_docs: list[dict] = []
    industry_news_docs: list[dict] = []
    trade_show_docs: list[dict] = []
    # competitor_profiles: {competitor_id: {name, products, cases, ...}}
    profiles: dict = defaultdict(lambda: {
        "name": "", "products": [], "cases": [], "solutions": [], "technologies": []
    })

    json_files = list(scan_root.rglob("*.json"))
    print(f"  扫描到 {len(json_files)} 个 JSON sidecar 文件")

    for jf in json_files:
        try:
            payload = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [警告] 读取失败 {jf}: {e}")
            continue

        meta = payload.get("meta", {})
        extracted = payload.get("extracted", {})
        raw_content = payload.get("raw_content", "")
        data_type = meta.get("data_type")
        competitor_id = meta.get("competitor_id")

        if data_type in COMPETITOR_PROFILE_DTYPES and competitor_id:
            item = build_profile_item(data_type, extracted, meta["url"], raw_content)
            profiles[competitor_id][data_type].append(item)
            if not profiles[competitor_id]["name"]:
                profiles[competitor_id]["name"] = meta["site_name"]

        elif data_type == "news" and competitor_id:
            competitor_news_docs.append(
                build_competitor_news_doc(meta, extracted, raw_content)
            )

        elif data_type == "industry_news":
            industry_news_docs.append(
                build_industry_news_doc(meta, extracted, raw_content)
            )

        elif data_type == "trade_show":
            trade_show_docs.append(
                build_trade_show_doc(meta, extracted, raw_content)
            )

        else:
            print(f"  [跳过] data_type={data_type!r}, file={jf.name}")

    # 写入 Meilisearch
    index_simple_docs_task(client, "competitor_news", competitor_news_docs)
    index_simple_docs_task(client, "industry_news", industry_news_docs)
    index_simple_docs_task(client, "trade_shows", trade_show_docs)
    upsert_competitor_profiles_task(client, workspace, dict(profiles))

    print(f"\n  Indexing 完成 [workspace={workspace}, date={date}]")
```

---

## Task 3: Update `prefect_flows.py`

### 3a: Add imports

```python
from meilisearch_tasks import index_workspace_flow
from prefect_tasks import (
    ...,  # existing imports
    build_meta,
    save_json_task,
)
```

### 3b: Update `run_list_section_flow` — call `save_json_task` after `save_markdown_task`

In the loop over `results` (after `save_markdown_task` call):

```python
# 现有
filepath = save_markdown_task(output_dir, slug, extracted, fallback)
# 新增
meta = build_meta(site, section, workspace, result["url"])
save_json_task(output_dir, slug, extracted, fallback, meta)
```

### 3c: Update `run_single_section_flow` — same pattern

```python
# 现有
filepath = save_markdown_task(output_dir, slug, extracted, fallback)
# 新增
meta = build_meta(site, section, workspace, url)
save_json_task(output_dir, slug, extracted, fallback, meta)
```

### 3d: Update `crawl_sites_flow` — add indexing after all crawls

```python
@flow(name="crawl_sites", log_prints=True)
async def crawl_sites_flow(
    workspace: str = DEFAULT_WORKSPACE,
    filter_site: str | None = None,
    filter_section: str | None = None,
):
    config = load_config_task(workspace)
    llm_cfg: dict = config.get("llm_config", {})
    meili_cfg: dict | None = config.get("meilisearch_config")   # ← 新增
    ...

    # [现有爬取循环不变]

    print("\n" + "=" * 60)
    print("全部爬取完成，开始 Meilisearch 写入")
    print("=" * 60)

    # 新增：爬完后统一 index
    index_workspace_flow(workspace=workspace, meili_config=meili_cfg)  # ← 新增

    print("\n" + "=" * 60)
    print("全部任务完成")
    print("=" * 60)
```

---

## Task 4: Update `config/example.json` with `meilisearch_config`

```json
{
  "meilisearch_config": {
    "url": "http://localhost:7700",
    "api_key": "bT8kB0bK9iK0nF5x"
  },
  "llm_config": { ... },
  "sites": [ ... ]
}
```

---

## Verification

1. Start Meilisearch: `pixi run meilisearch-serve`
2. Run crawler on example config: `python crawler_prefect.py --workspace=example`
3. Check JSON sidecars exist: `ls output/example/$(date +%Y%m%d)/`
4. Check Meilisearch indices populated:
   ```bash
   curl http://localhost:7700/indexes/competitor_news/documents?limit=5 \
     -H "Authorization: Bearer bT8kB0bK9iK0nF5x"
   ```
5. For competitor_profiles, check aggregation:
   ```bash
   curl http://localhost:7700/indexes/competitor_profiles/documents \
     -H "Authorization: Bearer bT8kB0bK9iK0nF5x"
   ```
