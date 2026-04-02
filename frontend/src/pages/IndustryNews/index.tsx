import { type FormEvent, useEffect, useMemo, useState } from "react";
import { ExternalLink, Search, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { hybridSearch } from "../../api/meilisearch";
import { Button } from "../../components/ui/button";
import { ContentCard } from "../../components/ui/content-card";
import { EmptyState } from "../../components/ui/empty-state";
import { Input } from "../../components/ui/input";
import { PageHeader } from "../../components/ui/page-header";
import { Skeleton } from "../../components/ui/skeleton";
import { cn } from "../../lib/utils";
import { useWorkspaceStore } from "../../stores/workspaceStore";
import type { IndustryNews } from "../../types";

const NEWS_DATE_FORMATTER = new Intl.DateTimeFormat("zh-CN", {
  dateStyle: "medium",
  timeStyle: "short",
});

function groupNewsByCategory(items: IndustryNews[]) {
  const grouped: Record<string, IndustryNews[]> = {};
  const categoryOrder: string[] = [];

  for (const item of items) {
    const category = item.category?.trim() || "未分类";

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
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "外部来源";
  }
}

function getHeadline(item: IndustryNews) {
  const candidate = [item.title, item.headline, item.name].find(
    (value) => typeof value === "string" && value.trim().length > 0,
  );

  return candidate?.trim() || getHostname(item.url);
}

function getSourceSiteName(item: IndustryNews) {
  const siteName =
    typeof item.site_name === "string" ? item.site_name.trim() : "";
  return siteName || getHostname(item.url);
}

function getSummary(item: IndustryNews) {
  const text =
    item.cleaned_content?.trim() || item.raw_content?.trim() || "暂无摘要。";
  return text.length > 320 ? `${text.slice(0, 320)}…` : text;
}

function buildPreviewMarkdown(item: IndustryNews) {
  const raw = item.raw_content?.trim();
  const cleaned = item.cleaned_content?.trim();
  const base = raw || cleaned || "暂无内容。";

  if (base.includes("\\n") && !base.includes("\n")) {
    return base.replaceAll("\\n", "\n");
  }

  return base;
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
  const [searchInput, setSearchInput] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("全部");
  const [categories, setCategories] = useState<string[]>([]);
  const [newsData, setNewsData] = useState<Record<string, IndustryNews[]>>({});
  const [loading, setLoading] = useState(false);
  const [previewArticle, setPreviewArticle] = useState<IndustryNews | null>(
    null,
  );

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setPreviewArticle(null);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    void loadIndustryNews(activeQuery, activeCategory);
  }, [activeCategory, activeQuery, currentWorkspace]);

  async function loadIndustryNews(query: string, category: string) {
    setLoading(true);

    try {
      const categoryFilter =
        category !== "全部"
          ? `category = "${category.replaceAll('"', '\\"')}"`
          : undefined;

      const result = await hybridSearch<IndustryNews>("industry_news", {
        query,
        workspace: currentWorkspace,
        filter: categoryFilter,
        limit: 100,
        semanticRatio: query ? 0.4 : undefined,
      });

      const { grouped, categoryOrder } = groupNewsByCategory(result.hits);
      if (category === "全部") {
        setCategories(categoryOrder);
      }
      setNewsData(grouped);
    } catch (error) {
      console.error("加载行业新闻失败:", error);
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
  }

  const totalCount = useMemo(
    () => Object.values(newsData).reduce((sum, items) => sum + items.length, 0),
    [newsData],
  );

  const categoryOptions = useMemo(() => ["全部", ...categories], [categories]);

  const visibleSections = useMemo(() => {
    if (activeCategory === "全部") {
      const mergedItems =
        categories.length > 0
          ? categories.flatMap((category) => newsData[category] || [])
          : Object.values(newsData).flat();

      return [
        {
          category: "全部",
          items: mergedItems,
        },
      ];
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
          title="行业新闻"
          description="阅读高价值资讯、趋势与事件摘要"
          // stats={
          //   <>
          //     <StatCard label="Workspace" value={currentWorkspace} />
          //     <StatCard label="Categories" value={categories.length} />
          //     <StatCard label="Articles" value={totalCount} />
          //   </>
          // }
          actions={
            <>
              <form
                className="flex flex-col gap-3 lg:flex-row"
                onSubmit={handleSearchSubmit}
              >
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
                    variant={
                      activeCategory === category ? "default" : "outline"
                    }
                    size="sm"
                    className={cn(
                      "rounded-full",
                      activeCategory === category &&
                        "bg-sky-600 hover:bg-sky-700",
                    )}
                    onClick={() => setActiveCategory(category)}
                  >
                    {category}
                  </Button>
                ))}
              </div>

              {activeQuery ? (
                <p className="mt-4 text-sm text-slate-500">
                  当前搜索词:{" "}
                  <span className="font-medium text-slate-800">
                    {activeQuery}
                  </span>
                </p>
              ) : null}
            </>
          }
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
              {activeCategory !== "全部" ? (
                <div className="flex items-center justify-between px-1">
                  <div>
                    <h3 className="text-xl font-semibold tracking-tight text-slate-950">
                      {category}
                    </h3>
                    <p className="mt-1 text-sm text-slate-500">
                      {items.length} 条资讯
                    </p>
                  </div>
                </div>
              ) : null}

              <div className="grid gap-4 xl:grid-cols-2">
                {items.map((item) => (
                  <div
                    key={item.id}
                    role="button"
                    tabIndex={0}
                    className="rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2"
                    onClick={() => setPreviewArticle(item)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setPreviewArticle(item);
                      }
                    }}
                  >
                    <ContentCard
                      topBar={
                        <>
                          <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                            {getSourceSiteName(item)}
                          </span>
                          <span className="text-xs font-medium text-slate-400">
                            {NEWS_DATE_FORMATTER.format(
                              new Date(item.crawled_at),
                            )}
                          </span>
                        </>
                      }
                      title={
                        <span className="group inline-flex items-start gap-2 text-left text-xl font-semibold leading-8 text-slate-950 transition-colors hover:text-sky-700">
                          <span className="text-balance">
                            {getHeadline(item)}
                          </span>
                        </span>
                      }
                      meta={
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(event) => event.stopPropagation()}
                          className="inline-flex items-center gap-1 text-sm leading-6 text-slate-500 underline decoration-slate-300 underline-offset-4 hover:text-slate-700"
                        >
                          原始链接: {item.url}
                          <ExternalLink
                            className="h-4 w-4"
                            aria-hidden="true"
                          />
                        </a>
                      }
                      content={
                        <ReactMarkdown>{getSummary(item)}</ReactMarkdown>
                      }
                    />
                  </div>
                ))}
              </div>
            </section>
          ))
        )}
      </div>

      {previewArticle ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6"
          onClick={() => setPreviewArticle(null)}
        >
          <section
            className="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <h3 className="truncate text-lg font-semibold text-slate-900">
                {getHeadline(previewArticle)}
              </h3>
              <button
                type="button"
                onClick={() => setPreviewArticle(null)}
                className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </header>
            <div className="overflow-y-auto px-5 py-4">
              <div className="max-w-none text-[15px] leading-9 text-slate-700 [&_h1]:mb-4 [&_h1]:mt-8 [&_h1]:text-2xl [&_h1]:font-bold [&_h1]:tracking-tight [&_h2]:mb-3 [&_h2]:mt-7 [&_h2]:text-xl [&_h2]:font-semibold [&_h3]:mb-3 [&_h3]:mt-6 [&_h3]:text-lg [&_h3]:font-semibold [&_p]:my-5 [&_p]:leading-9 [&_ul]:my-5 [&_ol]:my-5 [&_li]:my-2 [&_li]:leading-9 [&_blockquote]:my-6 [&_blockquote]:border-l-4 [&_blockquote]:border-slate-300 [&_blockquote]:pl-4 [&_code]:rounded [&_code]:bg-slate-100 [&_code]:px-1.5 [&_code]:py-0.5 [&_pre]:my-6 [&_pre]:overflow-x-auto [&_pre]:rounded-xl [&_pre]:bg-slate-900 [&_pre]:p-4 [&_pre]:text-slate-100 [&_table]:my-6 [&_table]:w-full [&_table]:border-separate [&_table]:border-spacing-0 [&_table]:border-2 [&_table]:border-slate-300 [&_table]:bg-white [&_th]:border [&_th]:border-slate-300 [&_th]:bg-slate-50 [&_th]:px-3 [&_th]:py-2 [&_th]:text-left [&_th]:font-semibold [&_td]:border [&_td]:border-slate-300 [&_td]:px-3 [&_td]:py-2">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {buildPreviewMarkdown(previewArticle)}
                </ReactMarkdown>
              </div>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}
