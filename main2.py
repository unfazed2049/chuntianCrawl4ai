import asyncio
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter
from crawl4ai import JsonCssExtractionStrategy, LLMExtractionStrategy
from crawl4ai.async_configs import LLMConfig
import re

class ArticleData(BaseModel):
    title: str
    date: str
    content: str
    editor: str

async def main():
    # # Create a scorer
    # scorer = KeywordRelevanceScorer(
    #     keywords=["kxyj"],
    #     weight=0.8
    # )

    # strategy = BestFirstCrawlingStrategy(
    #     max_depth=1,
    #     include_external=False,
    #     url_scorer=scorer,
    #     max_pages=50,              # Maximum number of pages to crawl (optional)
    # )
    #

    llm_strategy = LLMExtractionStrategy(
            llm_config = LLMConfig(provider="gpt-4o-mini",api_token="sk-94A2rGOiwJyYEB7mAfWtnQwlSAE1tfKmkpBTvEjwIn8LLFLJ", base_url="https://fastcn.poloapi.com/v1"),
            schema=ArticleData.schema(),
            extraction_type="schema",
            instruction="Extract 'title', 'date', 'content' and 'editor' from the content."
        )

    url_filter = URLPatternFilter(patterns=[r"/kxyj/[a-z0-9]+\.htm$"])

    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=3,
            include_external=False,
            # filter_chain=FilterChain([url_filter]),
            max_pages=10,
        ),
        # deep_crawl_strategy=strategy,
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun("http://www.pnmtcl.com/", config=config)

        print(f"Crawled {len(results)} pages in total")

        # Access individual results
        for result in results:  # Show first 3 results
            print(result.url)

if __name__ == "__main__":
    asyncio.run(main())
