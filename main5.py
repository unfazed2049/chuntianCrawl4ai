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
    browser_config = BrowserConfig()  # Default browser configuration


    async with AsyncWebCrawler(config=browser_config) as crawler:
        wait_for = """() => {
            const items = document.querySelectorAll('div.expo_box');
            return items.length > 0;
        }
        """

        session_id = "foodexworld_internalexpo"
        run_config = CrawlerRunConfig(
            session_id = session_id,
            # extraction_strategy = llm_strategy,
            # extraction_strategy=JsonCssExtractionStrategy(schema),
            # css_selector="div#articleDiv",
            css_selector="div.expo_index",
            wait_for=f"js:{wait_for}",
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

        await crawler.start()

        result = await crawler.arun(
            url="https://www.foodexworld.com/internalexpo",
            config=run_config
        )
        # Different content formats
        # print(result.markdown.raw_markdown) # Raw markdown from cleaned html
        print(result.markdown.raw_markdown) # Most relevant content in markdown


        for page in range(1, 3):
            js_next_page_tpl = """(() => {
                const items = document.querySelectorAll('div.expo_box');
                items.forEach(el => el.remove());

                const btns =  document.querySelectorAll('ul.pagination > li:not(.disabled)');
                if (btns[__PAGE__]) {
                    btns[__PAGE__].firstChild.click();
                }
            })()
            """

            wait_for_next = """() => {
                const items = document.querySelectorAll('div.expo_box');
                console.log("length ====", items.length);
                return items.length > 0;
            }
            """

            js_next_page = js_next_page_tpl.replace("__PAGE__", str(page))

            print(js_next_page)

            config_next = CrawlerRunConfig(
                session_id=session_id,
                js_code_before_wait=f"js:{js_next_page}",
                wait_for=f"js:{wait_for_next}",
                js_only=True,       # We're continuing from the open tab
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(
                url="https://www.foodexworld.com/internalexpo",
                config=config_next
            )
            # Different content formats
            # print(result.markdown.raw_markdown) # Raw markdown from cleaned html
            print(result.markdown.raw_markdown) # Most relevant content in markdown

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
