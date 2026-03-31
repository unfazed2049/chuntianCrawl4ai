# Meilisearch Document Schema

## Index 1: `competitor_profiles`

每个竞争对手一条记录，由汇集脚本从爬取结果中整理后 upsert。
`products / cases / solutions / technologies` 均为数组，支持追加更新。

```json
{
  "id": "string ({workspace}_{competitor_id}，如 default_hiperbaric)",
  "workspace": "string (如 default、production)",
  "competitor_id": "string (纯公司标识，如 hiperbaric，用于跨 workspace 关联)",
  "name": "string (公司名称)",
  "website": "string",
  "country": "string",
  "updated_at": "string (ISO 8601)",

  "products": [
    {
      "model": "string",
      "pressure_range": "string",
      "capacity": "string",
      "energy_consumption": "string",
      "features": ["string"],
      "applications": ["string"],
      "price_range": "string",
      "source_url": "string",
      "raw_content": "string"
    }
  ],

  "cases": [
    {
      "client": "string",
      "industry": "string",
      "effect_data": "string (灭菌率、均质度等效果数据)",
      "source_url": "string",
      "raw_content": "string"
    }
  ],

  "solutions": [
    {
      "target_pain_point": "string (针对的客户痛点)",
      "industries": ["string"],
      "source_url": "string",
      "raw_content": "string"
    }
  ],

  "technologies": [
    {
      "topic": "string (技术主题)",
      "patents": ["string"],
      "certifications": ["string (CE、FDA、ISO 等)"],
      "source_url": "string",
      "raw_content": "string"
    }
  ]
}
```

### Meilisearch 配置建议

```json
{
  "filterableAttributes": ["workspace", "competitor_id", "country"]
}
```

---

## Index 2: `competitor_news`

竞争对手新闻动态，每条新闻一条记录，爬一条插一条。

```json
{
  "id": "string (url hash，url 本身全局唯一，无需加 workspace 前缀)",
  "workspace": "string (如 default、production)",
  "competitor_id": "string (关联 competitor_profiles.competitor_id)",
  "competitor_name": "string",
  "category": "enum: 新品发布 | 公司动态 | 认证奖项 | 招聘信息 | 合作伙伴 | 海外拓展",
  "title": "string",
  "summary": "string",
  "url": "string",
  "published_at": "string (ISO 8601，页面上的发布时间)",
  "crawled_at": "string (爬取时间)",
  "source_section": "string (来自哪个板块，如 产品中心、新闻动态)",
  "tags": ["string"],
  "raw_content": "string"
}
```

### category 说明

| 值 | 含义 |
|---|---|
| `新品发布` | 新品发布、设备升级 |
| `公司动态` | 公司动态、工厂投产、办事处设立 |
| `认证奖项` | 新增认证(CE、FDA、ISO)、行业奖项 |
| `招聘信息` | 招聘信息,用于推断市场拓展和研发方向 |
| `合作伙伴` | 合作伙伴、供应商、联合推广 |
| `海外拓展` | 海外市场拓展 |

### Meilisearch 配置建议

```json
{
  "filterableAttributes": ["workspace", "competitor_id", "category", "published_at", "tags"],
  "sortableAttributes": ["published_at", "crawled_at"]
}
```

---

## Index 3: `trade_shows`

展会信息，每个展会一条记录，来源可以是展会官网或行业媒体报道，通过 `id` 去重合并。

```json
{
  "id": "string (展会唯一标识，如 展会名+年份 的 hash)",
  "workspace": "string (如 default、production)",
  "name": "string (展会名称)",
  "year": "number",
  "start_date": "string (ISO 8601, 如 2025-06-10)",
  "end_date": "string (ISO 8601, 如 2025-06-13)",
  "location": "string (城市/场馆)",
  "organizer": "string (主办方)",
  "website": "string",
  "crawled_at": "string (ISO 8601)",

  "exhibitors": [
    {
      "name": "string (参展商名称)",
      "booth": "string (展位号，如有)",
      "products_showcased": ["string"],
      "raw_content": "string"
    }
  ],

  "new_products": [
    {
      "exhibitor": "string",
      "model": "string",
      "highlights": ["string (核心卖点)"],
      "raw_content": "string"
    }
  ],

  "summary": "string (展会整体摘要)",
  "tags": ["string"],
  "raw_content": "string"
}
```

