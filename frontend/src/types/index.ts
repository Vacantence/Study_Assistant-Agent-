export interface User {
  id: number;
  name: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface Conversation {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
  msg_count: number;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  filepath: string | null;
  created_at: string;
}

export interface ReviewCard {
  id: number;
  user_id: number;
  question: string;
  answer: string;
  topic: string;
  easiness: number;
  interval_days: number;
  repetitions: number;
  next_review: string;
  created_at: string;
  updated_at: string;
}

export interface GraphNode {
  name: string;
  description: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
}

export interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Document {
  id: number;
  user_id: number;
  filename: string;
  content_type: string;
  chunk_count: number;
  created_at: string;
}

export interface CacheEntry {
  id: number;
  query: string;
  quality_score: number;
  access_count: number;
  created_at: string;
}

export interface MemoryItem {
  key: string;
  value: string;
}

export interface Stats {
  review_due: number;
  graph_nodes: number;
}

export interface ExportResult {
  title: string;
  markdown: string;
}

export interface LLMProvider {
  id: number | null;
  user_id?: number;
  name: string;
  api_base: string;
  api_key: string;
  model: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}
