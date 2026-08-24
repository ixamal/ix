#!/usr/bin/env node
/**
 * Rekordbox / Traktor OSC stub.
 * The live copy belongs in ~/local_tools/mcp_adapters — never in git.
 */
const HOST = process.env.DJ_OSC_HOST || "127.0.0.1";
const PORT = Number(process.env.DJ_OSC_PORT || "9000");

if (HOST !== "127.0.0.1" && HOST !== "localhost") {
  console.error(`Refusing non-loopback host ${HOST}`);
  process.exit(1);
}

console.error(`dj stub ready on ${HOST}:${PORT} (stdio MCP not wired in this stub)`);
console.log("Placeholder. Wire Pioneer Pro DJ Link or Traktor OSC here.");
