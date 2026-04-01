"""
Prefect Flows for Crawl4ai
定义爬虫的工作流程
"""

from pathlib import Path

from crawl4ai import AsyncWebCrawler
from prefect import flow

from app_config import load_app_config
from markdown_utils import pick_markdown_content
from meilisearch_tasks import index_workspace_flow
from prefect_tasks import (
    build_browser_config,
    build_crawler_run_config,
    build_llm_strategy,
    build_meta,
    build_output_dir,
    clean_markdown_with_llm_task,
    collect_urls_js_pagination_task,
    collect_urls_url_template_task,
    crawl_detail_pages_task,
    crawl_single_page_task,
    load_config_task,
    load_prompts_task,
    parse_extracted,
    save_json_task,
    slug_from_url,
    DEFAULT_CONFIG,
    DEFAULT_WORKSPACE,
)
from redis_bloom_filter import create_detail_filter


# ─── LIST 模式 Flow ────────────────────────────────────────────────────────


@flow(name="run_list_section", log_prints=True)
async def run_list_section_flow(
    crawler: AsyncWebCrawler,
    site: dict,
    section: dict,
    llm_cfg: dict,
    prompts: dict,
    workspace: str = DEFAULT_WORKSPACE,
    redis_bloom_cfg: dict | None = None,
) -> list[str]:
    """LIST 模式：收集列表页链接，批量爬取详情页"""
    print(f"\n  [LIST] {section['name']}")
    list_cfg = section.get("list", {})
    pagination = list_cfg.get("pagination", {})
    link_filter = list_cfg.get("link_filter_pattern")
    browser_cfg = section.get("browser_config", {})

    # 1. 收集详情页 URL
    pagination_type = pagination.get("type", "url_template")
    if pagination_type == "url_template":
        detail_urls = await collect_urls_url_template_task(
            crawler, pagination, link_filter
        )
    elif pagination_type == "js_pagination":
        detail_urls = await collect_urls_js_pagination_task(
            crawler, pagination, browser_cfg, link_filter
        )
    else:
        print(f"  [错误] 未知 pagination.type: {pagination_type}")
        return []

    print(f"  共收集 {len(detail_urls)} 个详情页 URL")
    if not detail_urls:
        return []

    # 检查是否跳过 Redis Bloom 过滤
    skip_bloom = section.get("skip_bloom_filter", False)
    if skip_bloom:
        print("  [跳过] Redis Bloom 过滤已禁用（section 配置）")
        detail_bloom = None
    else:
        # 使用全局 Redis Bloom 配置
        detail_bloom = create_detail_filter(
            redis_bloom_cfg,
            workspace=workspace,
            site_name=site["name"],
            section_name=section["name"],
        )
        if detail_bloom:
            print("  [启用] Redis Bloom 过滤")
        elif redis_bloom_cfg and redis_bloom_cfg.get("enabled"):
            print("  [警告] Redis Bloom 已配置但不可用")

    if detail_bloom:
        before_filter_count = len(detail_urls)
        detail_urls = detail_bloom.filter_new_urls(detail_urls)
        skipped_count = before_filter_count - len(detail_urls)
        print(
            f"  Redis Bloom 过滤后待爬取 {len(detail_urls)} 个（跳过已爬取 {skipped_count} 个）"
        )
        if not detail_urls:
            return []

    # 2. 构建爬取配置（方案 B：crawl 阶段不做 LLM 提取）
    # 旧逻辑保留注释，便于后续快速切回 crawl 阶段提取。
    # prompt_key = section.get("prompt", "default")
    # prompt_cfg = prompts.get(prompt_key)
    # if not prompt_cfg:
    #     print(f"  [警告] 未找到 prompt '{prompt_key}'，使用 'default'")
    #     prompt_cfg = prompts.get("default", {})
    # llm_strategy = build_llm_strategy(llm_cfg, prompt_cfg)
    run_config = build_crawler_run_config(section.get("crawler_config", {}), None)

    # 4. 批量爬取详情页
    print(f"  开始批量爬取 {len(detail_urls)} 个详情页...")
    results = await crawl_detail_pages_task(crawler, detail_urls, run_config)

    # 5. 保存
    output_dir = build_output_dir(site, section, workspace)
    saved = 0
    crawled_urls: list[str] = []
    saved_json_paths: list[str] = []
    for result in results:
        if not result["success"]:
            print(f"  [警告] 详情页失败: {result['url']} - {result['error_message']}")
            continue
        extracted = parse_extracted(result["extracted_content"])
        fallback = pick_markdown_content(result["markdown"])
        slug = slug_from_url(result["url"])
        meta = build_meta(site, section, workspace, result["url"])
        cleaned_content = clean_markdown_with_llm_task(llm_cfg, prompts, meta, fallback)
        json_path = save_json_task(
            output_dir,
            slug,
            extracted,
            cleaned_content,
            meta,
        )
        print(f"    已保存: {json_path}")
        saved += 1
        crawled_urls.append(result["url"])
        saved_json_paths.append(json_path)

    if detail_bloom and crawled_urls:
        detail_bloom.mark_crawled(crawled_urls)
        print(f"  Redis Bloom 已写入 {len(crawled_urls)} 个详情页")

    print(f"  完成，共保存 {saved} 个文件 -> {output_dir}")
    return saved_json_paths


