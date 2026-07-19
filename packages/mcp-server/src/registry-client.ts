import type { AssembleRequest, AssembleResponse, ToolEntry } from "./types.js";

export class RegistryClient {
  private readonly baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async assemble(req: AssembleRequest): Promise<AssembleResponse> {
    const res = await fetch(`${this.baseUrl}/assemble`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });

    if (!res.ok) {
      throw new Error(`Registry error ${res.status}: ${await res.text()}`);
    }

    return res.json() as Promise<AssembleResponse>;
  }

  async listAll(): Promise<ToolEntry[]> {
    const res = await fetch(`${this.baseUrl}/tools`);
    if (!res.ok) throw new Error(`Registry error ${res.status}`);
    return res.json() as Promise<ToolEntry[]>;
  }

  async recordUsage(toolId: string, sessionId: string, step: number): Promise<void> {
    await fetch(`${this.baseUrl}/usage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ toolId, sessionId, step }),
    }).catch(() => {});
  }
}
