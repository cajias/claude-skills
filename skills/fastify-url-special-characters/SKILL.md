---
name: fastify-url-special-characters
description: |
  Fix test failures when validating route parameters with special characters in Fastify.
  Use when: (1) Tests expect 400 but get 404 for invalid route parameters,
  (2) Special characters like # @ are being stripped from URLs before handler runs,
  (3) Route parameter validation tests fail unexpectedly.
  Covers Fastify URL parsing behavior and how to test parameter validation correctly.
author: Claude Code
version: 1.0.0
date: 2026-01-25
---

# Fastify URL Special Characters in Route Parameters

## Problem

When testing route parameter validation in Fastify, tests may fail because certain
special characters are handled at the routing level before your handler runs.
You expect `400 Bad Request` from your validation but get `404 Not Found` because
Fastify never matched your route.

## Context / Trigger Conditions

- Test expects `400` status code but receives `404`
- Testing route parameter validation with special characters
- Using Fastify with dynamic route parameters like `/gateways/:gatewayId/mcp`
- Characters like `#`, `?`, or URL-encoded values in test URLs

Example test that fails unexpectedly:

```typescript
// This test FAILS - gets 404 instead of 400
const response = await server.inject({
  method: "POST",
  url: "/gateways/invalid@gateway#id!/mcp",
  payload: validPayload,
});
expect(response.statusCode).toBe(400); // FAILS: gets 404
```

## Root Cause

Fastify (and most HTTP frameworks) parse URLs according to RFC 3986:

1. **`#` (hash/fragment)**: Everything after `#` is treated as a fragment and stripped
   - `/gateways/invalid@gateway#id/mcp` → `/gateways/invalid@gateway` (route doesn't match)

2. **`?` (query string)**: Everything after `?` is parsed as query parameters
   - `/gateways/test?id/mcp` → route is `/gateways/test` with query `id/mcp`

3. **URL encoding**: Some characters are decoded before routing
   - `%20` (space) is passed through to handler
   - `%2F` (/) may cause routing issues

## Solution

### Step 1: Identify Which Characters Fastify Passes Through

Characters that reach your handler (can be validated):

- Letters, numbers, hyphens, underscores: `a-z`, `A-Z`, `0-9`, `-`, `_`
- Dots: `.` (passed through)
- Spaces (URL-encoded as `%20`): decoded and passed through
- `@` symbol: passed through

Characters that DON'T reach your handler:

- `#` - Treated as fragment start, URL truncated
- `?` - Treated as query string start
- `/` - Path separator (even when encoded)

### Step 2: Update Tests to Use Passable Invalid Characters

```typescript
// BAD: These characters are stripped by Fastify router
url: "/gateways/invalid@gateway#id!/mcp"; // Gets 404, # truncates URL

// GOOD: Use characters that pass through but fail your validation
url: "/gateways/invalid.gateway.id/mcp"; // Gets 400, dots aren't alphanumeric
url: "/gateways/invalid gateway/mcp"; // Gets 400, spaces encoded as %20
```

### Step 3: Test Each Validation Rule Separately

```typescript
// Test for invalid characters (using dots)
it("should return 400 for invalid gateway ID format (with dot)", async () => {
  const response = await server.inject({
    method: "POST",
    url: "/gateways/invalid.gateway.id/mcp",
    payload: validPayload,
  });
  expect(response.statusCode).toBe(400);
});

// Test for too-long IDs (using valid chars but exceeding length)
it("should return 400 for gateway ID exceeding max length", async () => {
  const longId = "a".repeat(200); // Assuming max is 128
  const response = await server.inject({
    method: "POST",
    url: `/gateways/${longId}/mcp`,
    payload: validPayload,
  });
  // Note: Very long paths may return 404 due to path length limits
  expect([400, 404]).toContain(response.statusCode);
});
```

## Verification

Test that your validation pattern correctly rejects the characters you care about:

```typescript
// Validation regex: /^[a-zA-Z0-9_-]{1,128}$/
const GATEWAY_ID_PATTERN = /^[a-zA-Z0-9_-]{1,128}$/;

// These should FAIL validation (return false)
console.log(GATEWAY_ID_PATTERN.test("invalid.gateway")); // false - has dot
console.log(GATEWAY_ID_PATTERN.test("invalid gateway")); // false - has space
console.log(GATEWAY_ID_PATTERN.test("")); // false - empty

// These should PASS validation (return true)
console.log(GATEWAY_ID_PATTERN.test("valid-gateway")); // true
console.log(GATEWAY_ID_PATTERN.test("valid_gateway_123")); // true
```

## Example

Real-world fix from MCP Proxy service:

```typescript
// Before: Test failed with 404 because # was stripped
it("should return 400 for invalid gateway ID format", async () => {
  const response = await server.inject({
    method: "POST",
    url: "/gateways/invalid@gateway#id!/mcp", // # causes 404
    payload: validJsonRpcRequest,
  });
  expect(response.statusCode).toBe(400); // FAILS: gets 404
});

// After: Use dots instead, which Fastify passes through
it("should return 400 for invalid gateway ID format (with dot)", async () => {
  const response = await server.inject({
    method: "POST",
    url: "/gateways/invalid.gateway.id/mcp", // dots pass through
    payload: validJsonRpcRequest,
  });
  expect(response.statusCode).toBe(400); // PASSES
});
```

## Notes

- This behavior is consistent across most HTTP frameworks, not just Fastify
- The RFC 3986 URL spec defines this parsing behavior
- If you need to accept special characters in route parameters, consider:
  - Base64 encoding the parameter value
  - Using query parameters instead of path parameters
  - URL-encoding and decoding manually

## References

- [RFC 3986 - URI Generic Syntax](https://datatracker.ietf.org/doc/html/rfc3986)
- [Fastify Route Parameters](https://fastify.dev/docs/latest/Reference/Routes/#url-building)
