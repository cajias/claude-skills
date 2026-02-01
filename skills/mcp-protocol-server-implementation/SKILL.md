---
name: mcp-protocol-server-implementation
description: |
  Requirements for implementing an MCP (Model Context Protocol) server that works with
  the official @modelcontextprotocol/sdk client. Use when: (1) implementing an MCP server
  from scratch, (2) getting "Expected initialize response" errors, (3) MCP client fails
  to connect or times out, (4) tools/list returns successfully but client doesn't recognize
  server, (5) implementing MCP Streamable HTTP transport. Covers initialize method,
  notification handling, SSE response format, and session management.
author: Claude Code
version: 1.0.0
date: 2026-01-27
---

# MCP Protocol Server Implementation

## Problem

When implementing a custom MCP server, the official MCP SDK client
(`@modelcontextprotocol/sdk`) with `StreamableHTTPClientTransport` fails to connect
or times out, even when `tools/list` returns correct JSON-RPC responses.

## Context / Trigger Conditions

- Building a custom MCP server (Lambda, Express, etc.) from scratch
- Using `StreamableHTTPClientTransport` from `@modelcontextprotocol/sdk`
- Client throws "Expected initialize response" error
- Client times out during connection
- Server returns valid JSON-RPC for `tools/list` but client doesn't work
- Direct curl to `tools/list` works but SDK client fails

## Solution

### 1. Handle the `initialize` Method (REQUIRED)

The SDK client sends `initialize` as its first request. Your server MUST respond:

```typescript
if (method === "initialize") {
  return {
    jsonrpc: "2.0",
    id,
    result: {
      protocolVersion: "2024-11-05", // Current MCP protocol version
      serverInfo: {
        name: "your-server-name",
        version: "1.0.0",
      },
      capabilities: {
        tools: {}, // Indicates server supports tools
      },
    },
  };
}
```

### 2. Handle Notifications (REQUIRED)

The client sends `notifications/initialized` after initialize. Per JSON-RPC 2.0 spec,
notifications have NO `id` field and servers MUST NOT send a response body.

```typescript
// Check if message is a notification
function isNotification(message: McpRequest): boolean {
  return message.id === undefined;
}

// In handler:
if (isNotification(mcpRequest)) {
  // Return 202 Accepted with empty body
  return { statusCode: 202, headers, body: "" };
}
```

### 3. SSE Response Format (RECOMMENDED)

When client sends `Accept: text/event-stream`, respond in SSE format:

```typescript
function formatAsSSE(response: McpResponse): string {
  return `event: message\ndata: ${JSON.stringify(response)}\n\n`;
}

function clientAcceptsSSE(acceptHeader: string | undefined): boolean {
  return acceptHeader?.includes("text/event-stream") ?? false;
}

// Set Content-Type accordingly
const contentType = useSSE ? "text/event-stream" : "application/json";
```

### 4. Session Management (RECOMMENDED)

Track sessions via `mcp-session-id` header:

```typescript
const incomingSessionId = headers["mcp-session-id"];
const sessionId = incomingSessionId ?? randomUUID();

// Include in response headers
responseHeaders["mcp-session-id"] = sessionId;
responseHeaders["Access-Control-Expose-Headers"] = "mcp-session-id";
```

### 5. CORS Headers (REQUIRED for browser clients)

```typescript
const headers = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "Content-Type,Authorization,mcp-session-id,mcp-protocol-version",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Expose-Headers": "mcp-session-id",
  "Cache-Control": "no-cache",
};
```

## Verification

1. Test with curl first:

```bash
# Test initialize
curl -X POST https://your-server/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}'

# Should return protocolVersion, serverInfo, capabilities

# Test tools/list
curl -X POST https://your-server/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
```

1. Then test with MCP SDK client:

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const client = new Client({ name: "test", version: "1.0.0" });
const transport = new StreamableHTTPClientTransport(
  new URL("https://your-server/mcp"),
);
await client.connect(transport);
const tools = await client.listTools();
```

## Example

Complete minimal MCP server handler:

```typescript
export function handler(event: APIGatewayProxyEvent): APIGatewayProxyResult {
  const headers = { "Content-Type": "application/json" /* CORS headers */ };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers, body: "" };
  }

  const request = JSON.parse(event.body ?? "{}");

  // Handle notifications (no id = notification)
  if (request.id === undefined) {
    return { statusCode: 202, headers, body: "" };
  }

  // Handle methods
  switch (request.method) {
    case "initialize":
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: request.id,
          result: {
            protocolVersion: "2024-11-05",
            serverInfo: { name: "my-server", version: "1.0.0" },
            capabilities: { tools: {} },
          },
        }),
      };

    case "tools/list":
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: request.id,
          result: { tools: MY_TOOLS },
        }),
      };

    case "tools/call":
      // Handle tool execution
      break;

    default:
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: request.id,
          error: {
            code: -32601,
            message: `Method not found: ${request.method}`,
          },
        }),
      };
  }
}
```

## Notes

- **Protocol Version**: Use `2024-11-05` as of early 2026. Check MCP spec for updates.
- **JSON-RPC Error Codes**:
  - `-32700`: Parse error
  - `-32600`: Invalid request
  - `-32601`: Method not found
  - `-32603`: Internal error
- **Method Call Order**: Client always sends `initialize` first, then `notifications/initialized`,
  then other methods like `tools/list`.
- **Timeout Issues**: If client times out, check that `initialize` response is correct—this is
  the most common cause.

## References

- [MCP Protocol Specification](https://modelcontextprotocol.io/specification)
- [MCP SDK GitHub](https://github.com/modelcontextprotocol/sdk)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
