# Example: Documentation Writing

## Scenario

You need comprehensive API documentation for your REST endpoints.

## User Request

```text
tell q to write API documentation for our user management endpoints
```

## Agent Selection Process

1. **Parse request:**
   - Trigger: "tell q to"
   - Task: "write API documentation for our user management endpoints"
   - Explicit agent: None

2. **Keyword analysis:**
   - Detected keywords: write, documentation, API
   - Matched agent: `amzn-docs` (has documentation, write keywords)
   - Confidence: High

3. **Selected agent:** `amzn-docs`

## Command Execution

```bash
q chat --agent amzn-docs --no-interactive --trust-all-tools "write API documentation for our user management endpoints"
```

## Response to User

```text
Starting Q agent 'amzn-docs' in background to: write API documentation for our user management endpoints

Command: q chat --agent amzn-docs --no-interactive --trust-all-tools "write API documentation for our user management endpoints"
Background process ID: async_session_456

You can check progress with: read_bash sessionId: async_session_456
Or stop the agent with: stop_bash sessionId: async_session_456
```

## Expected Outcome

The amzn-docs agent will:

1. Analyze existing code to identify endpoints
2. Document each endpoint with:
   - HTTP method and path
   - Request parameters
   - Request body schema
   - Response codes and schemas
   - Authentication requirements
   - Example requests and responses
3. Create structured markdown documentation
4. Use natural, professional writing style
5. Include table of contents
6. Add usage examples

## Monitoring Progress

After 45 seconds, check progress:

```bash
read_bash sessionId: async_session_456 delay: 5
```

Expected output:

```text
Analyzing user management endpoints...
✓ Found 8 endpoints in src/routes/users.ts
✓ Extracted request/response schemas
✓ Generating documentation...

Creating docs/api/user-management.md:
  - POST /api/users (Create User)
  - GET /api/users (List Users)
  - GET /api/users/:id (Get User)
  - PUT /api/users/:id (Update User)
  - DELETE /api/users/:id (Delete User)
  - POST /api/users/:id/reset-password (Reset Password)
  - GET /api/users/:id/activity (Get Activity)
  - PUT /api/users/:id/preferences (Update Preferences)

✓ Documentation created at docs/api/user-management.md
```

## Sample Output

The generated documentation might look like:

```markdown
# User Management API

## Overview

This API provides endpoints for managing user accounts, including creation,
retrieval, updates, and deletion.

## Authentication

All endpoints require authentication using JWT tokens in the Authorization header:

Authorization: Bearer <token>

## Endpoints

### Create User

**POST** `/api/users`

Creates a new user account.

**Request Body:**
...
```

## Why amzn-docs Agent?

The `amzn-docs` agent is the best choice because:

- Specialized in documentation generation
- Natural, professional writing style
- Understands API documentation patterns
- Can analyze code to extract endpoint information
- Produces well-structured, readable documentation
- Follows documentation best practices
