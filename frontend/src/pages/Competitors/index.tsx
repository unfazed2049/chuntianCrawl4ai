import { useState, useEffect } from 'react';
import { Layout, List, Tabs, Card, Spin, Empty } from '@arco-design/web-react';
import { hybridSearch } from '../../api/meilisearch';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import type { CompetitorProfile, CompetitorNews } from '../../types';
import ReactMarkdown from 'react-markdown';
import './index.css';

const { Content } = Layout;
const TabPane = Tabs.TabPane;

export default function Competitors() {
  const { currentWorkspace } = useWorkspaceStore();
  const [competitors, setCompetitors] = useState<CompetitorProfile[]>([]);
  const [selectedCompetitor, setSelectedCompetitor] = useState<string | null>(null);
  const [newsData, setNewsData] = useState<CompetitorNews[]>([]);
  const [profileData, setProfileData] = useState<CompetitorProfile | null>(null);
  const [loading, setLoading] = useState(false);

  // 加载竞争对手列表
  useEffect(() => {
    loadCompetitors();
  }, [currentWorkspace]);

  // 加载选中竞争对手的数据
  useEffect(() => {
    if (selectedCompetitor) {
      loadCompetitorData(selectedCompetitor);
    }
  }, [selectedCompetitor, currentWorkspace]);

  const loadCompetitors = async () => {
    setLoading(true);
    try {
      const result = await hybridSearch<CompetitorProfile>('competitor_profiles', {
        query: '',
        filter: `workspace = "${currentWorkspace}"`,
        limit: 100,
      });
      setCompetitors(result.hits);
      if (result.hits.length > 0 && !selectedCompetitor) {
        setSelectedCompetitor(result.hits[0].competitor_id);
      }
    } catch (error) {
      console.error('加载竞争对手列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCompetitorData = async (competitorId: string) => {
    setLoading(true);
    try {
      // 加载竞争对手新闻
      const newsResult = await hybridSearch<CompetitorNews>('competitor_news', {
        query: '',
        filter: `workspace = "${currentWorkspace}" AND competitor_id = "${competitorId}"`,
        limit: 50,
      });
      setNewsData(newsResult.hits);

      // 加载竞争对手档案
      const profileResult = await hybridSearch<CompetitorProfile>('competitor_profiles', {
        query: '',
        filter: `workspace = "${currentWorkspace}" AND competitor_id = "${competitorId}"`,
        limit: 1,
      });
      setProfileData(profileResult.hits[0] || null);
    } catch (error) {
      console.error('加载竞争对手数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="competitors-page">
      <div className="competitors-list">
        <div className="list-header">竞争对手列表</div>
        <Spin loading={loading}>
          <List
            dataSource={competitors}
            render={(item) => (
              <List.Item
                key={item.competitor_id}
                className={selectedCompetitor === item.competitor_id ? 'active' : ''}
                onClick={() => setSelectedCompetitor(item.competitor_id)}
              >
                <div className="competitor-item">
                  <div className="competitor-name">{item.name}</div>
                  <div className="competitor-country">{item.country}</div>
                </div>
              </List.Item>
            )}
          />
        </Spin>
      </div>

      <div className="competitors-content">
        {selectedCompetitor && profileData ? (
          <Tabs defaultActiveTab="news">
            <TabPane key="news" title="新闻">
              <List
                dataSource={newsData}
                render={(item) => (
                  <List.Item key={item.id}>
                    <Card hoverable>
                      <div className="news-title">{item.url}</div>
                      <div className="news-meta">
                        来源: {item.source_section} | 时间: {new Date(item.crawled_at).toLocaleString()}
                      </div>
                      <ReactMarkdown className="news-content">
                        {item.cleaned_content.substring(0, 200)}...
                      </ReactMarkdown>
                    </Card>
                  </List.Item>
                )}
              />
            </TabPane>

            <TabPane key="products" title="产品">
              {profileData.products?.length > 0 ? (
                <List
                  dataSource={profileData.products}
                  render={(item, index) => (
                    <List.Item key={index}>
                      <Card>
                        <pre>{JSON.stringify(item, null, 2)}</pre>
                      </Card>
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="暂无产品数据" />
              )}
            </TabPane>

            <TabPane key="cases" title="案例">
              {profileData.cases?.length > 0 ? (
                <List
                  dataSource={profileData.cases}
                  render={(item, index) => (
                    <List.Item key={index}>
                      <Card>
                        <pre>{JSON.stringify(item, null, 2)}</pre>
                      </Card>
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="暂无案例数据" />
              )}
            </TabPane>

            <TabPane key="solutions" title="解决方案">
              {profileData.solutions?.length > 0 ? (
                <List
                  dataSource={profileData.solutions}
                  render={(item, index) => (
                    <List.Item key={index}>
                      <Card>
                        <pre>{JSON.stringify(item, null, 2)}</pre>
                      </Card>
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="暂无解决方案数据" />
              )}
            </TabPane>

            <TabPane key="technologies" title="技术栈">
              {profileData.technologies?.length > 0 ? (
                <List
                  dataSource={profileData.technologies}
                  render={(item, index) => (
                    <List.Item key={index}>
                      <Card>
                        <pre>{JSON.stringify(item, null, 2)}</pre>
                      </Card>
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="暂无技术栈数据" />
              )}
            </TabPane>
          </Tabs>
        ) : (
          <Empty description="请选择一个竞争对手" />
        )}
      </div>
    </div>
  );
}
