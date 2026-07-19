import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import type { RegistryClient } from "./registry-client.js";
import type { AssembleRequest } from "./types.js";

export function createDTAEServer(client: RegistryClient): Server {
  const server = new Server(
    { name: "dtae-mcp", version: "0.1.0" },
    { capabilities: { tools: {} } }
  );

  let currentQuery = "";
  let currentPhase: AssembleRequest["phase"] = "execution";

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    const response = await client.assemble({
      query: currentQuery || "general task",
      phase: currentPhase,
    });

    return {
      tools: response.tools.map((t) => ({
        name: t.name,
        description: t.description,
        inputSchema: {
          type: "object" as const,
          ...(t.parameters as object),
        },
      })),
    };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    // Update context signal so next ListTools reflects current state
    currentQuery = `calling ${name}`;

    await client.recordUsage(name, "session", Date.now());

    // Return a clear error — actual execution happens in the upstream tool server.
    // DTAE is a selection proxy, not an executor.
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify({
            _dtae: "proxy",
            tool: name,
            args,
            message:
              "Route this call to the upstream tool server registered for this tool.",
          }),
        },
      ],
    };
  });

  return server;
}
