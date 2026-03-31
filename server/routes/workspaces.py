"""
工作空间相关路由
"""

from fastapi import APIRouter
from server.models.search import ApiResponse
from server.utils.meilisearch_client import hybrid_search

router = APIRouter()


@router.get("", response_model=ApiResponse[list[str]])
async def get_workspaces():
    """
    获取工作空间列表

    从所有索引中提取唯一的 workspace 值
    """
    workspaces = set()

    # 从各个索引中获取 workspace
    indexes = ["competitor_profiles", "competitor_news", "industry_news", "trade_shows"]

    for index_name in indexes:
        try:
            result = await hybrid_search(
                index_name=index_name,
                query="",
                limit=100,
            )

            for hit in result["hits"]:
                workspace = hit.get("workspace")
                if workspace:
                    workspaces.add(workspace)
        except:
            # 如果索引不存在或查询失败,跳过
            continue

    # 如果没有找到任何 workspace,返回默认值
    if not workspaces:
        workspaces.add("default")

    return ApiResponse(
        success=True,
        data=sorted(list(workspaces)),
        message="获取成功",
        total=len(workspaces),
    )
