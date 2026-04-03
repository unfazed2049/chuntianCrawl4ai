import unittest
from unittest.mock import AsyncMock, patch

import prefect_flows


class PrefectFlowOutputsTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_single_section_does_not_write_markdown(self):
        fake_result = {
            "success": True,
            "url": "https://example.com/a",
            "extracted_content": "",
            "markdown": "raw markdown",
            "error_message": None,
        }

        with (
            patch.object(
                prefect_flows,
                "crawl_single_page_task",
                new=AsyncMock(return_value=fake_result),
            ),
            patch.object(prefect_flows, "build_output_dir", return_value="/tmp/out"),
            patch.object(prefect_flows, "slug_from_url", return_value="a"),
            patch.object(prefect_flows, "parse_extracted", return_value={}),
            patch.object(
                prefect_flows, "pick_markdown_content", return_value="raw markdown"
            ),
            patch.object(
                prefect_flows, "save_json_task", return_value="/tmp/out/a.json"
            ),
            patch.object(
                prefect_flows,
                "build_meta",
                return_value={"url": "https://example.com/a"},
            ),
        ):
            site = {"name": "site-a"}
            section = {
                "name": "sec-a",
                "mode": "single",
                "single": {"url": "https://example.com/a"},
            }
            out = await prefect_flows.run_single_section_flow.fn(
                crawler=object(),
                site=site,
                section=section,
                llm_cfg={},
                prompts={},
                workspace="w",
            )

        self.assertFalse(hasattr(prefect_flows, "save_markdown_task"))
        self.assertEqual(out, ["/tmp/out/a.json"])

    async def test_crawl_sites_uses_site_level_browser_config(self):
        class DummyCrawlerContext:
            def __init__(self, config):
                self.config = config

            async def __aenter__(self):
                return object()

            async def __aexit__(self, exc_type, exc, tb):
                return False

        config = {
            "sites": [
                {
                    "name": "site-a",
                    "stealth": True,
                    "sections": [
                        {
                            "name": "sec-a",
                            "mode": "single",
                            "single": {"url": "https://example.com"},
                        }
                    ],
                }
            ]
        }

        with (
            patch.object(prefect_flows, "load_config_task", return_value=(config, "w")),
            patch.object(
                prefect_flows,
                "load_app_config",
                return_value={
                    "llm_config": {},
                    "meilisearch_config": None,
                    "redis_bloom_config": {},
                },
            ),
            patch.object(prefect_flows, "load_prompts_task", return_value={}),
            patch.object(
                prefect_flows, "build_browser_config", return_value="browser-cfg"
            ) as mocked_build_browser,
            patch.object(
                prefect_flows,
                "AsyncWebCrawler",
                side_effect=lambda config: DummyCrawlerContext(config),
            ),
            patch.object(
                prefect_flows, "run_section_flow", new=AsyncMock(return_value=[])
            ),
            patch.object(prefect_flows, "index_workspace_flow", return_value=None),
        ):
            await prefect_flows.crawl_sites_flow.fn(
                config_name="default",
                filter_site=None,
                filter_section=None,
            )

        mocked_build_browser.assert_called_once_with({"stealth": True})

    async def test_crawl_sites_indexes_each_section_immediately(self):
        class DummyCrawlerContext:
            async def __aenter__(self):
                return object()

            async def __aexit__(self, exc_type, exc, tb):
                return False

        config = {
            "sites": [
                {
                    "name": "site-a",
                    "sections": [
                        {
                            "name": "sec-1",
                            "mode": "single",
                            "single": {"url": "https://example.com/1"},
                        },
                        {
                            "name": "sec-2",
                            "mode": "single",
                            "single": {"url": "https://example.com/2"},
                        },
                    ],
                }
            ]
        }

        with (
            patch.object(prefect_flows, "load_config_task", return_value=(config, "w")),
            patch.object(
                prefect_flows,
                "load_app_config",
                return_value={
                    "llm_config": {"provider": "x", "api_token": "y"},
                    "meilisearch_config": {"url": "http://meili", "api_key": "k"},
                    "redis_bloom_config": {},
                },
            ),
            patch.object(prefect_flows, "load_prompts_task", return_value={}),
            patch.object(
                prefect_flows, "build_browser_config", return_value="browser-cfg"
            ),
            patch.object(
                prefect_flows,
                "AsyncWebCrawler",
                side_effect=lambda config: DummyCrawlerContext(),
            ),
            patch.object(
                prefect_flows,
                "run_section_flow",
                new=AsyncMock(
                    side_effect=[["/tmp/out/sec-1-a.json"], ["/tmp/out/sec-2-a.json"]]
                ),
            ),
            patch.object(
                prefect_flows, "index_workspace_flow", return_value=None
            ) as mocked_index,
        ):
            await prefect_flows.crawl_sites_flow.fn(
                config_name="default",
                filter_site=None,
                filter_section=None,
            )

        self.assertEqual(mocked_index.call_count, 2)
        self.assertEqual(
            mocked_index.call_args_list[0].kwargs["json_paths"],
            ["/tmp/out/sec-1-a.json"],
        )
        self.assertEqual(
            mocked_index.call_args_list[1].kwargs["json_paths"],
            ["/tmp/out/sec-2-a.json"],
        )


if __name__ == "__main__":
    unittest.main()
