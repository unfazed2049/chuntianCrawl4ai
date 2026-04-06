import { useEffect, useMemo, useState } from "react";
import {
  CalendarRange,
  Clock3,
  ExternalLink,
  Sparkles,
  X,
} from "lucide-react";
import dayjs from "dayjs";
import ReactMarkdown from "react-markdown";
import { hybridSearch } from "../../api/meilisearch";
import { Badge } from "../../components/ui/badge";
import { ContentCard } from "../../components/ui/content-card";
import { EmptyState } from "../../components/ui/empty-state";
import { PageHeader } from "../../components/ui/page-header";
import { Skeleton } from "../../components/ui/skeleton";
import { useWorkspaceStore } from "../../stores/workspaceStore";
import type { TradeShow } from "../../types";

const DATE_FORMATTER = new Intl.DateTimeFormat("zh-CN", {
  dateStyle: "medium",
  timeStyle: "short",
});

function getShowSummary(show: TradeShow) {
  const text =
    show.cleaned_content?.trim() || show.raw_content?.trim() || "暂无摘要。";
  return text.length > 260 ? `${text.slice(0, 260)}…` : text;
}

function buildPreviewMarkdown(show: TradeShow) {
  const raw = show.raw_content?.trim();
  const cleaned = show.cleaned_content?.trim();
  const base = raw || cleaned || "暂无内容。";

  if (base.includes("\\n") && !base.includes("\n")) {
    return base.replaceAll("\\n", "\n");
  }

  return base;
}

function getShowLink(show: TradeShow) {
  const candidate = [show.url, show.website, show.link].find(
    (value) => typeof value === "string" && value.trim().length > 0,
  );

  return candidate ?? null;
}

function getShowLocation(show: TradeShow) {
  const candidate = [show.location, show.city, show.country, show.venue].find(
    (value) => typeof value === "string" && value.trim().length > 0,
  );

  return candidate ?? "地点待补充";
}

function MonthSkeleton() {
  return (
    <div className="rounded-3xl border border-slate-200/70 bg-white/80 p-6">
      <Skeleton className="h-5 w-40 rounded-full" />
      <div className="mt-5 space-y-4">
        <div className="rounded-2xl border border-slate-100 p-5">
          <Skeleton className="h-4 w-32 rounded-full" />
          <Skeleton className="mt-4 h-6 w-2/3 rounded-xl" />
          <Skeleton className="mt-4 h-4 w-full rounded-lg bg-slate-100" />
          <Skeleton className="mt-2 h-4 w-4/5 rounded-lg bg-slate-100" />
        </div>
      </div>
    </div>
  );
}

