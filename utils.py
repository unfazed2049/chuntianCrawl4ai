"""
共享工具函数：配置加载、Prompts 加载
供 prefect_tasks.py 和 meilisearch_tasks.py 共用
"""

from pathlib import Path
import json

CONFIG_DIR = Path("config")
PROMPTS_DIR = Path("prompts")
OUTPUT_ROOT = Path("output")
DEFAULT_CONFIG = "default"
# 保留向后兼容
DEFAULT_WORKSPACE = DEFAULT_CONFIG


def load_config(config_name: str = DEFAULT_CONFIG) -> tuple[dict, str]:
    """从 config/{config_name}.json 加载配置，返回 (config, workspace)。
    workspace 优先取 JSON 内的 "workspace" 字段，缺省时 fallback 到 config_name。
    """
    config_path = CONFIG_DIR / f"{config_name}.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    workspace = config.get("workspace") or config_name
    return config, workspace


def load_prompts() -> dict:
    """加载 prompts/ 目录下所有 Markdown 文件，以文件名为 key"""
    prompts: dict = {}
    if not PROMPTS_DIR.exists():
        return prompts
    for prompt_file in PROMPTS_DIR.glob("*.md"):
        text = prompt_file.read_text(encoding="utf-8").strip()
        prompts[prompt_file.stem] = {"instruction": text}
    return prompts
