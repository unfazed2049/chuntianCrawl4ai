# Prefect 架构使用指南

本文档说明如何使用基于 Prefect 的爬虫架构。

## 架构概述

爬虫已被重构为基于 Prefect 的任务和工作流架构，提供以下优势：

- **任务可观测性**: 通过 Prefect UI 查看任务执行状态和日志
- **任务重试**: 自动重试失败的任务
- **并行执行**: 支持并行执行多个任务
- **任务依赖管理**: 自动管理任务之间的依赖关系
- **调度**: 支持定时执行爬虫任务

## 文件结构

```
.
├── prefect_tasks.py      # 定义所有 Prefect tasks
├── prefect_flows.py      # 定义 Prefect flows（工作流）
├── crawler_prefect.py    # 基于 Prefect 的入口文件
├── crawler.py            # 原始爬虫文件（保留用于向后兼容）
├── config/               # 配置文件目录
├── prompts/              # 提示词目录
└── output/               # 输出目录
```

## 核心组件

### Tasks (prefect_tasks.py)

定义了以下 Prefect tasks：

1. **配置加载 Tasks**
   - `load_prompts_task()`: 加载 prompts 目录中的所有提示词
   - `load_config_task(workspace)`: 加载指定 workspace 的配置文件

2. **URL 收集 Tasks**
   - `collect_urls_url_template_task()`: 使用 URL 模板翻页收集链接
   - `collect_urls_js_pagination_task()`: 使用 JS 翻页收集链接

3. **爬取 Tasks**
   - `crawl_detail_pages_task()`: 批量爬取详情页
   - `crawl_single_page_task()`: 爬取单个页面

4. **保存 Tasks**
   - `save_markdown_task()`: 保存提取结果为 markdown 文件

### Flows (prefect_flows.py)

定义了以下 Prefect flows：

1. **run_list_section_flow**: LIST 模式工作流
   - 收集列表页链接
   - 批量爬取详情页
   - 保存结果

2. **run_single_section_flow**: SINGLE 模式工作流
   - 爬取单个页面
   - 保存结果

3. **run_section_flow**: Section 工作流
   - 根据 section 的 mode 选择对应的 flow

4. **crawl_sites_flow**: 主工作流
   - 加载配置和 prompts
   - 遍历站点和 sections
   - 执行爬取任务

## 使用方法

### 1. 安装依赖

```bash
pip install prefect crawl4ai
```

### 2. 基本使用

先配置应用级环境变量：

```bash
cp .env.example .env
```

使用默认 workspace 运行所有站点：

```bash
python crawler_prefect.py
```

### 3. 指定 Workspace

```bash
python crawler_prefect.py --workspace=example
```

### 4. 过滤站点和 Section

只爬取特定站点：

```bash
python crawler_prefect.py example_site
```

只爬取特定站点的特定 section：

```bash
python crawler_prefect.py example_site news
```

结合 workspace 使用：

```bash
python crawler_prefect.py --workspace=example example_site news
```

## Prefect UI

### 启动 Prefect Server

```bash
prefect server start
```

访问 http://localhost:4200 查看 Prefect UI。

### 查看任务执行

在 Prefect UI 中，你可以：

- 查看所有 flow runs 的状态
- 查看每个 task 的执行日志
- 查看任务执行时间和性能指标
- 重新运行失败的任务

## 高级功能

### 1. 任务重试

在 `prefect_tasks.py` 中，你可以为任务添加重试配置：

```python
from prefect import task
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(
    name="crawl_detail_pages",
    tags=["crawl", "detail"],
    retries=3,
    retry_delay_seconds=60,
)
async def crawl_detail_pages_task(...):
    ...
```

### 2. 任务缓存

为任务添加缓存以避免重复执行：

```python
@task(
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
)
def load_config_task(workspace: str):
    ...
```

### 3. 并行执行

修改 `prefect_flows.py` 中的 flow 以支持并行执行：

```python
from prefect import flow
from prefect.task_runners import ConcurrentTaskRunner

@flow(
    name="crawl_sites",
    task_runner=ConcurrentTaskRunner(),
)
async def crawl_sites_flow(...):
    ...
```

### 4. 定时执行

创建一个部署并设置定时执行：

```bash
# 创建部署
prefect deployment build crawler_prefect.py:crawl_sites_flow \
    -n "daily-crawl" \
    -q "default"

# 设置定时执行（每天凌晨 2 点）
prefect deployment set-schedule daily-crawl --cron "0 2 * * *"

# 启动 agent
prefect agent start -q default
```

## 与原始 crawler.py 的对比

| 特性 | crawler.py | crawler_prefect.py |
|------|-----------|-------------------|
| 任务可观测性 | ❌ | ✅ |
| 任务重试 | ❌ | ✅ |
| 并行执行 | ❌ | ✅ |
| 任务依赖管理 | 手动 | 自动 |
| 定时执行 | 需要 cron | 内置支持 |
| UI 界面 | ❌ | ✅ |
| 向后兼容 | ✅ | ✅ |

## 迁移指南

如果你正在使用原始的 `crawler.py`，可以按照以下步骤迁移到 Prefect 架构：

1. 安装 Prefect: `pip install prefect`
2. 使用 `crawler_prefect.py` 替代 `crawler.py`
3. 命令行参数保持不变
4. 配置文件和 prompts 目录无需修改

## 故障排查

### 问题：任务执行失败

**解决方案**：
1. 检查 Prefect UI 中的任务日志
2. 确认配置文件和 prompts 文件格式正确
3. 检查网络连接和 API 密钥

### 问题：无法访问 Prefect UI

**解决方案**：
1. 确认 Prefect Server 已启动: `prefect server start`
2. 检查端口 4200 是否被占用
3. 尝试访问 http://127.0.0.1:4200

### 问题：任务执行缓慢

**解决方案**：
1. 启用并行执行（参见"高级功能"部分）
2. 调整 `ConcurrentTaskRunner` 的并发数
3. 优化爬取配置（减少等待时间等）

## 最佳实践

1. **使用 Prefect UI 监控任务**: 定期检查任务执行状态和日志
2. **配置任务重试**: 为网络请求相关的任务配置重试机制
3. **使用任务缓存**: 为配置加载等任务启用缓存
4. **合理设置并发**: 根据目标网站的负载能力调整并发数
5. **定期清理输出**: 定期清理 `output/` 目录中的旧文件

## 参考资源

- [Prefect 官方文档](https://docs.prefect.io/)
- [Crawl4ai 文档](https://crawl4ai.com/docs)
- [Workspace 使用指南](./WORKSPACE_USAGE.md)