# ─── SINGLE 模式 Flow ──────────────────────────────────────────────────────


@flow(name="run_single_section", log_prints=True)
async def run_single_section_flow(
    crawler: AsyncWebCrawler,
    site: dict,
    section: dict,
    llm_cfg: dict,
    prompts: dict,
    workspace: str = DEFAULT_WORKSPACE,
) -> list[str]:
    """SINGLE 模式：爬取单个页面"""
    print(f"\n  [SINGLE] {section['name']}")
    single_cfg = section.get("single", {})
    url: str | None = single_cfg.get("url")
    if not url:
        print("  [错误] single 模式缺少 url 配置")
        return []

    # 构建配置（方案 B：crawl 阶段不做 LLM 提取）
    # 旧逻辑保留注释，便于后续快速切回 crawl 阶段提取。
    # prompt_key = section.get("prompt", "default")
    # prompt_cfg = prompts.get(prompt_key)
    # if not prompt_cfg:
    #     print(f"  [警告] 未找到 prompt '{prompt_key}'，使用 'default'")
    #     prompt_cfg = prompts.get("default", {})
    # llm_strategy = build_llm_strategy(llm_cfg, prompt_cfg)
    run_config = build_crawler_run_config(section.get("crawler_config", {}), None)

    # 爬取
    result = await crawl_single_page_task(crawler, url, run_config)
    if not result["success"]:
        print(f"  [错误] 爬取失败: {url} - {result['error_message']}")
        return []

    extracted = parse_extracted(result["extracted_content"])
    fallback = pick_markdown_content(result["markdown"])
    slug = slug_from_url(url)
    meta = build_meta(site, section, workspace, url)
    cleaned_content = clean_markdown_with_llm_task(llm_cfg, prompts, meta, fallback)

    output_dir = build_output_dir(site, section, workspace)
    json_path = save_json_task(output_dir, slug, extracted, cleaned_content, meta)
    print(f"  完成 -> {json_path}")
    return [json_path]


# ─── Section Flow ──────────────────────────────────────────────────────────


@flow(name="run_section", log_prints=True)
async def run_section_flow(
    crawler: AsyncWebCrawler,
    site: dict,
    section: dict,
    llm_cfg: dict,
    prompts: dict,
    workspace: str = DEFAULT_WORKSPACE,
    redis_bloom_cfg: dict | None = None,
) -> list[str]:
    """根据 section 的 mode 选择对应的 flow"""
    mode = section.get("mode", "single")
    if mode == "list":
        return await run_list_section_flow(
            crawler,
            site,
            section,
            llm_cfg,
            prompts,
            workspace,
            redis_bloom_cfg,
        )
    elif mode == "single":
        return await run_single_section_flow(
            crawler, site, section, llm_cfg, prompts, workspace
        )
    else:
        print(f"  [跳过] 未知 mode: {mode}")
        return []


# ─── 主 Flow ───────────────────────────────────────────────────────────────


@flow(name="crawl_sites", log_prints=True)
async def crawl_sites_flow(
    config_name: str = DEFAULT_CONFIG,
    filter_site: str | None = None,
    filter_section: str | None = None,
):
    """主工作流：加载配置，遍历站点和 sections"""
    # 加载配置，workspace 从 JSON 内读取
    config, workspace = load_config_task(config_name)
    app_cfg = load_app_config()
    llm_cfg: dict = app_cfg["llm_config"]
    meili_cfg: dict | None = app_cfg.get("meilisearch_config")
    if not meili_cfg or not meili_cfg.get("url"):
        meili_cfg = None
    redis_bloom_cfg: dict = app_cfg["redis_bloom_config"]

    # 加载 prompts
    prompts: dict = load_prompts_task()
    if not prompts:
        prompts = config.get("prompts", {})
        if prompts:
            print(f"[提示] 从配置文件加载 prompts，建议迁移到 prompts/ 目录")

    sites: list[dict] = config.get("sites", [])

    print("=" * 60)
    print(f"多站点爬虫启动 [workspace: {workspace}]")
    print("=" * 60)

    all_json_paths: list[str] = []
    for site in sites:
        if filter_site and site["name"] != filter_site:
            continue

        print(f"\n【站点】{site['name']}")
        sections: list[dict] = site.get("sections", [])

        from crawl4ai.async_configs import BrowserConfig

        browser_config = BrowserConfig(headless=True)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for section in sections:
                if filter_section and section["name"] != filter_section:
                    continue
                section_json_paths = await run_section_flow(
                    crawler,
                    site,
                    section,
                    llm_cfg,
                    prompts,
                    workspace,
                    redis_bloom_cfg,
                )
                all_json_paths.extend(section_json_paths)

    print("\n" + "=" * 60)
    print("全部爬取完成，开始 Meilisearch 写入")
    print("=" * 60)

    index_workspace_flow(
        workspace=workspace,
        meili_config=meili_cfg,
        llm_config=llm_cfg,
        json_paths=all_json_paths,
    )

    print("\n" + "=" * 60)
    print("全部任务完成")
    print("=" * 60)
