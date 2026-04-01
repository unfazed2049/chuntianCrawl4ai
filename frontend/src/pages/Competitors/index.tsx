import { useEffect, useMemo, useState } from 'react';
import { Building2, ExternalLink, Layers3, Newspaper, Radar, Wrench } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { hybridSearch } from '../../api/meilisearch';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent } from '../../components/ui/card';
import { ContentCard } from '../../components/ui/content-card';
import { EmptyState } from '../../components/ui/empty-state';
import { PageHeader } from '../../components/ui/page-header';
import { Skeleton } from '../../components/ui/skeleton';
import { StatCard } from '../../components/ui/stat-card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { cn } from '../../lib/utils';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import type { CompetitorNews, CompetitorProfile } from '../../types';

const tabs = [
  { key: 'news', label: '新闻', icon: Newspaper },
  { key: 'products', label: '产品', icon: Layers3 },
  { key: 'cases', label: '案例', icon: Building2 },
  { key: 'solutions', label: '解决方案', icon: Radar },
  { key: 'technologies', label: '技术栈', icon: Wrench },
] as const;

type TabKey = (typeof tabs)[number]['key'];

const DATE_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  dateStyle: 'medium',
  timeStyle: 'short',
});

function renderStructuredItem(item: unknown) {
  return JSON.stringify(item, null, 2);
}

function getHostname(url?: string) {
  if (!url) {
    return '未提供站点';
  }

  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
}

function NewsSkeleton() {
  return (
    <div className="rounded-3xl border border-slate-200/70 bg-white/70 p-5">
      <Skeleton className="h-4 w-24 rounded-full" />
      <Skeleton className="mt-4 h-6 w-2/3 rounded-xl" />
      <Skeleton className="mt-3 h-4 w-1/2 rounded-lg bg-slate-100" />
      <div className="mt-4 space-y-2">
        <Skeleton className="h-4 w-full rounded-lg bg-slate-100" />
        <Skeleton className="h-4 w-full rounded-lg bg-slate-100" />
        <Skeleton className="h-4 w-4/5 rounded-lg bg-slate-100" />
      </div>
    </div>
  );
}

