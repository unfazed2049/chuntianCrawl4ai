import { useState, useEffect } from 'react';
import { Card, List, Spin, Empty, Tag } from '@arco-design/web-react';
import { hybridSearch } from '../../api/meilisearch';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import type { TradeShow } from '../../types';
import ReactMarkdown from 'react-markdown';
import dayjs from 'dayjs';
import './index.css';

export default function TradeShowsPage() {
  const { currentWorkspace } = useWorkspaceStore();
  const [tradeShows, setTradeShows] = useState<TradeShow[]>([]);
  const [groupedShows, setGroupedShows] = useState<Record<string, TradeShow[]>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTradeShows();
  }, [currentWorkspace]);

  const loadTradeShows = async () => {
    setLoading(true);
    try {
      const result = await hybridSearch<TradeShow>('trade_shows', {
        query: '',
        filter: `workspace = "${currentWorkspace}"`,
        limit: 200,
      });

      // 按爬取时间排序(最新的在前面)
      const sorted = result.hits.sort((a, b) => 
        new Date(b.crawled_at).getTime() - new Date(a.crawled_at).getTime()
      );

      // 按月份分组
      const grouped: Record<string, TradeShow[]> = {};
      sorted.forEach((show) => {
        const monthKey = dayjs(show.crawled_at).format('YYYY-MM');
        if (!grouped[monthKey]) {
          grouped[monthKey] = [];
        }
        grouped[monthKey].push(show);
      });

      setTradeShows(sorted);
      setGroupedShows(grouped);
    } catch (error) {
      console.error('加载展会信息失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const monthKeys = Object.keys(groupedShows).sort((a, b) => b.localeCompare(a));

  return (
    <div className="trade-shows-page">
      <Spin loading={loading}>
        {monthKeys.length > 0 ? (
          monthKeys.map((monthKey) => (
            <div key={monthKey} className="month-section">
              <div className="month-header">
                {dayjs(monthKey).format('YYYY年 MM月')}
                <Tag color="arcoblue" style={{ marginLeft: 12 }}>
                  {groupedShows[monthKey].length} 个展会
                </Tag>
              </div>
              <List
                dataSource={groupedShows[monthKey]}
                render={(item) => (
                  <List.Item key={item.id}>
                    <Card hoverable className="trade-show-card">
                      <div className="show-header">
                        <div className="show-name">{item.name}</div>
                        <Tag color="orange">{item.year}</Tag>
                      </div>
                      <div className="show-meta">
                        爬取时间: {dayjs(item.crawled_at).format('YYYY-MM-DD HH:mm:ss')}
                      </div>
                      <ReactMarkdown className="show-content">
                        {item.cleaned_content.substring(0, 200)}...
                      </ReactMarkdown>
                    </Card>
                  </List.Item>
                )}
              />
            </div>
          ))
        ) : (
          <Empty description="暂无展会信息" />
        )}
      </Spin>
    </div>
  );
}