export default function TradeShowsPage() {
  const { currentWorkspace } = useWorkspaceStore();
  const [groupedShows, setGroupedShows] = useState<Record<string, TradeShow[]>>(
    {},
  );
  const [loading, setLoading] = useState(false);
  const [previewShow, setPreviewShow] = useState<TradeShow | null>(null);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setPreviewShow(null);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    void loadTradeShows();
  }, [currentWorkspace]);

  async function loadTradeShows() {
    setLoading(true);

    try {
      const result = await hybridSearch<TradeShow>("trade_shows", {
        query: "",
        workspace: currentWorkspace,
        limit: 100,
      });

      const sorted = result.hits.toSorted(
        (a, b) =>
          new Date(b.crawled_at).getTime() - new Date(a.crawled_at).getTime(),
      );

      const grouped = sorted.reduce<Record<string, TradeShow[]>>(
        (accumulator, show) => {
          const monthKey = dayjs(show.crawled_at).format("YYYY-MM");

          if (!accumulator[monthKey]) {
            accumulator[monthKey] = [];
          }

          accumulator[monthKey].push(show);
          return accumulator;
        },
        {},
      );

      setGroupedShows(grouped);
    } catch (error) {
      console.error("加载展会信息失败:", error);
      setGroupedShows({});
    } finally {
      setLoading(false);
    }
  }

  const monthKeys = useMemo(
    () => Object.keys(groupedShows).toSorted((a, b) => b.localeCompare(a)),
    [groupedShows],
  );
  const previewShowLink = previewShow ? getShowLink(previewShow) : null;

  return (
    <div className="px-4 py-6 lg:px-8 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <PageHeader
          eyebrow="Trade Shows"
          title="展会信息"
          description="按时间整理会展节点与市场曝光"
        />

        {loading ? (
          <section className="grid gap-4">
            <MonthSkeleton />
            <MonthSkeleton />
          </section>
        ) : monthKeys.length === 0 ? (
          <EmptyState
            icon={<CalendarRange className="h-5 w-5" aria-hidden="true" />}
            title="暂无展会信息"
            description="当前工作空间还没有抓取到展会动态，后续同步后会在这里按月份呈现。"
          />
        ) : (
          monthKeys.map((monthKey) => (
            <section key={monthKey} className="space-y-4">
              <div className="flex items-center justify-between px-1">
                <div>
                  <h3 className="text-2xl font-semibold tracking-tight text-slate-950">
                    {dayjs(monthKey).format("YYYY 年 MM 月")}
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    {groupedShows[monthKey].length} 个展会节点
                  </p>
                </div>
                <Badge>{monthKey}</Badge>
              </div>

              <div className="grid gap-4">
                {groupedShows[monthKey].map((show) => {
                  const showLink = getShowLink(show);

                  return (
                    <div
                      key={show.id}
                      role="button"
                      tabIndex={0}
                      className="rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2"
                      onClick={() => setPreviewShow(show)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          setPreviewShow(show);
                        }
                      }}
                    >
                      <ContentCard
                        topBar={
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge className="bg-amber-50 text-amber-700">
                              {show.year}
                            </Badge>
                            <Badge className="bg-slate-100 text-slate-700">
                              {getShowLocation(show)}
                            </Badge>
                          </div>
                        }
                        action={
                          showLink ? (
                            <a
                              href={showLink}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(event) => event.stopPropagation()}
                              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-[border-color,background-color,color] hover:border-slate-300 hover:bg-slate-50 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2"
                            >
                              查看链接
                              <ExternalLink
                                className="h-4 w-4"
                                aria-hidden="true"
                              />
                            </a>
                          ) : null
                        }
                        title={
                          <h4 className="text-balance text-2xl font-semibold tracking-tight text-slate-950">
                            {show.name}
                          </h4>
                        }
                        meta={
                          <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
                            <span className="inline-flex items-center gap-2">
                              <Clock3 className="h-4 w-4" aria-hidden="true" />
                              {DATE_FORMATTER.format(new Date(show.crawled_at))}
                            </span>
                            {show.month ? (
                              <span className="inline-flex items-center gap-2">
                                <Sparkles
                                  className="h-4 w-4"
                                  aria-hidden="true"
                                />
                                {show.month} 月事件
                              </span>
                            ) : null}
                          </div>
                        }
                        content={
                          <ReactMarkdown>{getShowSummary(show)}</ReactMarkdown>
                        }
                      />
                    </div>
                  );
                })}
              </div>
            </section>
          ))
        )}
      </div>

      {previewShow ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6"
          onClick={() => setPreviewShow(null)}
        >
          <section
            className="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <h3 className="truncate text-lg font-semibold text-slate-900">
                {previewShow.name}
              </h3>
              <button
                type="button"
                onClick={() => setPreviewShow(null)}
                className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </header>
            <div className="overflow-y-auto px-5 py-4">
              <div className="mb-4 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                <Badge className="bg-amber-50 text-amber-700">{previewShow.year}</Badge>
                <Badge className="bg-slate-100 text-slate-700">
                  {getShowLocation(previewShow)}
                </Badge>
                <span className="inline-flex items-center gap-2">
                  <Clock3 className="h-4 w-4" aria-hidden="true" />
                  {DATE_FORMATTER.format(new Date(previewShow.crawled_at))}
                </span>
                {previewShow.month ? (
                  <span className="inline-flex items-center gap-2">
                    <Sparkles className="h-4 w-4" aria-hidden="true" />
                    {previewShow.month} 月事件
                  </span>
                ) : null}
                {previewShowLink ? (
                  <a
                    href={previewShowLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm leading-6 text-slate-500 underline decoration-slate-300 underline-offset-4 hover:text-slate-700"
                  >
                    原始链接
                    <ExternalLink className="h-4 w-4" aria-hidden="true" />
                  </a>
                ) : null}
              </div>
              <div className="max-w-none text-[15px] leading-9 text-slate-700 [&_h1]:mb-4 [&_h1]:mt-8 [&_h1]:text-2xl [&_h1]:font-bold [&_h1]:tracking-tight [&_h2]:mb-3 [&_h2]:mt-7 [&_h2]:text-xl [&_h2]:font-semibold [&_h3]:mb-3 [&_h3]:mt-6 [&_h3]:text-lg [&_h3]:font-semibold [&_p]:my-5 [&_p]:leading-9 [&_ul]:my-5 [&_ol]:my-5 [&_li]:my-2 [&_li]:leading-9 [&_blockquote]:my-6 [&_blockquote]:border-l-4 [&_blockquote]:border-slate-300 [&_blockquote]:pl-4 [&_code]:rounded [&_code]:bg-slate-100 [&_code]:px-1.5 [&_code]:py-0.5 [&_pre]:my-6 [&_pre]:overflow-x-auto [&_pre]:rounded-xl [&_pre]:bg-slate-900 [&_pre]:p-4 [&_pre]:text-slate-100 [&_table]:my-6 [&_table]:w-full [&_table]:border-separate [&_table]:border-spacing-0 [&_table]:border-2 [&_table]:border-slate-300 [&_table]:bg-white [&_th]:border [&_th]:border-slate-300 [&_th]:bg-slate-50 [&_th]:px-3 [&_th]:py-2 [&_th]:text-left [&_th]:font-semibold [&_td]:border [&_td]:border-slate-300 [&_td]:px-3 [&_td]:py-2">
                <ReactMarkdown>{buildPreviewMarkdown(previewShow)}</ReactMarkdown>
              </div>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}
