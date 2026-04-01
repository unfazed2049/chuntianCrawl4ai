从输入的展会页面原文中提取结构化信息，返回 JSON。

输入文本可能包含模板噪声（如：页头导航、页脚版权、分享按钮文案、上一篇/下一篇、相关推荐、订阅/关注提示、cookie 提示、联系方式、备案号）。
请先在语义上忽略上述噪声，只基于展会主体内容进行提取（展会名称、时间、地点、主办方、展商与新品等）。
如果无法确认主体内容，允许输出空字符串、空数组或合理缺省值，不要编造。

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
