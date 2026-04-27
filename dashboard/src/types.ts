/**
 * TypeScript types matching Python models
 */

export type MessageType = 
  | "TASK"
  | "RESULT"
  | "ERROR"
  | "TOOL_CALL"
  | "TOOL_RESULT"
  | "SYSTEM";

export interface WireMessage {
  id: string;
  session_id: string;
  parent_id: string | null;
  sender: string;
  receiver: string;
  type: MessageType;
  content: string;
  metadata: Record<string, any>;
  tokens_in: number;
  tokens_out: number;
  model: string | null;
  latency_ms: number;
  cost_usd: number;
  timestamp: string;
  tags: string[];
}

export interface Session {
  id: string;
  name: string | null;
  started_at: string;
  ended_at: string | null;
  message_count: number;
  total_tokens: number;
  total_cost_usd: number;
  agents: string[];
}

export interface WebSocketEvent {
  event: "message" | "session_start" | "session_end";
  data: any;
}

export interface Stats {
  total_messages: number;
  total_sessions: number;
  total_tokens: number;
  total_cost_usd: number;
}

// Graph types
export interface GraphNode {
  id: string;
  message_count: number;
  total_tokens: number;
  dominant_type: MessageType;
}

export interface GraphEdge {
  source: string;
  target: string;
  count: number;
  dominant_type: MessageType;
  total_tokens: number;
  avg_latency_ms: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// D3 types (with x, y for simulation)
export interface D3Node extends GraphNode {
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface D3Edge {
  source: D3Node | string;
  target: D3Node | string;
  count: number;
  dominant_type: MessageType;
  total_tokens: number;
  avg_latency_ms: number;
}

// Message type colors
export const MESSAGE_TYPE_COLORS: Record<MessageType, string> = {
  TASK: "bg-aw-teal text-slate-900",
  RESULT: "bg-aw-purple text-slate-900",
  ERROR: "bg-aw-red text-slate-900",
  TOOL_CALL: "bg-aw-amber text-slate-900",
  TOOL_RESULT: "bg-aw-amber-dim text-white",
  SYSTEM: "bg-aw-gray text-white",
};

// Graph colors (for D3)
export const GRAPH_COLORS: Record<MessageType, string> = {
  TASK: "#5DCAA5",
  RESULT: "#AFA9EC",
  ERROR: "#F09595",
  TOOL_CALL: "#EF9F27",
  TOOL_RESULT: "#B87C14",
  SYSTEM: "#888888",
};
