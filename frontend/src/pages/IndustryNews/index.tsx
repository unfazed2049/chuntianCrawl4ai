import { type FormEvent, useEffect, useMemo, useState } from 'react';
import { ExternalLink, Search } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { hybridSearch } from '../../api/meilisearch';
import { Button } from '../../components/ui/button';
import { ContentCard } from '../../components/ui/content-card';
import { EmptyState } from '../../components/ui/empty-state';
import { Input } from '../../components/ui/input';
import { PageHeader } from '../../components/ui/page-header';
import { Skeleton } from '../../components/ui/skeleton';
import { StatCard } from '../../components/ui/stat-card';
import { cn } from '../../lib/utils';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import type { IndustryNews } from '../../types';

const NEWS_DATE_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  dateStyle: 'medium',
  timeStyle: 'short',
});

function groupNewsByCategory(items: IndustryNews[]) {
  const grouped: Record<string, IndustryNews[]> = {};
  const categoryOrder: string[] = [];

  for (const item of items) {
    const category = item.category?.trim() || '未分类';

    if (!grouped[category]) {
      grouped[category] = [];
      categoryOrder.push(category);
    }

    grouped[category].push(item);
  }

  return { grouped, categoryOrder };
}

function getHostname(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return '外部来源';
  }
}

function getHeadline(item: IndustryNews) {
  const candidate = [item.title, item.headline, item.name]
    .find((value) => typeof value === 'string' && value.trim().length > 0);

  return candidate?.trim() || getHostname(item.url);
}

function getSummary(item: IndustryNews) {
  const text = item.cleaned_content?.trim() || item.raw_content?.trim() || '暂无摘要。';
  return text.length > 320 ? `${text.slice(0, 320)}…` : text;
}

function NewsCardSkeleton() {
  return (
    <div className="rounded-3xl border border-slate-200/70 bg-white/70 p-6">
      <Skeleton className="h-4 w-24 rounded-full" />
      <Skeleton className="mt-4 h-7 w-2/3 rounded-xl" />
      <Skeleton className="mt-3 h-4 w-48 rounded-lg bg-slate-100" />
      <div className="mt-5 space-y-2">
        <Skeleton className="h-4 w-full rounded-lg bg-slate-100" />
        <Skeleton className="h-4 w-full rounded-lg bg-slate-100" />
        <Skeleton className="h-4 w-4/5 rounded-lg bg-slate-100" />
      </div>
    </div>
  );
}

