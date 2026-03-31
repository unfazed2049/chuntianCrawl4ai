从输入的展会页面原文中提取结构化信息，返回 JSON。

必须输出字段：
- `name`
- `year`
- `start_date`
- `end_date`
- `location`
- `organizer`
- `website`
- `exhibitors`
- `new_products`
- `summary`
- `tags`

其中 `start_date`/`end_date` 为 ISO 8601，无则空字符串。
`exhibitors` 和 `new_products` 输出数组。

只返回 JSON，不要解释。
