// Meilisearch 数据类型定义

export interface CompetitorNews {
  id: string;
  workspace: string;
  competitor_id: string;
  competitor_name: string;
  url: string;
  crawled_at: string;
  source_section: string;
  cleaned_content: string;
  raw_content: string;
  [key: string]: any; // LLM 提取的动态字段
}

export interface IndustryNews {
  id: string;
  workspace: string;
  url: string;
  crawled_at: string;
  cleaned_content: string;
  raw_content: string;
  category?: string;
  [key: string]: any; // LLM 提取的动态字段
}

export interface TradeShow {
  id: string;
  workspace: string;
  crawled_at: string;
  cleaned_content: string;
  raw_content: string;
  name: string;
  year: number;
  month?: number;
  [key: string]: any; // LLM 提取的动态字段
}

export interface CompetitorProfile {
  id: string;
  workspace: string;
  competitor_id: string;
  name: string;
  website: string;
  country: string;
  updated_at: string;
  products: any[];
  cases: any[];
  solutions: any[];
  technologies: any[];
}

export interface SearchParams {
  query?: string;
  semanticRatio?: number;
  limit?: number;
  offset?: number;
  filter?: string;
  workspace?: string;
}
