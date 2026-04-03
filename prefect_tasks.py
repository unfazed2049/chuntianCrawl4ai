"""
Prefect Tasks for Crawl4ai
将爬虫功能拆分为独立的 Prefect tasks
"""

import json
import re
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import litellm
from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    DefaultMarkdownGenerator,
    LLMExtractionStrategy,
    PruningContentFilter,
)
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, LLMConfig
from prefect.cache_policies import NO_CACHE
from prefect import task

from schemas import CRAWL_CONTENT_SCHEMA
from utils import (
    CONFIG_DIR,
    DEFAULT_CONFIG,
    DEFAULT_WORKSPACE,
    OUTPUT_ROOT,
    PROMPTS_DIR,
    load_config,
    load_prompts,
)

FILENAME_ILLEGAL = re.compile(r'[\\/:*?"<>|\r\n\t]')

# 默认配置
DEFAULT_BROWSER_CONFIG = {
    "headless": True,
    "verbose": False,
}

DEFAULT_CRAWLER_CONFIG = {
    "css_selector": None,
    "wait_for": None,
    "js_code_before_wait": None,
    "content_filter_threshold": 0.5,
}


# ─── 配置加载 Tasks ─────────────────────────────────────────────────────────


@task(name="load_prompts", tags=["config"])
def load_prompts_task() -> dict:
    """Load all prompts from prompts/ directory"""
    return load_prompts()


@task(name="load_config", tags=["config"])
def load_config_task(config_name: str = DEFAULT_CONFIG) -> tuple[dict, str]:
    """Load configuration from config/{config_name}.json, returns (config, workspace)"""
    return load_config(config_name)


# ─── 工具函数 Tasks ─────────────────────────────────────────────────────────


def sanitize_filename(name: str, fallback: str = "untitled") -> str:
    name = name.strip()
    name = FILENAME_ILLEGAL.sub("_", name)
    name = name[:100]
    return name or fallback


def slug_from_url(url: str) -> str:
    """使用完整 URL 的哈希值作为 slug，避免同路径不同 query 冲突"""
    value = (url or "").strip()
    if not value:
        return sanitize_filename("", "page")
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def build_output_dir(
    site: dict, section: dict, workspace: str = DEFAULT_WORKSPACE
) -> Path:
    """output/{workspace}/{YYYYMMDD}/{site.name}/{section.name}/"""
    from datetime import date

    today = date.today().strftime("%Y%m%d")
    return (
        OUTPUT_ROOT
        / workspace
        / today
        / sanitize_filename(site["name"])
        / sanitize_filename(section["name"])
    )


def build_browser_config(section_cfg: dict | None) -> BrowserConfig:
    """将 section.browser_config 与默认配置合并后转换为 BrowserConfig"""
    merged = DEFAULT_BROWSER_CONFIG.copy()
    if section_cfg:
        normalized = dict(section_cfg)
        if "stealth" in normalized and "enable_stealth" not in normalized:
            normalized["enable_stealth"] = normalized.pop("stealth")
        else:
            normalized.pop("stealth", None)
        merged.update({k: v for k, v in normalized.items() if v is not None})
    return BrowserConfig(**merged)


def build_llm_strategy(llm_cfg: dict, prompt_cfg: dict) -> LLMExtractionStrategy:
    """根据 llm_config 和 prompt 配置构建 LLMExtractionStrategy"""
    schema = CRAWL_CONTENT_SCHEMA
    if schema and isinstance(schema, dict):
        json_schema = {
            "type": "object",
            "properties": {k: {"type": v} for k, v in schema.items()},
        }
    else:
        json_schema = schema

    return LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider=llm_cfg["provider"],
            api_token=llm_cfg["api_token"],
            base_url=llm_cfg.get("base_url"),
        ),
        schema=json_schema,
        extraction_type="schema",
        instruction=prompt_cfg.get("instruction", ""),
    )


