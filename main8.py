import asyncio
import re
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    PruningContentFilter,
)
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy


SEED_URL = "https://news.foodmate.net/guonei/"
OUTPUT_FILE = Path("output/hpp_focus_results_4.md")
ALL_PAGES_DIR = Path("output/hpp_all_pages_4")
FOCUS_PAGES_DIR = Path("output/hpp_focus_pages_4")

# HPP 超高压方向关键词（核心 + 应用）
CORE_KEYWORDS = [
    "hpp",
    "uhp",
    "ultra high pressure",
    "high pressure processing",
    "超高压",
    "高压处理",
    "高静压",
    "hip",
    "isostatic",
]

TOPIC_KEYWORDS = [
    "设备",
    "装备",
    "技术",
    "工艺",
    "系统",
    "生产线",
    "应用",
    "场景",
    "案例",
    "食品",
    "果汁",
    "肉制品",
    "水产",
    "杀菌",
    "保鲜",
    "industrial",
    "equipment",
    "technology",
    "application",
    "case",
]


def normalize_text(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def keyword_hits(text: str, keywords: list[str]) -> int:
    normalized = normalize_text(text)
    hits = 0
    for kw in keywords:
        k = kw.lower()
        if re.search(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])", normalized):
            hits += 1
        elif k in normalized:
            hits += 1
    return hits


def relevance_score(text: str) -> tuple[int, int, int]:
    core_hits = keyword_hits(text, CORE_KEYWORDS)
    topic_hits = keyword_hits(text, TOPIC_KEYWORDS)
    score = core_hits * 3 + topic_hits
    return score, core_hits, topic_hits


def is_valid_hpp_content(title: str, content: str) -> tuple[bool, int, int, int]:
    merged = f"{title}\n{content}"
    score, core_hits, topic_hits = relevance_score(merged)
    is_valid = core_hits >= 1 and score >= 4 and (topic_hits >= 1 or core_hits >= 2)
    return is_valid, score, core_hits, topic_hits


def extract_title(result) -> str:
    metadata = getattr(result, "metadata", None) or {}
    title = str(metadata.get("title", "")).strip()
    if title:
        return title
    slug = result.url.rstrip("/").split("/")[-1]
    return slug or result.url


def extract_content(result) -> str:
    md = getattr(result, "markdown", None)
    if md:
        return (md.fit_markdown or md.raw_markdown or "").strip()
    return ""


def normalized_host(url: str) -> str:
    host = (urlparse(url).netloc or "").lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def is_same_domain(url: str, seed_url: str) -> bool:
    return normalized_host(url) == normalized_host(seed_url)


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|\r\n\t]", "_", name).strip()
    name = re.sub(r"\s+", "_", name)
    return (name[:120] or "untitled").strip("._") or "untitled"


def save_page_markdown(
    directory: Path, index: int, title: str, url: str, content: str
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{index:04d}_{sanitize_filename(title)}.md"
    filepath = directory / filename
    body = [f"# {title}", "", f"- URL: {url}", "", content]
    filepath.write_text("\n".join(body), encoding="utf-8")
    return filepath


def save_results(items: list[dict]) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = ["# HPP 超高压有效信息", ""]
    lines.append(f"共筛选出 {len(items)} 条高相关页面。")
    lines.append("")

    for i, item in enumerate(items, 1):
        lines.append(f"## {i}. {item['title']}")
        lines.append(f"- URL: {item['url']}")
        lines.append(
            f"- 相关度: {item['score']} (core={item['core_hits']}, topic={item['topic_hits']})"
        )
        lines.append("")
        lines.append(item["excerpt"])
        lines.append("")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")


async def main() -> None:
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=3,
            include_external=False,
            max_pages=300,
        ),
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.5)
        ),
        cache_mode=CacheMode.BYPASS,
        verbose=True,
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(SEED_URL, config=config)

    valid_items: list[dict] = []
    print(f"\n总共抓取页面(原始): {len(results)}")

    same_domain_results = [
        r
        for r in results
        if getattr(r, "success", False) and is_same_domain(r.url, SEED_URL)
    ]
    print(f"同域名成功页面: {len(same_domain_results)}")

    all_saved = 0
    focus_saved = 0

    for i, result in enumerate(same_domain_results, 1):
        title = extract_title(result)
        content = extract_content(result)
        if not content:
            continue

        save_page_markdown(ALL_PAGES_DIR, i, title, result.url, content)
        all_saved += 1

        valid, score, core_hits, topic_hits = is_valid_hpp_content(title, content)
        if not valid:
            continue

        save_page_markdown(FOCUS_PAGES_DIR, focus_saved + 1, title, result.url, content)
        focus_saved += 1

        excerpt = re.sub(r"\n{2,}", "\n", content)[:1000].strip()
        valid_items.append(
            {
                "title": title,
                "url": result.url,
                "score": score,
                "core_hits": core_hits,
                "topic_hits": topic_hits,
                "excerpt": excerpt,
            }
        )
        print(f"[保留] score={score:>2} | {title} | {result.url}")

    valid_items.sort(key=lambda x: x["score"], reverse=True)
    save_results(valid_items)

    print(f"\n已保存同域名页面: {all_saved} -> {ALL_PAGES_DIR}")
    print(f"已保存高相关页面: {focus_saved} -> {FOCUS_PAGES_DIR}")
    print(f"高相关汇总文件: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
