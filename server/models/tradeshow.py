"""
展会数据模型
"""

from typing import Any, Optional
from pydantic import BaseModel


class TradeShow(BaseModel):
    """展会信息"""

    id: str
    workspace: str
    crawled_at: str
    cleaned_content: str
    raw_content: Optional[str] = None
    name: str
    year: int
    month: Optional[int] = None
