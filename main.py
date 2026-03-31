import asyncio
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, DefaultMarkdownGenerator, PruningContentFilter, CacheMode
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, LLMConfig
from crawl4ai import JsonCssExtractionStrategy, LLMExtractionStrategy
import json

class ArticleData(BaseModel):
    title: str
    date: str
    content: str
    editor: str

async def main():
    llm_strategy = LLMExtractionStrategy(
            llm_config = LLMConfig(provider="gpt-4o-mini",api_token="sk-94A2rGOiwJyYEB7mAfWtnQwlSAE1tfKmkpBTvEjwIn8LLFLJ", base_url="https://fastcn.poloapi.com/v1"),
            # schema=ArticleData.schema(),
            extraction_type="schema",
            instruction="Extract 'title', 'date', 'content' and 'source' from the content."
        )

    browser_config = BrowserConfig()  # Default browser configuration
    run_config = CrawlerRunConfig(
        extraction_strategy = llm_strategy,
        # extraction_strategy=JsonCssExtractionStrategy(schema),
        # css_selector="div#articleDiv",
        cache_mode=CacheMode.BYPASS,
        # target_elements = ["div#articleDiv"],
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.8),
            # options={"ignore_links": True},
            # content_filter=BM25ContentFilter(
            #     user_query="RPA",
            #     bm25_threshold=0.2
            # )
        )
    )   # Default crawl run configuration

    async with AsyncWebCrawler(config=browser_config) as crawler:

        result = await crawler.arun(
            url="https://news.foodmate.net/2026/03/739487.html",
            config=run_config
        )
        # Different content formats
        # print(result.markdown.raw_markdown) # Raw markdown from cleaned html
        # print(result.markdown.raw_markdown) # Most relevant content in markdown
        print(result.extracted_content)
        print(result.markdown.raw_markdown)

        # Check success status
        # print(result.success)      # True if crawl succeeded
        # print(result.status_code)  # HTTP status code (e.g., 200, 404)

        # Access extracted media and links
        # print(result.media)        # Dictionary of found media (images, videos, audio)
        # print(result.links)        # Dictionary of internal and external links
        # data = json.loads(result.extracted_content)
        # print("data ===", data)
        #


if __name__ == "__main__":
    asyncio.run(main())
