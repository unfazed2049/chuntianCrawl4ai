# Crawl4AI API Server

FastAPI 后端服务,提供 RESTful API 接口用于访问 Meilisearch 爬虫数据。

## 功能特性

- RESTful API 设计
- 统一响应格式
- CORS 支持
- 混合搜索(关键词 + 语义搜索)
- 自动 API 文档(Swagger UI)

## 技术栈

- **FastAPI**: 现代、快速的 Python Web 框架
- **Uvicorn**: ASGI 服务器
- **Pydantic**: 数据验证和序列化
- **Meilisearch**: 搜索引擎客户端

## 项目结构

```
server/
├── __init__.py
├── main.py                      # FastAPI 主应用
├── config.py                    # 配置管理
├── models/                      # Pydantic 数据模型
│   ├── __init__.py
│   ├── search.py               # 搜索模型
│   ├── competitor.py           # 竞争对手模型
│   ├── news.py                 # 新闻模型
│   └── tradeshow.py            # 展会模型
├── routes/                      # API 路由
│   ├── __init__.py
│   ├── search.py               # 搜索路由
│   ├── competitors.py          # 竞争对手路由
│   ├── industry_news.py        # 行业新闻路由
│   ├── trade_shows.py          # 展会路由
│   └── workspaces.py           # 工作空间路由
└── utils/                       # 工具函数
    ├── __init__.py
    └── meilisearch_client.py   # Meilisearch 客户端封装
```

## API 端点

### 搜索相关

- `GET /api/search` - 通用搜索接口
  - 参数: `index`, `q`, `workspace`, `limit`, `offset`, `semantic_ratio`

### 竞争对手相关

- `GET /api/competitors` - 获取竞争对手列表
- `GET /api/competitors/{competitor_id}` - 获取竞争对手详情
- `GET /api/competitors/{competitor_id}/news` - 获取竞争对手新闻

### 行业新闻相关

- `GET /api/industry-news` - 获取行业新闻列表
- `GET /api/industry-news/categories` - 获取新闻分类

### 展会信息相关

- `GET /api/trade-shows` - 获取展会列表
- `GET /api/trade-shows/by-month` - 按月份分组获取展会

### 工作空间相关

- `GET /api/workspaces` - 获取工作空间列表

### 其他

- `GET /` - 根路径,返回 API 信息
- `GET /health` - 健康检查
- `GET /docs` - Swagger UI 文档
- `GET /redoc` - ReDoc 文档

## 快速开始

### 1. 安装依赖

```bash
# 使用 pixi (推荐)
pixi install

# 或使用 pip
pip install fastapi uvicorn pydantic meilisearch
```

### 2. 配置环境变量

确保项目根目录的 `.env` 文件已配置:

```env
MEILI_URL=http://localhost:7700
MEILI_API_KEY=your_api_key_here
```

### 3. 启动服务

```bash
# 使用 pixi
pixi run api-serve

# 或直接使用 uvicorn
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动。

### 4. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 统一响应格式

所有 API 端点返回统一的响应格式:

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "total": 100
}
```

## 开发指南

### 添加新端点

1. 在 `server/routes/` 创建新路由文件
2. 定义路由函数和响应模型
3. 在 `server/main.py` 注册路由

示例:

```python
# server/routes/my_route.py
from fastapi import APIRouter
from server.models.search import ApiResponse

router = APIRouter()

@router.get("", response_model=ApiResponse[list])
async def my_endpoint():
    return ApiResponse(
        success=True,
        data=[],
        message="成功",
    )
```

```python
# server/main.py
from server.routes import my_route

app.include_router(my_route.router, prefix="/api/my-route", tags=["我的路由"])
```

### 自定义搜索

修改 `server/utils/meilisearch_client.py` 中的 `hybrid_search` 函数:

```python
result = await hybrid_search(
    index_name="your_index",
    query="search term",
    workspace="default",
    limit=20,
    semantic_ratio=0.4,
)
```

## 常见问题

### 1. 连接不到 Meilisearch

检查 `.env` 文件中的 `MEILI_URL` 和 `MEILI_API_KEY` 是否正确。

### 2. CORS 错误

确保前端地址已添加到 `server/main.py` 的 CORS 配置中:

```python
allow_origins=[
    "http://localhost:5173",  # 添加你的前端地址
]
```

### 3. 模块导入错误

确保从项目根目录运行服务:

```bash
cd /data/chuntianCrawl4ai
uvicorn server.main:app --reload
```

## 部署

### 开发环境

```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境

```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

或使用 Gunicorn:

```bash
gunicorn server.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## License

MIT
