import axios from 'axios';
import type { SearchParams } from '../types';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  total?: number;
}

function extractWorkspace(filter?: string) {
  const matched = filter?.match(/(?:^|\sAND\s)workspace\s*=\s*"([^"]+)"/);
  return matched?.[1];
}

function clampLimit(limit: number | undefined, max: number) {
  if (limit == null) {
    return undefined;
  }

  return Math.min(limit, max);
}

// API 基础 URL (通过 Vite 代理访问)
const API_BASE_URL = '/api';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API 请求失败:', error);
    return Promise.reject(error);
  }
);

// 通用搜索接口
export async function hybridSearch<T>(
  indexName: string,
  params: SearchParams
) {
  const workspace = params.workspace ?? extractWorkspace(params.filter) ?? 'hpp';
  type SearchPayload = {
    hits: T[];
    estimatedTotalHits?: number;
    total?: number;
    limit: number;
    offset: number;
  };

  const response = await apiClient.get<ApiResponse<SearchPayload>>('/search', {
    params: {
      index: indexName,
      q: params.query || '',
      workspace,
      limit: clampLimit(params.limit, 100) ?? 20,
      offset: params.offset ?? 0,
      semantic_ratio: params.semanticRatio ?? 0.4,
      filter: params.filter,
    },
  });

  const payload = (((response as unknown as ApiResponse<SearchPayload>)?.data) ?? response) as SearchPayload;
  return {
    hits: payload?.hits ?? [],
    estimatedTotalHits: payload?.estimatedTotalHits ?? payload?.total ?? 0,
  } as { hits: T[]; estimatedTotalHits?: number };
}

// 获取竞争对手列表
export async function getCompetitors(workspace: string = 'hpp') {
  const response: any = await apiClient.get('/competitors', {
    params: { workspace, limit: 100 },
  });
  return response.data ?? response;
}

// 获取竞争对手详情
export async function getCompetitorProfile(competitorId: string, workspace: string = 'hpp') {
  const response: any = await apiClient.get(`/competitors/${competitorId}`, {
    params: { workspace },
  });
  return response.data ?? response;
}

// 获取竞争对手新闻
export async function getCompetitorNews(
  competitorId: string,
  workspace: string = 'hpp',
  limit: number = 50
) {
  const response: any = await apiClient.get(`/competitors/${competitorId}/news`, {
    params: { workspace, limit },
  });
  return response.data ?? response;
}

// 获取行业新闻
export async function getIndustryNews(
  workspace: string = 'hpp',
  category?: string,
  limit: number = 50
) {
  const response: any = await apiClient.get('/industry-news', {
    params: { workspace, category, limit },
  });
  return response.data ?? response;
}

// 获取新闻分类
export async function getNewsCategories(workspace: string = 'hpp') {
  const response: any = await apiClient.get('/industry-news/categories', {
    params: { workspace },
  });
  return response.data ?? response;
}

// 获取展会信息
export async function getTradeShows(workspace: string = 'hpp', year?: number) {
  const response: any = await apiClient.get('/trade-shows', {
    params: { workspace, year, limit: 100 },
  });
  return response.data ?? response;
}

// 按月份获取展会信息
export async function getTradeShowsByMonth(workspace: string = 'hpp') {
  const response: any = await apiClient.get('/trade-shows/by-month', {
    params: { workspace, limit: 200 },
  });
  return response.data ?? response;
}

// 获取工作空间列表
export async function getWorkspaces() {
  const response: any = await apiClient.get('/workspaces');
  return response.data ?? response;
}
