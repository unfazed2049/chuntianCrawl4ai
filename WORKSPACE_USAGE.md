# Workspace 使用说明

## 概述

Workspace 功能允许同一个爬虫程序使用不同的配置文件和输出目录,实现多环境、多项目的隔离管理。

## 目录结构

```
project/
├── config/
│   ├── default.json      # 默认配置
│   ├── example.json      # 示例配置
│   └── production.json   # 生产环境配置
├── prompts/
│   ├── default.json      # 默认提取 prompt
│   ├── news_article.json # 新闻文章 prompt
│   └── product_page.json # 产品页面 prompt
└── output/
    ├── default/          # 默认 workspace 输出
    │   └── 20260330/
    ├── example/          # example workspace 输出
    │   └── 20260330/
    └── production/       # production workspace 输出
        └── 20260330/
```

## 使用方法

### 1. 创建配置文件

在 `config/` 目录下创建新的配置文件,例如 `config/myproject.json`:

```json
{
  "sites": [ ... ]
}
```

**注意**:
- `config/` 只放爬取目标与规则（sites/sections/list/single）
- 应用级配置（LLM、Redis Bloom、Meilisearch）放在项目根目录 `.env`
- prompts 放在 `prompts/` 目录

### 2. 配置应用级 .env

复制 `.env.example` 为 `.env`，并填写实际值:

```bash
cp .env.example .env
```

关键变量：
- `LLM_PROVIDER`
- `LLM_API_TOKEN`
- `LLM_BASE_URL`（可选）
- `REDIS_BLOOM_*`（详情页二次爬取去重）
- `MEILI_*`（Meilisearch 连接与 hybrid 检索）

### 3. 创建 Prompt 文件

在 `prompts/` 目录下创建 Markdown prompt 文件，例如 `prompts/my_prompt.md`:

```markdown
Extract page content and return JSON only.

Rules:
- Keep body in `content_markdown`
- Preserve image references `![alt](url)`
- Keep paragraph formatting
```

然后在配置文件的 section 中引用该 prompt:

```json
{
  "name": "新闻列表",
  "mode": "list",
  "prompt": "my_prompt",
  ...
}
```

### 4. 运行爬虫

#### 使用默认 workspace (default)
```bash
python crawler.py
```

#### 指定 workspace
```bash
python crawler.py --workspace=myproject
```

#### 指定 workspace 并过滤站点
```bash
python crawler.py --workspace=myproject 站点名称
```

#### 指定 workspace、站点和章节
```bash
python crawler.py --workspace=myproject 站点名称 章节名称
```

### 3. 输出目录

输出文件将保存在 `output/{workspace}/{日期}/` 目录下:

- `output/default/20260330/` - 默认 workspace 的输出
- `output/myproject/20260330/` - myproject workspace 的输出

## 命令行参数

- `--workspace=<name>`: 指定使用的 workspace 名称 (默认: default)
- `<site_name>`: 可选,只运行指定站点
- `<section_name>`: 可选,只运行指定章节 (需要同时指定站点)

## 示例

### 示例 1: 开发环境和生产环境分离

```bash
# 开发环境
python crawler.py --workspace=dev

# 生产环境
python crawler.py --workspace=production
```

### 示例 2: 不同项目使用不同配置

```bash
# 项目 A
python crawler.py --workspace=projectA

# 项目 B
python crawler.py --workspace=projectB
```

### 示例 3: 测试特定站点

```bash
# 使用 test workspace 测试特定站点
python crawler.py --workspace=test 中国农业大学 科学研究
```

## 注意事项

1. 配置文件必须放在 `config/` 目录下
2. 配置文件名格式为 `{workspace}.json`
3. Prompt 文件必须放在 `prompts/` 目录下
4. Prompt 文件名格式为 `{prompt_name}.md`
5. 如果指定的 workspace 配置文件不存在,程序会报错并退出
6. 每个 workspace 的输出目录相互独立,不会互相影响
7. 所有 workspace 共享同一个 `prompts/` 目录中的 prompt 文件

## Prompts 目录说明

### Prompts 的作用

Prompts 定义了如何从网页中提取数据。每个 prompt 为 Markdown 指令文本。

说明：
- schema 不写在 prompt 文件里
- schema 统一在代码中定义（`schemas.py`）

### 可用的 Prompt 文件

- `default.md`: 默认提取 prompt
- `news_article.md`: 新闻文章 prompt
- `product_page.md`: 产品页面 prompt

### 创建自定义 Prompt

在 `prompts/` 目录下创建新的 Markdown 文件:

```markdown
Extract page content and return JSON only.

Rules:
- Keep body in `content_markdown`
- Preserve image references `![alt](url)`
- Keep paragraph formatting
```

然后在配置文件的 section 中引用:

```json
{
  "name": "产品列表",
  "mode": "list",
  "prompt": "my_custom_prompt",
  ...
}
```

### 向后兼容

如果您的配置文件中仍然包含 `prompts` 字段，程序会继续工作，但会显示提示建议迁移到 `prompts/` 目录。
