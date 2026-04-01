import { useEffect, useMemo, useState } from 'react';
import { CalendarRange, Clock3, ExternalLink, Sparkles } from 'lucide-react';
import dayjs from 'dayjs';
import ReactMarkdown from 'react-markdown';
import { hybridSearch } from '../../api/meilisearch';
import { Badge } from '../../components/ui/badge';
import { ContentCard } from '../../components/ui/content-card';
import { EmptyState } from '../../components/ui/empty-state';
import { PageHeader } from '../../components/ui/page-header';
import { Skeleton } from '../../components/ui/skeleton';
import { StatCard } from '../../components/ui/stat-card';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import type { TradeShow } from '../../types';

const DATE_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  dateStyle: 'medium',
  timeStyle: 'short',
});

function getShowSummary(show: TradeShow) {
  const text = show.cleaned_content?.trim() || show.raw_content?.trim() || '暂无摘要。';
  return text.length > 260 ? `${text.slice(0, 260)}…` : text;
}

function getShowLink(show: TradeShow) {
  const candidate = [show.url, show.website, show.link].find(
    (value) => typeof value === 'string' && value.trim().length > 0
  );

  return candidate ?? null;
}

function getShowLocation(show: TradeShow) {
  const candidate = [show.location, show.city, show.country, show.venue].find(
    (value) => typeof value === 'string' && value.trim().length > 0
  );

  return candidate ?? '地点待补充';
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
  const [groupedShows, setGroupedShows] = useState<Record<string, TradeShow[]>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void loadTradeShows();
  }, [currentWorkspace]);

  async function loadTradeShows() {
    setLoading(true);

    try {
      const result = await hybridSearch<TradeShow>('trade_shows', {
        query: '',
        filter: `workspace = "${currentWorkspace}"`,
        limit: 200,
      });

      const sorted = result.hits.toSorted(
        (a, b) => new Date(b.crawled_at).getTime() - new Date(a.crawled_at).getTime()
      );

      const grouped = sorted.reduce<Record<string, TradeShow[]>>((accumulator, show) => {
        const monthKey = dayjs(show.crawled_at).format('YYYY-MM');

        if (!accumulator[monthKey]) {
          accumulator[monthKey] = [];
        }

        accumulator[monthKey].push(show);
        return accumulator;
      }, {});

      setGroupedShows(grouped);
    } catch (error) {
      console.error('加载展会信息失败:', error);
      setGroupedShows({});
    } finally {
      setLoading(false);
    }
  }

  const monthKeys = useMemo(
    () => Object.keys(groupedShows).toSorted((a, b) => b.localeCompare(a)),
    [groupedShows]
  );

  const totalShows = useMemo(
    () => Object.values(groupedShows).reduce((sum, shows) => sum + shows.length, 0),
    [groupedShows]
  );

  return (
    <div className="px-4 py-6 lg:px-8 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <PageHeader
          eyebrow="Trade Shows"
          title="用时间线方式整理会展曝光与行业节点"
          description="按月聚合展会信息，保留摘要、时间和扩展链接，让会展动态从“数据列表”变成更易浏览的市场事件流。"
          stats={(
            <>
              <StatCard label="Workspace" value={currentWorkspace} />
              <StatCard label="Months" value={monthKeys.length} />
              <StatCard label="Shows" value={totalShows} />
            </>
          )}
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
                    {dayjs(monthKey).format('YYYY 年 MM 月')}
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">{groupedShows[monthKey].length} 个展会节点</p>
                </div>
                <Badge>{monthKey}</Badge>
              </div>

              <div className="grid gap-4">
                {groupedShows[monthKey].map((show) => {
                  const showLink = getShowLink(show);

                  return (
                    <ContentCard
                      key={show.id}
                      topBar={(
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge className="bg-amber-50 text-amber-700">{show.year}</Badge>
                          <Badge className="bg-slate-100 text-slate-700">{getShowLocation(show)}</Badge>
                        </div>
                      )}
                      action={showLink ? (
                        <a
                          href={showLink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-[border-color,background-color,color] hover:border-slate-300 hover:bg-slate-50 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2"
                        >
                          查看链接
                          <ExternalLink className="h-4 w-4" aria-hidden="true" />
                        </a>
                      ) : null}
                      title={<h4 className="text-balance text-2xl font-semibold tracking-tight text-slate-950">{show.name}</h4>}
                      meta={(
                        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
                          <span className="inline-flex items-center gap-2">
                            <Clock3 className="h-4 w-4" aria-hidden="true" />
                            {DATE_FORMATTER.format(new Date(show.crawled_at))}
                          </span>
                          {show.month ? (
                            <span className="inline-flex items-center gap-2">
                              <Sparkles className="h-4 w-4" aria-hidden="true" />
                              {show.month} 月事件
                            </span>
                          ) : null}
                        </div>
                      )}
                      content={<ReactMarkdown>{getShowSummary(show)}</ReactMarkdown>}
                    />
                  );
                })}
              </div>
            </section>
          ))
        )}
      </div>
    </div>
  );
}
