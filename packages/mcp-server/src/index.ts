#!/usr/bin/env node
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { RegistryClient } from "./registry-client.js";
import { createDTAEServer } from "./server.js";

const REGISTRY_URL = process.env.DTAE_REGISTRY_URL ?? "http://localhost:8000";

async function main(): Promise<void> {
  const client = new RegistryClient(REGISTRY_URL);
  const server = createDTAEServer(client);
  const transport = new StdioServerTransport();

  await server.connect(transport);
  process.stderr.write(`DTAE MCP server running — registry: ${REGISTRY_URL}\n`);
}

main().catch((err) => {
  process.stderr.write(`Fatal: ${err}\n`);
  process.exit(1);
});
