"""
统一响应模型
"""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""

    success: bool
    data: Optional[T] = None
    message: str = "操作成功"
    total: Optional[int] = None


class SearchRequest(BaseModel):
    """搜索请求模型"""

    query: str = ""
    workspace: Optional[str] = None
    limit: int = 20
    offset: int = 0
    semantic_ratio: float = 0.4
    filter: Optional[str] = None


class SearchResult(BaseModel):
    """搜索结果模型"""

    hits: list[dict[str, Any]]
    total: int
    limit: int
    offset: int
    processing_time_ms: int