export default function IndustryNewsPage() {
  const { currentWorkspace } = useWorkspaceStore();
  const [searchInput, setSearchInput] = useState('');
  const [activeQuery, setActiveQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string>('全部');
  const [categories, setCategories] = useState<string[]>([]);
  const [newsData, setNewsData] = useState<Record<string, IndustryNews[]>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void loadIndustryNews('');
  }, [currentWorkspace]);

  async function loadIndustryNews(query: string) {
    setLoading(true);

    try {
      const result = await hybridSearch<IndustryNews>('industry_news', {
        query,
        filter: `workspace = "${currentWorkspace}"`,
        limit: 200,
        semanticRatio: query ? 0.4 : undefined,
      });

      const { grouped, categoryOrder } = groupNewsByCategory(result.hits);
      setCategories(categoryOrder);
      setNewsData(grouped);
      setActiveCategory((previous) => {
        if (previous === '全部') {
          return '全部';
        }

        return categoryOrder.includes(previous) ? previous : '全部';
      });
    } catch (error) {
      console.error('加载行业新闻失败:', error);
      setCategories([]);
      setNewsData({});
    } finally {
      setLoading(false);
    }
  }

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextQuery = searchInput.trim();
    setActiveQuery(nextQuery);
    void loadIndustryNews(nextQuery);
  }

  const totalCount = useMemo(
    () => Object.values(newsData).reduce((sum, items) => sum + items.length, 0),
    [newsData]
  );

  const categoryOptions = useMemo(() => ['全部', ...categories], [categories]);

  const visibleSections = useMemo(() => {
    if (activeCategory === '全部') {
      return categories.map((category) => ({
        category,
        items: newsData[category] || [],
      }));
    }

    return [
      {
        category: activeCategory,
        items: newsData[activeCategory] || [],
      },
    ];
  }, [activeCategory, categories, newsData]);

  return (
    <div className="px-4 py-6 lg:px-8 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <PageHeader
          eyebrow="Industry Signals"
          title="更适合阅读与筛选的行业资讯流"
          description="围绕当前工作空间聚合行业新闻，按主题分组展示，并保留搜索入口，减少后台组件感和信息噪声。"
          stats={(
            <>
              <StatCard label="Workspace" value={currentWorkspace} />
              <StatCard label="Categories" value={categories.length} />
              <StatCard label="Articles" value={totalCount} />
            </>
          )}
          actions={(
            <>
              <form className="flex flex-col gap-3 lg:flex-row" onSubmit={handleSearchSubmit}>
                <label className="sr-only" htmlFor="industry-news-search">
                  搜索行业新闻
                </label>
                <div className="relative flex-1">
                  <Search
                    className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    aria-hidden="true"
                  />
                  <Input
                    id="industry-news-search"
                    name="industry-news-search"
                    autoComplete="off"
                    className="pl-11"
                    placeholder="搜索行业新闻、主题或关键词…"
                    value={searchInput}
                    onChange={(event) => setSearchInput(event.target.value)}
                  />
                </div>
                <Button type="submit" className="h-11 rounded-xl px-5">
                  搜索资讯
                </Button>
              </form>

              <div className="mt-4 flex flex-wrap gap-2">
                {categoryOptions.map((category) => (
                  <Button
                    key={category}
                    type="button"
                    variant={activeCategory === category ? 'default' : 'outline'}
                    size="sm"
                    className={cn(
                      'rounded-full',
                      activeCategory === category && 'bg-sky-600 hover:bg-sky-700'
                    )}
                    onClick={() => setActiveCategory(category)}
                  >
                    {category}
                  </Button>
                ))}
              </div>

              {activeQuery ? (
                <p className="mt-4 text-sm text-slate-500">
                  当前搜索词: <span className="font-medium text-slate-800">{activeQuery}</span>
                </p>
              ) : null}
            </>
          )}
        />

        {loading ? (
          <section className="grid gap-4 lg:grid-cols-2">
            <NewsCardSkeleton />
            <NewsCardSkeleton />
            <NewsCardSkeleton />
            <NewsCardSkeleton />
          </section>
        ) : totalCount === 0 ? (
          <EmptyState
            icon={<Search className="h-5 w-5" aria-hidden="true" />}
            title="没有匹配的行业资讯"
            description="调整关键词，或者切换工作空间后重试。当前结果为空时不再显示空白列表。"
          />
        ) : (
          visibleSections.map(({ category, items }) => (
            <section key={category} className="space-y-4">
              <div className="flex items-center justify-between px-1">
                <div>
                  <h3 className="text-xl font-semibold tracking-tight text-slate-950">{category}</h3>
                  <p className="mt-1 text-sm text-slate-500">{items.length} 条资讯</p>
                </div>
              </div>

              <div className="grid gap-4 xl:grid-cols-2">
                {items.map((item) => (
                  <ContentCard
                    key={item.id}
                    topBar={(
                      <>
                        <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                          {getHostname(item.url)}
                        </span>
                        <span className="text-xs font-medium text-slate-400">
                          {NEWS_DATE_FORMATTER.format(new Date(item.crawled_at))}
                        </span>
                      </>
                    )}
                    title={(
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group inline-flex items-start gap-2 text-left text-xl font-semibold leading-8 text-slate-950 transition-colors hover:text-sky-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2"
                      >
                        <span className="text-balance">{getHeadline(item)}</span>
                        <ExternalLink className="mt-1 h-4 w-4 shrink-0 text-slate-400 transition-colors group-hover:text-sky-600" aria-hidden="true" />
                      </a>
                    )}
                    meta={<p className="text-sm leading-6 text-slate-500">原始链接: {item.url}</p>}
                    content={<ReactMarkdown>{getSummary(item)}</ReactMarkdown>}
                  />
                ))}
              </div>
            </section>
          ))
        )}
      </div>
    </div>
  );
}
