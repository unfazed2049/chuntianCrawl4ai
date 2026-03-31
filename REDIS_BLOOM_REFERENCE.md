# Redis Bloom 过滤快速参考

## 配置位置

### 全局配置（.env）
```bash
REDIS_BLOOM_ENABLED=true          # 启用/禁用
REDIS_HOST=127.0.0.1              # Redis 服务器
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=                   # 可选
REDIS_BLOOM_KEY_PREFIX=crawl:detail
REDIS_BLOOM_ERROR_RATE=0.001      # 误判率
REDIS_BLOOM_CAPACITY=100000       # 容量
```

### Section 配置（config/*.json）
```json
{
  "name": "section_name",
  "mode": "list",
  "skip_bloom_filter": true,  // 可选，默认 false
  "list": {...}
}
```

## 行为矩阵

| 全局 ENABLED | skip_bloom_filter | 结果 |
|-------------|-------------------|------|
| true        | false (默认)       | ✅ 启用过滤 |
| true        | true              | ❌ 跳过过滤 |
| false       | false             | ❌ 跳过过滤 |
| false       | true              | ❌ 跳过过滤 |

## Redis Key 格式

```
{key_prefix}:{workspace}:{site_name}:{section_name}
```

**示例：**
```
crawl:detail:hpp:食品伙伴网:中国食品
```

## 日志输出

### 启用过滤
```
  共收集 50 个详情页 URL
  [启用] Redis Bloom 过滤
  Redis Bloom 过滤后待爬取 12 个（跳过已爬取 38 个）
```

### 跳过过滤（section 配置）
```
  共收集 50 个详情页 URL
  [跳过] Redis Bloom 过滤已禁用（section 配置）
```

### Redis 不可用
```
  共收集 50 个详情页 URL
  [警告] Redis Bloom 已配置但不可用
```

## 使用场景

### 场景 1：定期增量抓取
```json
{
  "name": "新闻列表",
  "mode": "list",
  "list": {...}  // 默认启用，只抓新文章
}
```

### 场景 2：每次全量抓取
```json
{
  "name": "产品目录",
  "mode": "list",
  "skip_bloom_filter": true,  // 每次都重新抓取
  "list": {...}
}
```

### 场景 3：混合策略
```json
{
  "sites": [
    {
      "name": "新闻站",
      "sections": [
        {
          "name": "今日头条",
          "mode": "list",
          "skip_bloom_filter": true,  // 每次全抓
          "list": {...}
        },
        {
          "name": "历史新闻",
          "mode": "list",
          "list": {...}  // 增量抓取
        }
      ]
    }
  ]
}
```

## 注意事项

1. **只支持 Prefect 版本** — `crawler.py` 不支持 Redis Bloom
2. **只支持 list 模式** — `single` 模式不需要过滤
3. **自动降级** — Redis 不可用时自动跳过过滤，不影响爬取
4. **命名空间隔离** — 不同 workspace 的 Redis key 完全隔离
5. **跨 config 共享** — 同一 workspace 的不同 config 共享去重状态

## 清理 Redis 数据

### 清理特定 section
```bash
redis-cli DEL "crawl:detail:hpp:食品伙伴网:中国食品"
```

### 清理整个 workspace
```bash
redis-cli --scan --pattern "crawl:detail:hpp:*" | xargs redis-cli DEL
```

### 查看 key 信息
```bash
# 查看 key 是否存在
redis-cli EXISTS "crawl:detail:hpp:食品伙伴网:中国食品"

# 查看 Bloom 过滤器信息
redis-cli BF.INFO "crawl:detail:hpp:食品伙伴网:中国食品"
```

## 示例配置

完整示例见 `config/example_bloom.json`
