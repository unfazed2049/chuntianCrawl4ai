import { useState, useEffect } from 'react';
import { Tabs, List, Card, Spin, Empty, Input } from '@arco-design/web-react';
import { IconSearch } from '@arco-design/web-react/icon';
import { hybridSearch } from '../../api/meilisearch';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import type { IndustryNews } from '../../types';
import ReactMarkdown from 'react-markdown';
import './index.css';

const TabPane = Tabs.TabPane;

export default function IndustryNewsPage() {
  const { currentWorkspace } = useWorkspaceStore();
  const [categories, setCategories] = useState<string[]>([]);
  const [newsData, setNewsData] = useState<Record<string, IndustryNews[]>>({});
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadIndustryNews();
  }, [currentWorkspace]);

  const loadIndustryNews = async () => {
    setLoading(true);
    try {
      const result = await hybridSearch<IndustryNews>('industry_news', {
        query: '',
        filter: `workspace = "${currentWorkspace}"`,
        limit: 200,
      });

      // 按 category 分组
      const grouped: Record<string, IndustryNews[]> = {};
      const cats = new Set<string>();

      result.hits.forEach((item) => {
        const category = item.category || '未分类';
        cats.add(category);
        if (!grouped[category]) {
          grouped[category] = [];
        }
        grouped[category].push(item);
      });

      setCategories(Array.from(cats));
      setNewsData(grouped);
    } catch (error) {
      console.error('加载行业新闻失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadIndustryNews();
      return;
    }

    setLoading(true);
    try {
      const result = await hybridSearch<IndustryNews>('industry_news', {
        query: searchQuery,
        filter: `workspace = "${currentWorkspace}"`,
        limit: 200,
        semanticRatio: 0.4,
      });

      const grouped: Record<string, IndustryNews[]> = {};
      const cats = new Set<string>();

      result.hits.forEach((item) => {
        const category = item.category || '未分类';
        cats.add(category);
        if (!grouped[category]) {
          grouped[category] = [];
        }
        grouped[category].push(item);
      });

      setCategories(Array.from(cats));
      setNewsData(grouped);
    } catch (error) {
      console.error('搜索行业新闻失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="industry-news-page">
      <div className="search-bar">
        <Input.Search
          placeholder="搜索行业新闻..."
          value={searchQuery}
          onChange={setSearchQuery}
          onSearch={handleSearch}
          style={{ width: 400 }}
          searchButton
        />
      </div>

      <Spin loading={loading}>
        <Tabs defaultActiveTab={categories[0]}>
          {categories.map((category) => (
            <TabPane key={category} title={category}>
              <List
                dataSource={newsData[category] || []}
                render={(item) => (
                  <List.Item key={item.id}>
                    <Card hoverable>
                      <div className="news-title">
                        <a href={item.url} target="_blank" rel="noopener noreferrer">
                          {item.url}
                        </a>
                      </div>
                      <div className="news-meta">
                        时间: {new Date(item.crawled_at).toLocaleString()}
                      </div>
                      <ReactMarkdown className="news-content">
                        {item.cleaned_content.substring(0, 300)}...
                      </ReactMarkdown>
                    </Card>
                  </List.Item>
                )}
              />
            </TabPane>
          ))}
        </Tabs>
      </Spin>
    </div>
  );
}
