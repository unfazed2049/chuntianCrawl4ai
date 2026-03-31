# Daily Digest 写入方案

## 整体流程

```
每日爬取完成
    ↓
按 category 从各 index 召回当天数据
    ↓
关键词过滤，取 top n 相关条目
    ↓
LLM 对每个 category 生成摘要
    ↓
写入 daily_digest index
```

## 召回策略

每个 category 独立查询，查询条件：

- `industry_news`：按 `published_at` 过滤当天 + `category` 过滤
- `competitor_news`：按 `crawled_at` 过滤当天
- `trade_shows`：按 `start_date <= today <= end_date` 过滤进行中展会，或 `crawled_at` 过滤当天新增

关键词建议围绕核心业务词（如 HPP、超高压、灭菌、食品安全等）做相关度排序，取 top 5~10 条。

## LLM 总结

每个 category 将 top n 条目的 `title` + `summary` 拼接后送入 LLM，prompt 示例：

```
以下是今日{category}相关资讯，请用 3-5 句话总结核心信息：

1. {title}: {summary}
2. {title}: {summary}
...

要求：突出与 HPP 超高压设备行业相关的关键信息。
```

## 写入时机

建议每天固定时间跑（如凌晨爬取完成后），用当天日期作为 `id` upsert，重复运行会覆盖当天记录。

## 降级处理

- 某个 category 当天无数据 → 该 category 不写入 `categories`，跳过
- LLM 调用失败 → `summary` 写入空字符串，`top_items` 仍正常写入
- 召回条目数不足 → 有多少写多少，不强制 top n
