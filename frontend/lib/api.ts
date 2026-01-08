import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface GraphNode {
  id: string;
  labels: string[];
  properties: Record<string, unknown>;
}

export interface GraphRelationship {
  id: string;
  type: string;
  startNodeId: string;
  endNodeId: string;
  properties: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  relationships: GraphRelationship[];
}

export interface Decision {
  id: string;
  decision_type: string;
  reasoning: string;
  outcome: string;
  confidence: number;
  risk_factors: string[];
  timestamp: string;
  made_by: string;
  status: string;
}

export interface Customer {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  risk_score: number;
  customer_since: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  tool_calls?: Array<{
    name: string;
    arguments: Record<string, unknown>;
    result?: unknown;
  }>;
}

export interface ChatResponse {
  response: string;
  decision_trace?: Decision;
  tool_calls: Array<{
    name: string;
    arguments: Record<string, unknown>;
    result?: unknown;
  }>;
  similar_decisions: Decision[];
}

export interface SimilarDecision {
  decision: Decision;
  similarity_score: number;
  similarity_type: string;
}

export interface CausalChain {
  decision_id: string;
  causes: Decision[];
  effects: Decision[];
  depth: number;
}

// API Functions

// Chat
export async function sendChatMessage(
  message: string,
  conversationHistory: ChatMessage[] = []
): Promise<ChatResponse> {
  const response = await api.post('/api/chat', {
    message,
    conversation_history: conversationHistory,
  });
  return response.data;
}

// Customers
export async function searchCustomers(query: string, limit = 10): Promise<Customer[]> {
  const response = await api.get('/api/customers/search', {
    params: { query, limit },
  });
  return response.data;
}

export async function getCustomer(customerId: string): Promise<Customer> {
  const response = await api.get(`/api/customers/${customerId}`);
  return response.data;
}

export async function getCustomerDecisions(customerId: string): Promise<Decision[]> {
  const response = await api.get(`/api/customers/${customerId}/decisions`);
  return response.data;
}

// Decisions
export async function getDecision(decisionId: string): Promise<Decision> {
  const response = await api.get(`/api/decisions/${decisionId}`);
  return response.data;
}

export async function getSimilarDecisions(
  decisionId: string,
  limit = 5,
  similarityType: 'structural' | 'semantic' | 'hybrid' = 'hybrid'
): Promise<SimilarDecision[]> {
  const response = await api.get(`/api/decisions/${decisionId}/similar`, {
    params: { limit, similarity_type: similarityType },
  });
  return response.data;
}

export async function getCausalChain(decisionId: string, depth = 3): Promise<CausalChain> {
  const response = await api.get(`/api/decisions/${decisionId}/causal-chain`, {
    params: { depth },
  });
  return response.data;
}

export async function recordDecision(decision: Partial<Decision>): Promise<Decision> {
  const response = await api.post('/api/decisions', decision);
  return response.data;
}

// Policies
export async function getPolicies(): Promise<Array<{ id: string; name: string; rules: string[] }>> {
  const response = await api.get('/api/policies');
  return response.data;
}

export async function getPolicy(policyId: string): Promise<{ id: string; name: string; rules: string[] }> {
  const response = await api.get(`/api/policies/${policyId}`);
  return response.data;
}

// Graph Visualization
export async function getGraphData(
  centerNodeId?: string,
  depth = 2,
  nodeTypes?: string[]
): Promise<GraphData> {
  const response = await api.get('/api/graph', {
    params: {
      center_node_id: centerNodeId,
      depth,
      node_types: nodeTypes?.join(','),
    },
  });
  return response.data;
}

export async function getDecisionGraph(decisionId: string, depth = 2): Promise<GraphData> {
  const response = await api.get(`/api/graph/decision/${decisionId}`, {
    params: { depth },
  });
  return response.data;
}

// GDS Analytics
export async function runFastRP(): Promise<{ nodes_updated: number }> {
  const response = await api.post('/api/gds/fastrp');
  return response.data;
}

export async function detectCommunities(): Promise<Array<{ community_id: number; members: string[] }>> {
  const response = await api.get('/api/gds/communities');
  return response.data;
}

export async function getInfluenceScores(limit = 20): Promise<Array<{ id: string; score: number }>> {
  const response = await api.get('/api/gds/influence', {
    params: { limit },
  });
  return response.data;
}

export async function detectFraudPatterns(
  accountId: string
): Promise<{ risk_score: number; patterns: string[]; similar_accounts: string[] }> {
  const response = await api.get(`/api/gds/fraud-patterns/${accountId}`);
  return response.data;
}

// Vector Search
export async function semanticSearch(
  query: string,
  nodeType = 'Decision',
  limit = 10
): Promise<Array<{ id: string; score: number; content: string }>> {
  const response = await api.post('/api/vector/search', {
    query,
    node_type: nodeType,
    limit,
  });
  return response.data;
}

export async function hybridSearch(
  query: string,
  nodeType = 'Decision',
  limit = 10
): Promise<Array<{ id: string; semantic_score: number; structural_score: number; combined_score: number }>> {
  const response = await api.post('/api/vector/hybrid-search', {
    query,
    node_type: nodeType,
    limit,
  });
  return response.data;
}

export default api;
