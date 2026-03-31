"""
竞争对手数据模型
"""

from typing import Any, Optional
from pydantic import BaseModel


class CompetitorProfile(BaseModel):
    """竞争对手档案"""

    id: str
    workspace: str
    competitor_id: str
    name: str
    website: str
    country: str
    updated_at: str
    products: list[Any] = []
    cases: list[Any] = []
    solutions: list[Any] = []
    technologies: list[Any] = []


class CompetitorNews(BaseModel):
    """竞争对手新闻"""

    id: str
    workspace: str
    competitor_id: str
    competitor_name: str
    url: str
    crawled_at: str
    source_section: str
    cleaned_content: str
    raw_content: Optional[str] = None
