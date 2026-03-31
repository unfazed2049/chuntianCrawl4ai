import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
PROMPTS_DIR = ROOT / "prompts"


def _iter_prompt_keys_from_config() -> set[str]:
    prompt_keys: set[str] = set()
    for cfg_file in CONFIG_DIR.glob("*.json"):
        data = json.loads(cfg_file.read_text(encoding="utf-8"))
        for site in data.get("sites", []):
            for section in site.get("sections", []):
                key = section.get("prompt")
                if key:
                    prompt_keys.add(key)
    return prompt_keys


class PromptFilesTests(unittest.TestCase):
    def test_all_prompt_keys_referenced_by_config_exist(self):
        missing = []
        for key in sorted(_iter_prompt_keys_from_config()):
            prompt_path = PROMPTS_DIR / f"{key}.md"
            if not prompt_path.exists():
                missing.append(key)
        self.assertEqual(missing, [], f"missing prompts: {missing}")

    def test_crawl_prompts_keep_markdown_images_and_paragraphs(self):
        crawl_prompt_names = [
            "default",
            "news_article",
            "product_page",
            "competitor_product",
            "competitor_case",
            "competitor_news",
        ]

        for name in crawl_prompt_names:
            prompt_path = PROMPTS_DIR / f"{name}.md"
            self.assertTrue(prompt_path.exists(), f"prompt not found: {name}")
            instruction = prompt_path.read_text(encoding="utf-8").lower()
            self.assertIn(
                "markdown", instruction, f"{name} instruction should require markdown"
            )
            self.assertTrue(
                ("![" in instruction) or ("image" in instruction),
                f"{name} instruction should mention image references",
            )
            self.assertTrue(
                ("paragraph" in instruction) or ("段落" in instruction),
                f"{name} instruction should mention paragraph format",
            )

            self.assertIn("content_markdown", instruction)
            self.assertIn("images", instruction)

    def test_competitor_crawl_prompts_are_content_first_not_domain_structured(self):
        for name in ["competitor_product", "competitor_case", "competitor_news"]:
            prompt_path = PROMPTS_DIR / f"{name}.md"
            self.assertTrue(prompt_path.exists(), f"prompt not found: {name}")
            instruction = prompt_path.read_text(encoding="utf-8").lower()

            forbidden_terms = {
                "client",
                "industry",
                "effect_data",
                "pressure_range",
                "capacity",
                "energy_consumption",
                "price_range",
                "category",
            }
            self.assertFalse(
                any(term in instruction for term in forbidden_terms),
                f"{name} should not require domain-structured keys in crawl stage",
            )


if __name__ == "__main__":
    unittest.main()