### Meilisearch 配置建议

`start_date` 和 `end_date` 需设置为 filterable attributes，支持时间范围过滤：

```json
{
  "filterableAttributes": ["workspace", "year", "start_date", "end_date", "location", "tags"]
}
```

---

## Index 4: `industry_news`

行业资讯，每条资讯一条记录。来源包括行业媒体、科研机构、仪器设备类网站等，来源信息写入 `raw_content`。

```json
{
  "id": "string (url hash)",
  "workspace": "string (如 default、production)",
  "title": "string",
  "summary": "string",
  "url": "string",
  "published_at": "string (ISO 8601)",
  "crawled_at": "string (ISO 8601)",
  "category": "enum: 行业资讯 | 食品科技 | 政策法规 | 科研成果 | 市场分析 | 企业资讯",
  "tags": ["string"],
  "raw_content": "string"
}
```

### category 说明

| 值 | 含义 |
|---|---|
| `行业资讯` | 行业媒体的综合资讯 |
| `食品科技` | 食品科技、技术进展 |
| `政策法规` | 政策法规 |
| `科研成果` | 科研机构的科研项目、技术成果 |
| `市场分析` | 市场分析、行业数据 |
| `企业资讯` | 产经企业、企业资讯 |

### Meilisearch 配置建议

```json
{
  "filterableAttributes": ["workspace", "category", "published_at", "tags"],
  "sortableAttributes": ["published_at", "crawled_at"]
}
```

---

## Index 5: `daily_digest`

每日信息汇总，每天一条记录。由汇总脚本从各 index 召回当天相关度高的条目，经 LLM 总结后写入。

```json
{
  "id": "string ({workspace}_{date}，如 default_2026-03-30)",
  "workspace": "string (如 default、production)",
  "date": "string (ISO 8601)",
  "generated_at": "string (ISO 8601)",
  "categories": {
    "政策法规": {
      "summary": "string (LLM 生成的今日政策摘要)",
      "top_items": [
        {
          "title": "string",
          "url": "string",
          "relevance_score": "number"
        }
      ]
    },
    "科研成果": {
      "summary": "string",
      "top_items": [
        {
          "title": "string",
          "url": "string",
          "relevance_score": "number"
        }
      ]
    },
    "食品科技": {
      "summary": "string",
      "top_items": [...]
    },
    "市场分析": {
      "summary": "string",
      "top_items": [...]
    },
    "企业资讯": {
      "summary": "string",
      "top_items": [...]
    },
    "竞争对手动态": {
      "summary": "string",
      "top_items": [...]
    },
    "展会信息": {
      "summary": "string",
      "top_items": [...]
    }
  }
}
```

### 说明

- `categories` 的 key 与 `industry_news.category` 枚举对齐，额外增加 `竞争对手动态` 和 `展会信息`
- `top_items` 保留 `url` 用于溯源，`relevance_score` 为召回时的相关度分数
- `summary` 由 LLM 对召回的 top n 条目内容进行总结生成
- 召回方式可选：Meilisearch 关键词检索（简单）、Meilisearch hybrid search（语义+关键词）、外部向量库（精准但复杂）

---

## 说明

- `competitor_profiles` 中每个子数组项都保留 `raw_content`，方便后续 LLM 二次结构化处理
- `competitor_profiles.id` 格式为 `{workspace}_{competitor_id}`（如 `default_hiperbaric`），`competitor_id` 保留纯公司标识用于跨 workspace 关联
- `competitor_news.competitor_id` 关联 `competitor_profiles.competitor_id`，便于按公司聚合查询
- 所有 index 均含 `workspace` 字段，设为 filterable attribute，支持多项目隔离查询
- `daily_digest.id` 格式为 `{workspace}_{date}`（如 `default_2026-03-30`），同一天不同 workspace 各自独立
- 展会相关内容（含媒体报道的展会动态）统一进 `trade_shows`，不进 `industry_news`
- `daily_digest` 存储 LLM 加工后的结论，与原始 index 不冗余，历史报告可追溯
- 社交媒体、公众号数据暂未纳入，后续扩展时可在 `competitor_profiles` 中增加 `social_media` 数组
