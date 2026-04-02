"""
FastAPI 主应用
提供 RESTful API 接口用于前端访问 Meilisearch 数据
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routes import search, competitors, industry_news, trade_shows, workspaces
from server.utils.meilisearch_client import (
    ensure_filterable_attributes_for_known_indexes,
)

app = FastAPI(
    title="Crawl4AI Data API",
    description="API 服务用于访问 Meilisearch 爬虫数据",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite 开发服务器
        "http://localhost:3000",  # 备用端口
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(search.router, prefix="/api/search", tags=["搜索"])
app.include_router(competitors.router, prefix="/api/competitors", tags=["竞争对手"])
app.include_router(industry_news.router, prefix="/api/industry-news", tags=["行业新闻"])
app.include_router(trade_shows.router, prefix="/api/trade-shows", tags=["展会信息"])
app.include_router(workspaces.router, prefix="/api/workspaces", tags=["工作空间"])


@app.on_event("startup")
async def bootstrap_meilisearch_settings():
    try:
        ensure_filterable_attributes_for_known_indexes()
    except Exception as error:
        print(f"[warn] failed to bootstrap meilisearch filter settings: {error}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "success": True,
        "message": "Crawl4AI Data API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"success": True, "status": "healthy"}
