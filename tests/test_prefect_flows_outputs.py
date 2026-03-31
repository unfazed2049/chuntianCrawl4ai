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


if __name__ == "__main__":
    unittest.main()