export default function Competitors() {
  const { currentWorkspace } = useWorkspaceStore();
  const [competitors, setCompetitors] = useState<CompetitorProfile[]>([]);
  const [selectedCompetitor, setSelectedCompetitor] = useState<string | null>(null);
  const [newsData, setNewsData] = useState<CompetitorNews[]>([]);
  const [profileData, setProfileData] = useState<CompetitorProfile | null>(null);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [activeTab, setActiveTab] = useState<TabKey>('news');

  useEffect(() => {
    void loadCompetitors();
  }, [currentWorkspace]);

  useEffect(() => {
    if (!selectedCompetitor) {
      return;
    }

    void loadCompetitorData(selectedCompetitor);
  }, [selectedCompetitor, currentWorkspace]);

  async function loadCompetitors() {
    setLoadingList(true);

    try {
      const result = await hybridSearch<CompetitorProfile>('competitor_profiles', {
        query: '',
        filter: `workspace = "${currentWorkspace}"`,
        limit: 100,
      });

      setCompetitors(result.hits);
      setSelectedCompetitor((previous) => {
        if (previous && result.hits.some((item) => item.competitor_id === previous)) {
          return previous;
        }

        return result.hits[0]?.competitor_id ?? null;
      });
    } catch (error) {
      console.error('加载竞争对手列表失败:', error);
      setCompetitors([]);
      setSelectedCompetitor(null);
    } finally {
      setLoadingList(false);
    }
  }

  async function loadCompetitorData(competitorId: string) {
    setLoadingDetail(true);

    try {
      const newsPromise = hybridSearch<CompetitorNews>('competitor_news', {
        query: '',
        filter: `workspace = "${currentWorkspace}" AND competitor_id = "${competitorId}"`,
        limit: 50,
      });
      const profilePromise = hybridSearch<CompetitorProfile>('competitor_profiles', {
        query: '',
        filter: `workspace = "${currentWorkspace}" AND competitor_id = "${competitorId}"`,
        limit: 1,
      });

      const [newsResult, profileResult] = await Promise.all([newsPromise, profilePromise]);
      setNewsData(newsResult.hits);
      setProfileData(profileResult.hits[0] || null);
    } catch (error) {
      console.error('加载竞争对手数据失败:', error);
      setNewsData([]);
      setProfileData(null);
    } finally {
      setLoadingDetail(false);
    }
  }

  const selectedCompetitorProfile = useMemo(
    () => competitors.find((item) => item.competitor_id === selectedCompetitor) ?? null,
    [competitors, selectedCompetitor]
  );

  const structuredSections = useMemo(
    () => ({
      products: profileData?.products ?? [],
      cases: profileData?.cases ?? [],
      solutions: profileData?.solutions ?? [],
      technologies: profileData?.technologies ?? [],
    }),
    [profileData]
  );
  return (
    <div className="px-4 py-6 lg:px-8 lg:py-8">
      <div className="mx-auto grid max-w-7xl gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <Card className="overflow-hidden xl:sticky xl:top-[125px] xl:h-[calc(100vh-157px)]">
          <CardContent className="flex h-full flex-col p-0">
            <div className="border-b border-slate-100 px-6 py-5">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-sky-600">Competitors</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">竞争对手雷达</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                选择一个竞争对手，查看公司画像、资讯动态与结构化资料。
              </p>
            </div>

            <div className="border-b border-slate-100 px-6 py-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-xs uppercase tracking-[0.16em] text-slate-400">Workspace</div>
                  <div className="mt-2 text-sm font-semibold text-slate-900">{currentWorkspace}</div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-xs uppercase tracking-[0.16em] text-slate-400">Companies</div>
                  <div className="mt-2 text-sm font-semibold text-slate-900">{competitors.length}</div>
                </div>
              </div>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3" style={{ contentVisibility: 'auto' }}>
              {loadingList ? (
                <div className="space-y-3 px-3 py-2">
                  {Array.from({ length: 6 }).map((_, index) => (
                    <div key={index} className="rounded-2xl border border-slate-200/70 bg-white p-4">
                      <div className="h-4 w-24 animate-pulse rounded-full bg-slate-200" />
                      <div className="mt-3 h-4 w-16 animate-pulse rounded-full bg-slate-100" />
                    </div>
                  ))}
                </div>
              ) : competitors.length === 0 ? (
                <div className="px-4 py-12 text-center">
                  <p className="text-lg font-semibold text-slate-900">暂无竞争对手数据</p>
                  <p className="mt-2 text-sm text-slate-500">当前工作空间还没有可展示的竞争对手档案。</p>
                </div>
              ) : (
                competitors.map((item) => {
                  const isActive = selectedCompetitor === item.competitor_id;

                  return (
                    <button
                      key={item.competitor_id}
                      type="button"
                      onClick={() => setSelectedCompetitor(item.competitor_id)}
                      className={cn(
                        'mb-2 flex w-full flex-col rounded-2xl border px-4 py-4 text-left transition-[background-color,border-color,transform,box-shadow] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2',
                        isActive
                          ? 'border-sky-200 bg-sky-50 shadow-sm shadow-sky-100'
                          : 'border-transparent bg-white hover:-translate-y-0.5 hover:border-slate-200 hover:bg-slate-50'
                      )}
                    >
                      <span className="text-sm font-semibold text-slate-950">{item.name}</span>
                      <span className="mt-1 text-xs text-slate-500">{item.country || '地区未知'}</span>
                      <span className="mt-3 inline-flex w-fit rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-600">
                        {getHostname(item.website)}
                      </span>
                    </button>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <PageHeader
            eyebrow={selectedCompetitorProfile?.country || 'Global'}
            title={selectedCompetitorProfile?.name || '选择一个竞争对手'}
            description="当前视图聚焦于单家公司，左侧切换对象，右侧查看新闻、产品、案例与技术栈等结构化信息。"
            stats={(
              <>
                <StatCard label="News" value={newsData.length} />
                <StatCard label="Products" value={structuredSections.products.length} />
                <StatCard label="Technologies" value={structuredSections.technologies.length} />
              </>
            )}
            actions={(
              <div className="flex flex-wrap items-center gap-3">
                {profileData?.website ? <Badge className="bg-slate-100 text-slate-700">{getHostname(profileData.website)}</Badge> : null}
                {profileData?.website ? (
                  <Button asChild variant="outline">
                    <a href={profileData.website} target="_blank" rel="noopener noreferrer">
                      访问官网
                      <ExternalLink className="h-4 w-4" aria-hidden="true" />
                    </a>
                  </Button>
                ) : null}
              </div>
            )}
          />

          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as TabKey)}>
            <TabsList>
              {tabs.map((tab) => {
                const Icon = tab.icon;

                return (
                  <TabsTrigger key={tab.key} value={tab.key}>
                    <Icon className="h-4 w-4" aria-hidden="true" />
                    {tab.label}
                  </TabsTrigger>
                );
              })}
            </TabsList>

            {loadingDetail ? (
              <section className="grid gap-4 lg:grid-cols-2">
                <NewsSkeleton />
                <NewsSkeleton />
                <NewsSkeleton />
                <NewsSkeleton />
              </section>
            ) : !selectedCompetitor || !profileData ? (
              <EmptyState
                icon={<Building2 className="h-5 w-5" aria-hidden="true" />}
                title="请选择一个竞争对手"
                description="从左侧列表选择目标公司后，这里会显示新闻动态和结构化资料。"
                className="min-h-72"
              />
            ) : (
              <>
                <TabsContent value="news">
                  {newsData.length > 0 ? (
                    <section className="grid gap-4 xl:grid-cols-2">
                      {newsData.map((item) => (
                        <ContentCard
                          key={item.id}
                          topBar={(
                            <>
                              <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                {item.source_section || '资讯来源'}
                              </span>
                              <span className="text-xs font-medium text-slate-400">
                                {DATE_FORMATTER.format(new Date(item.crawled_at))}
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
                              <span className="text-balance">{getHostname(item.url)}</span>
                              <ExternalLink className="mt-1 h-4 w-4 shrink-0 text-slate-400 transition-colors group-hover:text-sky-600" aria-hidden="true" />
                            </a>
                          )}
                          meta={<p className="text-sm leading-6 text-slate-500">原始链接: {item.url}</p>}
                          content={<ReactMarkdown>{item.cleaned_content.slice(0, 280)}</ReactMarkdown>}
                        />
                      ))}
                    </section>
                  ) : (
                    <EmptyState
                      title="暂无相关新闻"
                      description="当前竞争对手还没有抓取到新闻动态，可以稍后刷新数据再查看。"
                    />
                  )}
                </TabsContent>

                {(['products', 'cases', 'solutions', 'technologies'] as const).map((tabKey) => (
                  <TabsContent key={tabKey} value={tabKey}>
                    <Card>
                      <CardContent className="p-6 lg:p-8">
                        <div className="mb-5 flex items-center justify-between gap-4">
                          <div>
                            <h3 className="text-xl font-semibold tracking-tight text-slate-950">
                              {tabs.find((item) => item.key === tabKey)?.label}
                            </h3>
                            <p className="mt-1 text-sm text-slate-500">用结构化块展示该公司的补充资料。</p>
                          </div>
                          <Badge>{structuredSections[tabKey].length} 条记录</Badge>
                        </div>

                        {structuredSections[tabKey].length > 0 ? (
                          <div className="grid gap-4">
                            {structuredSections[tabKey].map((item, index) => (
                              <div key={`${tabKey}-${index}`} className="overflow-hidden rounded-3xl border border-slate-200 bg-slate-50">
                                <div className="border-b border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700">
                                  {tabs.find((entry) => entry.key === tabKey)?.label} #{index + 1}
                                </div>
                                <pre className="overflow-x-auto p-5 text-xs leading-6 text-slate-700">{renderStructuredItem(item)}</pre>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center">
                            <p className="text-lg font-semibold text-slate-900">
                              暂无{tabs.find((item) => item.key === tabKey)?.label}数据
                            </p>
                            <p className="mt-2 text-sm leading-6 text-slate-500">
                              当前档案中还没有这一类结构化字段，后续可以继续补抓或优化抽取规则。
                            </p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </TabsContent>
                ))}
              </>
            )}
          </Tabs>
        </div>
      </div>
    </div>
  );
}
