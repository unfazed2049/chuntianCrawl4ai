"""
config.json 驱动的多站点爬虫
支持 list 模式（url_template / js_pagination）和 single 模式
内容提取使用 LLMExtractionStrategy，结果保存为 markdown 文件
"""

import asyncio
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    DefaultMarkdownGenerator,
    LLMExtractionStrategy,
    PruningContentFilter,
)
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, LLMConfig

from app_config import load_app_config
from markdown_utils import pick_markdown_content
from schemas import CRAWL_CONTENT_SCHEMA
from utils import load_prompts, load_config, DEFAULT_CONFIG, CONFIG_DIR, OUTPUT_ROOT

# ─── 常量 ────────────────────────────────────────────────────────────────────

PROMPTS_DIR = Path("prompts")

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


def sanitize_filename(name: str, fallback: str = "untitled") -> str:
    name = name.strip()
    name = FILENAME_ILLEGAL.sub("_", name)
    name = name[:100]
    return name or fallback


def slug_from_url(url: str) -> str:
    """从 URL 末尾提取 slug 作为文件名（去掉扩展名）"""
    part = url.rstrip("/").split("/")[-1]
    stem = part.rsplit(".", 1)[0] if "." in part else part
    return stem or sanitize_filename("", "page")


def build_output_dir(site: dict, section: dict, workspace: str) -> Path:
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
        merged.update({k: v for k, v in section_cfg.items() if v is not None})
    return BrowserConfig(**merged)


def build_llm_strategy(llm_cfg: dict, prompt_cfg: dict) -> LLMExtractionStrategy:
    """根据 llm_config 和 prompt 配置构建 LLMExtractionStrategy"""
    schema = CRAWL_CONTENT_SCHEMA
    # 将简单 schema dict 转成 JSON Schema 格式
    if schema and isinstance(schema, dict):
        json_schema = {
            "type": "object",
            "properties": {k: {"type": v} for k, v in schema.items()},
        }
    else:
        json_schema = schema  # 允许直接传入完整 JSON Schema

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
    llm_strategy: LLMExtractionStrategy,
    extra: dict | None = None,
) -> CrawlerRunConfig:
    """构建 CrawlerRunConfig，合并默认配置、section crawler_config 与额外参数"""
    # 从默认配置开始
    merged = DEFAULT_CRAWLER_CONFIG.copy()

    # 合并 section 配置
    if section_crawler_cfg:
        merged.update({k: v for k, v in section_crawler_cfg.items() if v is not None})

    # 合并额外参数
    if extra:
        merged.update({k: v for k, v in extra.items() if v is not None})

    # 提取 threshold 用于 content_filter
    threshold = merged.pop("content_filter_threshold", 0.5)

    return CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=threshold),
        ),
        **merged,
    )