def build_crawler_run_config(
    section_crawler_cfg: dict | None,
    llm_strategy: LLMExtractionStrategy | None = None,
    extra: dict | None = None,
) -> CrawlerRunConfig:
    """构建 CrawlerRunConfig"""
    merged = DEFAULT_CRAWLER_CONFIG.copy()
    if section_crawler_cfg:
        merged.update({k: v for k, v in section_crawler_cfg.items() if v is not None})
    if extra:
        merged.update({k: v for k, v in extra.items() if v is not None})

    threshold = merged.pop("content_filter_threshold", 0.5)

    run_cfg = {
        "cache_mode": CacheMode.BYPASS,
        "markdown_generator": DefaultMarkdownGenerator(
            content_source="cleaned_html",
            content_filter=PruningContentFilter(threshold=threshold),
            options={"ignore_links": True, "ignore_images": False},
        ),
        **merged,
    }
    if llm_strategy is not None:
        run_cfg["extraction_strategy"] = llm_strategy

    return CrawlerRunConfig(**run_cfg)


def parse_extracted(raw: str) -> dict:
    """解析 LLM 返回的 extracted_content JSON"""
    try:
        data = json.loads(raw or "[]")
        if isinstance(data, list) and data:
            return data[0]
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, IndexError):
        pass
    return {}


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


