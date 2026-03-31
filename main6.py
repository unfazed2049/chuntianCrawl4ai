import asyncio
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, DefaultMarkdownGenerator, PruningContentFilter, CacheMode
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, LLMConfig, VirtualScrollConfig
from crawl4ai import JsonCssExtractionStrategy, LLMExtractionStrategy
import json

class ArticleData(BaseModel):
    title: str
    date: str
    content: str

async def main():
    browser_config = BrowserConfig(enable_stealth=True)  # Default browser configuration

    # virtual_config = VirtualScrollConfig(
    #     container_selector="ul#ty-list",      # CSS selector for scrollable container
    #     scroll_count=500,                 # Number of scrolls to perform
    #     scroll_by=400,    # How much to scroll each time
    #     wait_after_scroll=2           # Wait time (seconds) after each scroll
    # )
    async with AsyncWebCrawler(config=browser_config) as crawler:

        js_code = """(async () => {
            for (let i = 0; i < 3; i++) {
                let btn = document.querySelectorAll('.load_event');
                if (btn.length == 0) {
                    btn = document.querySelectorAll('.load_event_s');
                }
                btn[0].click();
                await new Promise(resolve => setTimeout(resolve, 5000));
            }
        })()
        """

        wait_for_code = """() => {
            const items = document.querySelectorAll("ul#ty-list > li");
            return items.length >= 30;
        }
        """

        run_config = CrawlerRunConfig(
            # extraction_strategy = llm_strategy,
            # extraction_strategy=JsonCssExtractionStrategy(schema),
            css_selector="ul#ty-list",

            # virtual_scroll_config=virtual_config,
            # js_code=f"js:{js_code}",
            js_code_before_wait=f"js:{js_code}",
            wait_for=f"js:{wait_for_code}",
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

        # await crawler.start()

        result = await crawler.arun(
            url="https://www.instrument.com.cn/news/list-0.html",
            config=run_config
        )
        # Different content formats
        # print(result.markdown.raw_markdown) # Raw markdown from cleaned html
        # print(result.markdown.raw_markdown) # Most relevant content in markdown
        print(result.markdown.fit_markdown)
        print(result.links["internal"][:10])



if __name__ == "__main__":
    asyncio.run(main())