def build_meta(site: dict, section: dict, url: str) -> dict:
    """构建文档的 meta 信息，包含 site/section 上下文"""
    from datetime import datetime

    meta: dict[str, Any] = {
        "site_name": site.get("name"),
        "section_name": section.get("name"),
        "source_url": url,
        "crawled_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    # 竞争对手相关字段（非必须）
    if competitor_id := site.get("competitor_id"):
        meta["competitor_id"] = competitor_id
    if data_type := section.get("data_type"):
        meta["data_type"] = data_type

    return meta


def save_json(
    output_dir: Path,
    slug: str,
    extracted: dict,
    raw_content: str,
    meta: dict,
):
    """将提取结果保存为 JSON 文件

    结构：
    {
        "meta": { site/section 级别的上下文信息 },
        "raw_content": "原始 markdown",
        ...extracted 字段（LLM 提取的结构化数据）
    }
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{slug}.json"

    doc = {
        "meta": meta,
        "raw_content": raw_content,
        **extracted,
    }

    filepath.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    已保存: {filepath}")


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


# ─── 链接过滤 ─────────────────────────────────────────────────────────────────


def filter_links(links: list[dict], pattern: str | None) -> list[str]:
    """
    从 result.links['internal'] 或 ['external'] 过滤出目标 URL。
    links 元素格式：{"href": "...", "text": "..."}
    """
    urls = [lk.get("href", "") for lk in links if lk.get("href")]
    if not pattern:
        return list(dict.fromkeys(urls))  # 去重保序
    rx = re.compile(pattern)
    return list(dict.fromkeys(u for u in urls if rx.search(u)))


# ─── LIST 模式 ────────────────────────────────────────────────────────────────


async def collect_urls_url_template(
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
        print(f"  列表页 {page}: 找到 {len(filtered)} 个链接（新增 {len(new)}）")

    return all_urls


async def collect_urls_js_pagination(
    crawler: AsyncWebCrawler,
    pagination: dict,
    browser_cfg: dict,
    link_filter_pattern: str | None,
) -> list[str]:
    """js_pagination 翻页：保持 session，用 JS 点击翻页收集链接"""
    url: str = pagination["url"]
    total_pages: int = pagination.get("total_pages", 1)
    # 自动生成 session_id
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


async def run_list_section(
    crawler: AsyncWebCrawler,
    site: dict,
    section: dict,
    llm_cfg: dict,
    prompts: dict,
    workspace: str,
):
    print(f"\n  [LIST] {section['name']}")
    list_cfg = section.get("list", {})
    pagination = list_cfg.get("pagination", {})
    link_filter = list_cfg.get("link_filter_pattern")
    browser_cfg = section.get("browser_config", {})

    # 1. 收集详情页 URL
    pagination_type = pagination.get("type", "url_template")
    if pagination_type == "url_template":
        detail_urls = await collect_urls_url_template(crawler, pagination, link_filter)
    elif pagination_type == "js_pagination":
        detail_urls = await collect_urls_js_pagination(
            crawler, pagination, browser_cfg, link_filter
        )
    else:
        print(f"  [错误] 未知 pagination.type: {pagination_type}")
        return

    print(f"  共收集 {len(detail_urls)} 个详情页 URL")
    if not detail_urls:
        return

    # 2. 确定 prompt（使用 section 指定的 prompt，或使用 config 中的 default）
    prompt_key = section.get("prompt", "default")
    prompt_cfg = prompts.get(prompt_key)
    if not prompt_cfg:
        print(f"  [警告] 未找到 prompt '{prompt_key}'，使用 'default'")
        prompt_cfg = prompts.get("default", {})

    # 3. 构建爬取配置
    llm_strategy = build_llm_strategy(llm_cfg, prompt_cfg)
    run_config = build_crawler_run_config(
        section.get("crawler_config", {}), llm_strategy
    )

    # 4. 批量爬取详情页
    print(f"  开始批量爬取 {len(detail_urls)} 个详情页...")
    results = await crawler.arun_many(urls=detail_urls, config=run_config)

    # 5. 保存
    output_dir = build_output_dir(site, section, workspace)
    saved = 0
    for result in results:
        if not result.success:
            print(f"  [警告] 详情页失败: {result.url} - {result.error_message}")
            continue
        extracted = parse_extracted(result.extracted_content)
        raw_content = pick_markdown_content(result.markdown)
        slug = slug_from_url(result.url)
        meta = build_meta(site, section, result.url)
        save_json(output_dir, slug, extracted, raw_content, meta)
        saved += 1

    print(f"  完成，共保存 {saved} 个文件 -> {output_dir}")


# ─── SINGLE 模式 ──────────────────────────────────────────────────────────────


async def run_single_section(
    crawler: AsyncWebCrawler,
    site: dict,
    section: dict,
    llm_cfg: dict,
    prompts: dict,
    workspace: str,
):
    print(f"\n  [SINGLE] {section['name']}")
    single_cfg = section.get("single", {})
    url: str | None = single_cfg.get("url")
    if not url:
        print("  [错误] single 模式缺少 url 配置")
        return

    # 确定 prompt（使用 section 指定的 prompt，或使用 config 中的 default）
    prompt_key = section.get("prompt", "default")
    prompt_cfg = prompts.get(prompt_key)
    if not prompt_cfg:
        print(f"  [警告] 未找到 prompt '{prompt_key}'，使用 'default'")
        prompt_cfg = prompts.get("default", {})

    # 构建配置
    llm_strategy = build_llm_strategy(llm_cfg, prompt_cfg)
    run_config = build_crawler_run_config(
        section.get("crawler_config", {}), llm_strategy
    )

    # 爬取
    result = await crawler.arun(url=url, config=run_config)
    if not result.success:
        print(f"  [错误] 爬取失败: {url} - {result.error_message}")
        return

    extracted = parse_extracted(result.extracted_content)
    raw_content = pick_markdown_content(result.markdown)
    slug = slug_from_url(url)
    meta = build_meta(site, section, url)

    output_dir = build_output_dir(site, section, workspace)
    save_json(output_dir, slug, extracted, raw_content, meta)
    print(f"  完成 -> {output_dir / slug}.json")


# ─── 主入口 ───────────────────────────────────────────────────────────────────


async def run_section(
    crawler: AsyncWebCrawler,
    site: dict,
    section: dict,
    llm_cfg: dict,
    prompts: dict,
    workspace: str,
):
    mode = section.get("mode", "single")
    browser_cfg = build_browser_config(section.get("browser_config", {}))
    # 注：AsyncWebCrawler 以 site/section 级别复用，browser_config 在 crawler 层面设置
    # 这里我们用同一个 crawler 实例，browser_config 差异通过 BrowserConfig 传入新 crawler
    if mode == "list":
        await run_list_section(crawler, site, section, llm_cfg, prompts, workspace)
    elif mode == "single":
        await run_single_section(crawler, site, section, llm_cfg, prompts, workspace)
    else:
        print(f"  [跳过] 未知 mode: {mode}")


async def main():
    # 支持命令行参数：python crawler.py [--config=<name>] [site_name] [section_name]
    config_name = DEFAULT_CONFIG
    filter_site = None
    filter_section = None

    # 解析命令行参数
    args = sys.argv[1:]
    for arg in args[:]:
        if arg.startswith("--config="):
            config_name = arg.split("=", 1)[1]
            args.remove(arg)

    if len(args) > 0:
        filter_site = args[0]
    if len(args) > 1:
        filter_section = args[1]

    # 加载配置，workspace 从 JSON 内读取
    try:
        config, workspace = load_config(config_name)
    except FileNotFoundError as e:
        print(f"[错误] {e}")
        print(f"可用的配置文件应该放在: {CONFIG_DIR}/<config_name>.json")
        return

    app_cfg = load_app_config()
    llm_cfg: dict = app_cfg["llm_config"]

    # 加载 prompts: 优先从 prompts/ 目录加载，如果目录为空则从 config 中读取
    prompts: dict = load_prompts()
    if not prompts:
        prompts = config.get("prompts", {})
        if prompts:
            print(f"[提示] 从配置文件加载 prompts，建议迁移到 prompts/ 目录")

    sites: list[dict] = config.get("sites", [])

    print("=" * 60)
    print(f"多站点爬虫启动 [workspace: {workspace}]")
    print("=" * 60)

    for site in sites:
        if filter_site and site["name"] != filter_site:
            continue

        print(f"\n【站点】{site['name']}")
        sections: list[dict] = site.get("sections", [])

        browser_config = BrowserConfig(headless=True)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for section in sections:
                if filter_section and section["name"] != filter_section:
                    continue
                await run_section(crawler, site, section, llm_cfg, prompts, workspace)

    print("\n" + "=" * 60)
    print("全部任务完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