@task(name="clean_markdown_with_llm", tags=["llm", "clean"], cache_policy=NO_CACHE)
def clean_markdown_with_llm_task(
    llm_cfg: dict,
    prompts: dict,
    meta: dict,
    raw_content: str,
) -> str:
    if not raw_content:
        return ""

    prompt_cfg = prompts.get("clean_markdown", {})
    system_prompt = prompt_cfg.get("instruction", "").strip()
    if not system_prompt:
        return raw_content

    user_content = json.dumps(
        {
            "meta": {
                "url": meta.get("url", ""),
                "site_name": meta.get("site_name", ""),
                "section_name": meta.get("section_name", ""),
                "data_type": meta.get("data_type"),
            },
            "raw_content": raw_content,
        },
        ensure_ascii=False,
    )

    try:
        response = litellm.completion(
            model=llm_cfg["provider"],
            api_key=llm_cfg["api_token"],
            api_base=llm_cfg.get("base_url"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0,
        )
        text = response.choices[0].message.content or ""
        cleaned = _strip_markdown_fences(text)
        return cleaned or raw_content
    except Exception as e:
        print(f"  [警告] LLM 清洗失败 [{meta.get('url', '')}]: {e}")
        return raw_content


def filter_links(links: list[dict], pattern: str | None) -> list[str]:
    """从 result.links 过滤出目标 URL"""
    urls = [lk.get("href", "") for lk in links if lk.get("href")]
    if not pattern:
        return list(dict.fromkeys(urls))
    rx = re.compile(pattern)
    return list(dict.fromkeys(u for u in urls if rx.search(u)))


# ─── 保存 Tasks ─────────────────────────────────────────────────────────


@task(name="save_markdown", tags=["io"])
def save_markdown_task(
    output_dir: Path, slug: str, extracted: dict, fallback_content: str
):
    """将提取结果保存为 markdown 文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{slug}.md"

    lines = []
    title = extracted.get("title", "").strip()
    date = extracted.get("date", "").strip()
    content = extracted.get("content_markdown", "").strip() or fallback_content

    if title:
        lines.append(f"# {title}\n")
    if date:
        lines.append(f"日期：{date}\n")
    if title or date:
        lines.append("")
    lines.append(content)

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return str(filepath)


def build_meta(site: dict, section: dict, workspace: str, url: str) -> dict:
    """构建 JSON sidecar 的 meta 字段"""
    return {
        "workspace": workspace,
        "site_name": site["name"],
        "competitor_id": site.get("competitor_id"),
        "section_name": section["name"],
        "data_type": section.get("data_type"),
        "url": url,
        "crawled_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
    }


@task(name="save_json", tags=["io"])
def save_json_task(
    output_dir: Path, slug: str, extracted: dict, raw_content: str, meta: dict
) -> str:
    """将提取结果和元数据保存为 JSON sidecar，供后续 index 使用"""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{slug}.json"
    payload = {
        "meta": meta,
        "raw_content": raw_content,
    }
    filepath.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return str(filepath)


# ─── URL 收集 Tasks ─────────────────────────────────────────────────────────


@task(name="collect_urls_url_template", tags=["crawl", "list"], cache_policy=NO_CACHE)
async def collect_urls_url_template_task(
    crawler: AsyncWebCrawler,
    pagination: dict,
    link_filter_pattern: str | None,
) -> list[str]:
    """url_template 翻页：逐页爬取列表，收集内链"""
    tmpl: str = pagination["url_template"]
    page_start: int = pagination.get("page_start", 1)
    page_end: int = pagination.get("page_end", 1)

    all_urls: list[str] = []
    seen: set[str] = set()

    for page in range(page_start, page_end + 1):
        url = tmpl.format(page=page)
        result = await crawler.arun(
            url=url, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        )
        if not result.success:
            print(f"  [警告] 列表页 {page} 失败: {result.error_message}")
            continue

        internal = result.links.get("internal", [])
        filtered = filter_links(internal, link_filter_pattern)
        new = [u for u in filtered if u not in seen]
        seen.update(new)
        all_urls.extend(new)
        print(
            f"  列表页 {page}: 找到 {len(internal)} 个链接, 过滤出 {len(filtered)} 个链接（新增 {len(new)}）"
        )

    return all_urls


@task(name="collect_urls_js_pagination", tags=["crawl", "list"], cache_policy=NO_CACHE)
async def collect_urls_js_pagination_task(
    crawler: AsyncWebCrawler,
    pagination: dict,
    browser_cfg: dict,
    link_filter_pattern: str | None,
) -> list[str]:
    """js_pagination 翻页：保持 session，用 JS 点击翻页收集链接"""
    url: str = pagination["url"]
    total_pages: int = pagination.get("total_pages", 1)
    session_id: str = pagination.get("session_id") or f"session_{uuid.uuid4().hex[:8]}"
    wait_for_first: str | None = pagination.get("wait_for_first")
    js_next_page_tpl: str | None = pagination.get("js_next_page")
    wait_for_next: str | None = pagination.get("wait_for_next")

    all_urls: list[str] = []
    seen: set[str] = set()

    # 爬第 0 页（首页）
    first_config = CrawlerRunConfig(
        session_id=session_id,
        wait_for=wait_for_first,
        cache_mode=CacheMode.BYPASS,
    )
    await crawler.start()
    result = await crawler.arun(url=url, config=first_config)
    if result.success:
        internal = result.links.get("internal", [])
        filtered = filter_links(internal, link_filter_pattern)
        new = [u for u in filtered if u not in seen]
        seen.update(new)
        all_urls.extend(new)
        print(f"  JS 列表页 0: 找到 {len(filtered)} 个链接（新增 {len(new)}）")

    # 翻后续页
    for page in range(1, total_pages):
        if not js_next_page_tpl:
            break
        js_next = js_next_page_tpl.replace("{page}", str(page))
        next_config = CrawlerRunConfig(
            session_id=session_id,
            js_code_before_wait=f"js:{js_next}",
            wait_for=wait_for_next,
            js_only=True,
            cache_mode=CacheMode.BYPASS,
        )
        result = await crawler.arun(url=url, config=next_config)
        if not result.success:
            print(f"  [警告] JS 翻页 {page} 失败: {result.error_message}")
            continue
        internal = result.links.get("internal", [])
        filtered = filter_links(internal, link_filter_pattern)
        new = [u for u in filtered if u not in seen]
        seen.update(new)
        all_urls.extend(new)
        print(f"  JS 列表页 {page}: 找到 {len(filtered)} 个链接（新增 {len(new)}）")

    return all_urls


# ─── 爬取 Tasks ─────────────────────────────────────────────────────────


@task(name="crawl_detail_pages", tags=["crawl", "detail"], cache_policy=NO_CACHE)
async def crawl_detail_pages_task(
    crawler: AsyncWebCrawler,
    urls: list[str],
    run_config: CrawlerRunConfig,
) -> list[dict]:
    """批量爬取详情页"""
    results = await crawler.arun_many(urls=urls, config=run_config)

    crawl_results = []
    for result in results:
        crawl_results.append(
            {
                "url": result.url,
                "success": result.success,
                "extracted_content": result.extracted_content
                if result.success
                else None,
                "markdown": result.markdown if result.success else None,
                "error_message": result.error_message if not result.success else None,
            }
        )

    return crawl_results


@task(name="crawl_single_page", tags=["crawl", "single"], cache_policy=NO_CACHE)
async def crawl_single_page_task(
    crawler: AsyncWebCrawler,
    url: str,
    run_config: CrawlerRunConfig,
) -> dict:
    """爬取单个页面"""
    result = await crawler.arun(url=url, config=run_config)

    return {
        "url": result.url,
        "success": result.success,
        "extracted_content": result.extracted_content if result.success else None,
        "markdown": result.markdown if result.success else None,
        "error_message": result.error_message if not result.success else None,
    }
