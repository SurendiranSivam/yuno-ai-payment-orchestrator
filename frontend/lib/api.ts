/**
 * API Client — typed HTTP client for backend communication.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// ── Agent API ────────────────────────────────────────────

export const agentAPI = {
  list: () => fetchAPI<Agent[]>("/api/agents"),
  get: (id: string) => fetchAPI<Agent>(`/api/agents/${id}`),
  create: (data: AgentCreatePayload) =>
    fetchAPI<Agent>("/api/agents", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Partial<AgentCreatePayload>) =>
    fetchAPI<Agent>(`/api/agents/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: string) =>
    fetch(`${API_BASE}/api/agents/${id}`, { method: "DELETE" }),
};

// ── Workflow API ─────────────────────────────────────────

export const workflowAPI = {
  list: () => fetchAPI<Workflow[]>("/api/workflows"),
  templates: () => fetchAPI<Workflow[]>("/api/workflows/templates"),
  create: (data: WorkflowCreatePayload) =>
    fetchAPI<Workflow>("/api/workflows", { method: "POST", body: JSON.stringify(data) }),
};

// ── Workflow Runs API ────────────────────────────────────

export const workflowRunAPI = {
  list: (limit = 20) => fetchAPI<WorkflowRun[]>(`/api/workflow-runs?limit=${limit}`),
  get: (id: string) => fetchAPI<WorkflowRunDetail>(`/api/workflow-runs/${id}`),
  trigger: (data: WorkflowTriggerPayload) =>
    fetchAPI<{ status: string; message: string }>("/api/workflow-runs", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// ── Monitoring API ───────────────────────────────────────

export const monitoringAPI = {
  stats: () => fetchAPI<DashboardStats>("/api/monitoring/stats"),
  events: (limit = 50) => fetchAPI<WorkflowEvent[]>(`/api/monitoring/events?limit=${limit}`),
};

// ── Conversations API ────────────────────────────────────

export const conversationAPI = {
  list: (limit = 50) => fetchAPI<Conversation[]>(`/api/conversations?limit=${limit}`),
};

// ── WhatsApp Simulation ──────────────────────────────────

export const whatsappAPI = {
  simulate: (data: { phone: string; message: string }) =>
    fetchAPI<{ status: string; message: string }>("/api/whatsapp/simulate", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// ── Types ────────────────────────────────────────────────

export interface Agent {
  id: string;
  name: string;
  role: string;
  system_prompt: string;
  model: string;
  config: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface AgentCreatePayload {
  name: string;
  role: string;
  system_prompt: string;
  model: string;
  config: Record<string, any>;
  is_active: boolean;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  graph_definition: any;
  is_template: boolean;
  status: string;
  created_at: string;
}

export interface WorkflowCreatePayload {
  name: string;
  description: string;
  graph_definition: any;
  is_template: boolean;
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  status: string;
  trigger_source: string;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
  started_at: string;
  completed_at: string | null;
}

export interface WorkflowEvent {
  id: string;
  workflow_run_id: string;
  agent_name: string;
  event_type: string;
  message: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface WorkflowRunDetail extends WorkflowRun {
  events: WorkflowEvent[];
  messages: InterAgentMessage[];
  token_usage: TokenUsageRecord[];
}

export interface InterAgentMessage {
  id: string;
  sender_agent: string;
  receiver_agent: string;
  content: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface TokenUsageRecord {
  id: string;
  agent_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  model: string;
  created_at: string;
}

export interface DashboardStats {
  total_agents: number;
  total_workflows: number;
  total_runs: number;
  active_runs: number;
  completed_runs: number;
  failed_runs: number;
  total_conversations: number;
  total_tokens_used: number;
}

export interface Conversation {
  id: string;
  workflow_run_id: string | null;
  user_phone: string;
  direction: string;
  message: string;
  created_at: string;
}

export interface WorkflowTriggerPayload {
  workflow_id?: string;
  customer_message: string;
  customer_phone?: string;
}
