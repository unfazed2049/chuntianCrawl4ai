import asyncio
import re
import os
import json
from pathlib import Path
from crawl4ai import (
    AsyncWebCrawler,
    DefaultMarkdownGenerator,
    PruningContentFilter,
    CacheMode,
)
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, LLMConfig
from crawl4ai import JsonCssExtractionStrategy, LLMExtractionStrategy
from pydantic import BaseModel, Field

class ArticleData(BaseModel):
    title: str
    date: str
    content: str


# 配置
BASE_URL = "https://news.cau.edu.cn/kxyj"
LIST_URL_TEMPLATE = "https://news.cau.edu.cn/kxyj/index{page}.htm"
TOTAL_PAGES = 3
OUTPUT_DIR = Path("output/中国农业大学/科学研究")

# 匹配详情页 URL 的正则：href="32位hex.htm"，相对路径
DETAIL_URL_PATTERN = re.compile(r'href="([a-f0-9]{32}\.htm)"')

# 文件名非法字符替换
FILENAME_ILLEGAL = re.compile(r'[\\/:*?"<>|\r\n\t]')


def sanitize_filename(name: str, fallback: str) -> str:
    """将标题转换为合法文件名"""
    name = name.strip()
    name = FILENAME_ILLEGAL.sub("_", name)
    name = name[:100]  # 限制长度
    return name if name else fallback


async def fetch_list_page(crawler: AsyncWebCrawler, page: int) -> list[str]:
    """爬取一个列表页，返回详情页完整 URL 列表"""
    url = LIST_URL_TEMPLATE.format(page=page)
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    result = await crawler.arun(url=url, config=config)
    if not result.success:
        print(f"  [警告] 列表页 {page} 爬取失败: {result.error_message}")
        return []

    # 从 HTML 中正则匹配详情页路径
    matches = DETAIL_URL_PATTERN.findall(result.html)
    urls = [f"{BASE_URL}/{m}" for m in matches]
    print(f"  列表页 {page}: 找到 {len(urls)} 个详情页链接")
    return urls


async def fetch_detail_pages(crawler: AsyncWebCrawler, urls: list[str]) -> list[dict]:
    """批量爬取详情页，返回提取结果列表"""
    schema = {
        "name": "News Detail",
        "baseSelector": "body",
        "fields": [
            {"name": "title", "selector": "div.pageArticleTitle > h3", "type": "text"},
            {
                "name": "date",
                "selector": "div.pageArticleTitle > div.articleAuthor > span:nth-child(1)",
                "type": "text",
            },
            {"name": "content", "selector":"div#articleDiv", "type": "text"}
        ],
    }

    llm_strategy = LLMExtractionStrategy(
            llm_config = LLMConfig(provider="gpt-4o-mini",api_token="sk-94A2rGOiwJyYEB7mAfWtnQwlSAE1tfKmkpBTvEjwIn8LLFLJ", base_url="https://fastcn.poloapi.com/v1"),
            # schema=ArticleData.schema(),
            extraction_type="schema",
            instruction="Extract 'title', 'date' and 'content' from the content."
        )

    run_config = CrawlerRunConfig(
        # extraction_strategy=JsonCssExtractionStrategy(schema),
        extraction_strategy = llm_strategy,
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.5),
        ),
    )

    print(f"\n开始批量爬取 {len(urls)} 个详情页...")
    results = await crawler.arun_many(urls=urls, config=run_config)

    items = []
    for result in results:
        if not result.success:
            print(f"  [警告] 详情页爬取失败: {result.url} - {result.error_message}")
            continue

        # 提取 CSS 结构化字段
        title = ""
        date = ""
        try:
            data = json.loads(result.extracted_content or "[]")
            if data:
                title = data[0].get("title", "").strip()
                date = data[0].get("date", "").strip()
                content = data[0].get("content", "").strip()
        except (json.JSONDecodeError, IndexError):
            pass

        # URL 中的 hash 作为 fallback 文件名
        url_hash = result.url.split("/")[-1].replace(".htm", "")

         # 优先用 fit_markdown，fallback 到 raw_markdown
        if not content:
            content = result.markdown.fit_markdown or result.markdown.raw_markdown or ""

        items.append(
            {
                "url": result.url,
                "title": title,
                "date": date,
                "content": content,
                "url_hash": url_hash,
            }
        )
        print(f"  ✅ {title or url_hash} ({date})")

    return items


def save_articles(items: list[dict]):
    """将提取结果写入 markdown 文件"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for item in items:
        filename = item["url_hash"] + ".md"
        filepath = OUTPUT_DIR / filename

        # 组装 markdown 内容
        lines = []
        if item["title"]:
            lines.append(f"# {item['title']}\n")
        if item["date"]:
            lines.append(f"日期：{item['date']}\n")
        if item["title"] or item["date"]:
            lines.append("")  # 空行分隔
        lines.append(item["content"])

        filepath.write_text("\n".join(lines), encoding="utf-8")
        print(f"  已保存: {filepath}")


async def main():
    print("=" * 60)
    print("中国农业大学 - 科学研究 新闻爬虫")
    print("=" * 60)

    browser_config = BrowserConfig()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # 第一步：爬取列表页，收集详情页 URL
        print(f"\n【第一步】爬取 {TOTAL_PAGES} 页列表页...")
        all_detail_urls = []
        seen = set()

        for page in range(1, TOTAL_PAGES + 1):
            urls = await fetch_list_page(crawler, page)
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    all_detail_urls.append(url)

        print(f"\n共收集到 {len(all_detail_urls)} 个去重后的详情页 URL")

        if not all_detail_urls:
            print("未找到任何详情页，退出。")
            return

        # 第二步：批量爬取详情页
        print(f"\n【第二步】批量爬取详情页...")
        items = await fetch_detail_pages(crawler, all_detail_urls)

        # 第三步：保存文件
        print(f"\n【第三步】保存文件到 {OUTPUT_DIR} ...")
        save_articles(items)

        print(f"\n完成！共保存 {len(items)} 篇文章。")


if __name__ == "__main__":
    asyncio.run(main())
