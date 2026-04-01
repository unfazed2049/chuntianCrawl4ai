from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Option 1: Use the raw HTML directly from the webpage (before any processing)
    raw_md_generator = DefaultMarkdownGenerator(
        content_source="raw_html",
        options={"ignore_links": False, "ignore_images": False}
    )

    # Option 2: Use the cleaned HTML (after scraping strategy processing - default)
    cleaned_md_generator = DefaultMarkdownGenerator(
        content_source="cleaned_html",  # This is the default
        options={"ignore_links": True, , "ignore_images": False}
    )

    # Option 3: Use preprocessed HTML optimized for schema extraction
    fit_md_generator = DefaultMarkdownGenerator(
        content_source="fit_html",
        options={"ignore_links": True, , "ignore_images": False}
    )

    # Use one of the generators in your crawler config
    config = CrawlerRunConfig(
        markdown_generator=cleaned_md_generator,  # Try each of the generators
        # css_selector="div#articleDiv",
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://news.cau.edu.cn/kxyj/20f78e9e4111460d90a5c0a330a1572b.htm", config=config)
        if result.success:
            print("Fit Markdown:\n", result.markdown.fit_markdown)

            print("Markdown:\n", result.markdown.raw_markdown)
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
