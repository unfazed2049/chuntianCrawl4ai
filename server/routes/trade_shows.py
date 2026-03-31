"""
展会信息相关路由
"""

from fastapi import APIRouter, Query
from server.models.search import ApiResponse
from server.models.tradeshow import TradeShow
from server.utils.meilisearch_client import hybrid_search
from collections import defaultdict
from datetime import datetime

router = APIRouter()


@router.get("", response_model=ApiResponse[list[TradeShow]])
async def get_trade_shows(
    workspace: str = Query("default", description="工作空间"),
    year: int = Query(None, description="年份"),
    limit: int = Query(100, ge=1, le=200, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """获取展会信息列表"""
    filter_expr = None
    if year:
        filter_expr = f"year = {year}"

    result = await hybrid_search(
        index_name="trade_shows",
        query="",
        workspace=workspace,
        filter_expr=filter_expr,
        limit=limit,
        offset=offset,
    )

    # 按爬取时间排序(最新的在前面)
    sorted_hits = sorted(
        result["hits"], key=lambda x: x.get("crawled_at", ""), reverse=True
    )

    return ApiResponse(
        success=True,
        data=sorted_hits,
        message="获取成功",
        total=result["estimatedTotalHits"],
    )


@router.get("/by-month", response_model=ApiResponse[dict])
async def get_trade_shows_by_month(
    workspace: str = Query("default", description="工作空间"),
    limit: int = Query(200, ge=1, le=500, description="返回数量"),
):
    """按月份分组获取展会信息"""
    result = await hybrid_search(
        index_name="trade_shows",
        query="",
        workspace=workspace,
        limit=limit,
    )

    # 按爬取时间排序(最新的在前面)
    sorted_hits = sorted(
        result["hits"], key=lambda x: x.get("crawled_at", ""), reverse=True
    )

    # 按月份分组
    grouped = defaultdict(list)
    for show in sorted_hits:
        crawled_at = show.get("crawled_at", "")
        if crawled_at:
            try:
                dt = datetime.fromisoformat(crawled_at.replace("Z", "+00:00"))
                month_key = dt.strftime("%Y-%m")
                grouped[month_key].append(show)
            except:
                grouped["未知"].append(show)

    # 按月份键排序(最新的在前面)
    sorted_grouped = dict(sorted(grouped.items(), reverse=True))

    return ApiResponse(
        success=True,
        data=sorted_grouped,
        message="获取成功",
        total=len(sorted_grouped),
    )
