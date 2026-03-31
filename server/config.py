"""
配置管理
复用项目根目录的 app_config.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app_config import load_app_config

# 加载配置
config = load_app_config()

# 导出配置
MEILISEARCH_CONFIG = config["meilisearch_config"]
LLM_CONFIG = config["llm_config"]
REDIS_BLOOM_CONFIG = config["redis_bloom_config"]
