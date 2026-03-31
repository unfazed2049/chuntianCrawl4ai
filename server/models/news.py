"""
新闻数据模型
"""

from typing import Any, Optional
from pydantic import BaseModel


class IndustryNews(BaseModel):
    """行业新闻"""

    id: str
    workspace: str
    url: str
    crawled_at: str
    cleaned_content: str
    raw_content: Optional[str] = None
    category: Optional[str] = None
