# 配置迁移指南

## 改动说明

将 `--workspace=` 参数改为 `--config=` 参数，workspace 现在从 config JSON 文件内读取。

## 改动前后对比

### 改动前
```bash
python crawler.py --workspace=hpp
python crawler_prefect.py --workspace=example
```

### 改动后
```bash
python crawler.py --config=hpp
python crawler_prefect.py --config=example
```

## Config JSON 格式变化

每个 config 文件现在需要在顶层加 `workspace` 字段：

```json
{
  "workspace": "hpp",
  "sites": [
    ...
  ]
}
```

## 使用场景

### 同一 workspace，不同定时器跑不同站点

**config/competitor_daily.json**
```json
{
  "workspace": "hpp",
  "sites": [
    {
      "name": "Hiperbaric",
      "competitor_id": "hiperbaric",
      "sections": [...]
    }
  ]
}
```

**config/news_daily.json**
```json
{
  "workspace": "hpp",
  "sites": [
    {
      "name": "食品伙伴网",
      "sections": [...]
    }
  ]
}
```

**Prefect 定时器配置**
```bash
# 定时器 A：每天 2 点跑竞品爬虫
prefect deployment build crawler_prefect.py:crawl_sites_flow \
    -n "competitor-daily" \
    -q "default" \
    --param config_name=competitor_daily

prefect deployment set-schedule competitor-daily --cron "0 2 * * *"

# 定时器 B：每天 8 点跑新闻爬虫
prefect deployment build crawler_prefect.py:crawl_sites_flow \
    -n "news-daily" \
    -q "default" \
    --param config_name=news_daily

prefect deployment set-schedule news-daily --cron "0 8 * * *"
```

两个定时器输出都落到 `output/hpp/`，Redis Bloom key 共享命名空间（自动去重），Meilisearch 写同一索引。

### 不同 workspace，完全隔离

**config/production.json**
```json
{
  "workspace": "prod",
  "sites": [...]
}
```

**config/staging.json**
```json
{
  "workspace": "staging",
  "sites": [...]
}
```

输出路径、Redis key、Meilisearch 索引完全隔离。

## Redis Bloom 过滤配置

### 全局配置

Redis Bloom 过滤器用于避免重复爬取已抓取的详情页。配置在 `.env` 文件中：

```bash
# 启用 Redis Bloom 过滤
REDIS_BLOOM_ENABLED=true

# Redis 连接配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Bloom 过滤器参数
REDIS_BLOOM_KEY_PREFIX=crawl:detail
REDIS_BLOOM_ERROR_RATE=0.001
REDIS_BLOOM_CAPACITY=100000
REDIS_SOCKET_TIMEOUT=3
```

### Section 级别控制

默认情况下，所有 `list` 模式的 section 都会使用 Redis Bloom 过滤。如果需要某个 section 每次都重新爬取（不过滤），可以添加 `skip_bloom_filter` 字段：

**跳过过滤示例：**
```json
{
  "name": "中国食品",
  "mode": "list",
  "skip_bloom_filter": true,
  "list": {
    "pagination": {
      "type": "url_template",
      "url_template": "https://news.foodmate.net/guonei/list_{page}.html",
      "page_start": 1,
      "page_end": 3
    }
  }
}
```

**默认行为（启用过滤）：**
```json
{
  "name": "中国食品",
  "mode": "list",
  "list": {
    "pagination": {...}
  }
}
```

### 工作原理

1. **全局启用** — `.env` 中 `REDIS_BLOOM_ENABLED=true`
2. **Section 默认启用** — 所有 `list` 模式 section 自动使用过滤
3. **Section 可选关闭** — 设置 `"skip_bloom_filter": true` 跳过过滤
4. **命名空间隔离** — Redis key 格式：`{key_prefix}:{workspace}:{site_name}:{section_name}`

### 使用场景

**场景 1：大部分 section 需要去重，个别需要全量抓取**
```json
{
  "workspace": "hpp",
  "sites": [
    {
      "name": "食品伙伴网",
      "sections": [
        {
          "name": "中国食品",
          "mode": "list",
          "list": {...}  // 默认启用过滤
        },
        {
          "name": "国际食品",
          "mode": "list",
          "skip_bloom_filter": true,  // 每次全量抓取
          "list": {...}
        }
      ]
    }
  ]
}
```

**场景 2：同一 workspace 不同 config 共享去重**

`config/competitor_daily.json` 和 `config/news_daily.json` 都设置 `"workspace": "hpp"`，它们的 Redis Bloom key 会共享命名空间，实现跨 config 去重。

### 注意事项

1. **Redis Bloom 配置只能在 `.env` 全局设置**，不支持 section 级别覆盖参数（如 error_rate、capacity）
2. **`crawler.py` 不支持 Redis Bloom**，只有 `crawler_prefect.py` 支持（生产环境使用）
3. **Redis 不可用时自动降级**，会打印警告并继续爬取（不过滤）
4. **`single` 模式不支持过滤**，只有 `list` 模式支持

## 向后兼容

- `utils.py` 导出了 `DEFAULT_WORKSPACE` 常量（值为 `"default"`）保持向后兼容
- 如果 JSON 内没有 `workspace` 字段，会 fallback 到 config 文件名作为 workspace
