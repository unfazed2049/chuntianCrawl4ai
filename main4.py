import asyncio
import re
import json
from pathlib import Path
from dataclasses import dataclass
from crawl4ai import (
    AsyncWebCrawler,
    DefaultMarkdownGenerator,
    PruningContentFilter,
    CacheMode,
)
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy


# ─────────────────────────────────────────────
# 列表源配置：每个条目对应一个栏目
# ─────────────────────────────────────────────
@dataclass
class ListConfig:
    name: str  # 栏目名称（用于日志）
    list_url_template: str  # 列表页 URL 模板，含 {page} 占位
    total_pages: int  # 爬取页数
    detail_url_pattern: str  # 从列表页 HTML 中提取详情页 URL 的正则（完整 URL）
    output_dir: Path  # 输出目录
    # 详情页 CSS 选择器
    title_selector: str = "h1.title"
    date_selector: str = "div.info"
    content_selector: str = "div#article"


SOURCES: list[ListConfig] = [
    ListConfig(
        name="中国食品",
        list_url_template="https://news.foodmate.net/guonei/list_{page}.html",
        total_pages=3,
        detail_url_pattern=r'href="(https://news\.foodmate\.net/\d{4}/\d{2}/\d+\.html)"',
        output_dir=Path("output/食品伙伴网/中国食品"),
    ),
    ListConfig(
        name="国际食品",
        list_url_template="https://news.foodmate.net/guoji/list_{page}.html",
        total_pages=3,
        detail_url_pattern=r'href="(https://news\.foodmate\.net/\d{4}/\d{2}/\d+\.html)"',
        output_dir=Path("output/食品伙伴网/国际食品"),
    ),
]

# 文件名非法字符替换
FILENAME_ILLEGAL = re.compile(r'[\\/:*?"<>|\r\n\t]')


def sanitize_filename(name: str, fallback: str) -> str:
    """将标题转换为合法文件名"""
    name = name.strip()
    name = FILENAME_ILLEGAL.sub("_", name)
    name = name[:100]
    return name if name else fallback


# ─────────────────────────────────────────────
# 第一步：爬取列表页，提取详情页 URL
# ─────────────────────────────────────────────
async def fetch_list_pages(crawler: AsyncWebCrawler, source: ListConfig) -> list[str]:
    """爬取所有列表页，返回去重后的详情页 URL 列表"""
    pattern = re.compile(source.detail_url_pattern)
    seen: set[str] = set()
    urls: list[str] = []
    list_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    for page in range(1, source.total_pages + 1):
        url = source.list_url_template.format(page=page)
        result = await crawler.arun(url=url, config=list_config)
        if not result.success:
            print(
                f"  [警告] [{source.name}] 列表页 {page} 失败: {result.error_message}"
            )
            continue

        matches = pattern.findall(result.html)
        new_count = 0
        for m in matches:
            if m not in seen:
                seen.add(m)
                urls.append(m)
                new_count += 1

        print(
            f"  [{source.name}] 列表页 {page}: 新增 {new_count} 个链接（累计 {len(urls)}）"
        )

    return urls


# ─────────────────────────────────────────────
# 第二步：批量爬取详情页
# ─────────────────────────────────────────────
async def fetch_detail_pages(
    crawler: AsyncWebCrawler,
    urls: list[str],
    source: ListConfig,
) -> list[dict]:
    """批量爬取详情页，返回提取结果列表"""
    schema = {
        "name": "News Detail",
        "baseSelector": "body",
        "fields": [
            {"name": "title", "selector": source.title_selector, "type": "text"},
            {"name": "date", "selector": source.date_selector, "type": "text"},
        ],
    }

    run_config = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(schema),
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.5),
        ),
    )

    print(f"\n  开始批量爬取 {len(urls)} 个详情页...")
    results = await crawler.arun_many(urls=urls, config=run_config)

    items: list[dict] = []
    for result in results:
        if not result.success:
            print(f"  [警告] 详情页失败: {result.url} — {result.error_message}")
            continue

        title = ""
        date = ""
        try:
            data = json.loads(result.extracted_content or "[]")
            if data:
                title = data[0].get("title", "").strip()
                raw_date = data[0].get("date", "").strip()
                # 从 "时间：2026-03-23 15:05 来源：..." 中提取日期部分
                m = re.search(r"时间[：:]\s*(\d{4}-\d{2}-\d{2}[^\s&]*)", raw_date)
                date = m.group(1) if m else raw_date
        except (json.JSONDecodeError, IndexError):
            pass

        # fallback 文件名：URL 最后一段（如 739260）
        url_slug = result.url.rstrip("/").split("/")[-1].replace(".html", "")

        # 正文：优先 fit_markdown，fallback raw_markdown
        content = ""
        if result.markdown:
            content = result.markdown.fit_markdown or result.markdown.raw_markdown or ""

        items.append(
            {
                "url": result.url,
                "title": title,
                "date": date,
                "content": content,
                "url_slug": url_slug,
            }
        )
        print(f"  ✅ {title or url_slug} ({date})")

    return items


# ─────────────────────────────────────────────
# 第三步：保存文件
# ─────────────────────────────────────────────
def save_articles(items: list[dict], output_dir: Path) -> None:
    """将提取结果写入 markdown 文件"""
    output_dir.mkdir(parents=True, exist_ok=True)

    for item in items:
        filename = sanitize_filename(item["title"], item["url_slug"]) + ".md"
        filepath = output_dir / filename

        lines: list[str] = []
        if item["title"]:
            lines.append(f"# {item['title']}\n")
        if item["date"]:
            lines.append(f"日期：{item['date']}\n")
        if item["title"] or item["date"]:
            lines.append("")
        lines.append(item["content"])

        filepath.write_text("\n".join(lines), encoding="utf-8")
        print(f"  已保存: {filepath}")


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────
async def main() -> None:
    print("=" * 60)
    print("食品伙伴网 多栏目新闻爬虫")
    print("=" * 60)

    browser_config = BrowserConfig()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for source in SOURCES:
            print(f"\n{'─' * 50}")
            print(f"栏目：{source.name}  →  {source.output_dir}")
            print(f"{'─' * 50}")

            # 第一步：收集详情页 URL
            print(f"\n【第一步】爬取 {source.total_pages} 页列表...")
            detail_urls = await fetch_list_pages(crawler, source)
            print(f"共收集 {len(detail_urls)} 个去重详情页 URL")

            if not detail_urls:
                print("  未找到详情页，跳过此栏目。")
                continue

            # 第二步：批量抓取详情页
            print(f"\n【第二步】批量爬取详情页...")
            items = await fetch_detail_pages(crawler, detail_urls, source)

            # 第三步：保存
            print(f"\n【第三步】保存到 {source.output_dir} ...")
            save_articles(items, source.output_dir)
            print(f"  栏目「{source.name}」完成，共保存 {len(items)} 篇。")

    print("\n" + "=" * 60)
    print("全部栏目爬取完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
