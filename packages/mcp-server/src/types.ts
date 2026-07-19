export interface ToolEntry {
  id: string;
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  tags: string[];
  embedding: number[];
  usageCount: number;
}

export interface AssembleRequest {
  query: string;
  phase?: "planning" | "execution" | "verification" | "reporting";
  sessionId?: string;
  maxTools?: number;
  forceReassemble?: boolean;
}

export interface AssembleResponse {
  tools: ToolEntry[];
  trigger?: string;
  tokenEstimate: number;
}

export interface DTAEClientConfig {
  registryUrl: string;
  maxTools?: number;
  maxToolTokens?: number;
}
