# Example: AWS Infrastructure Task

## Scenario

You need to create AWS infrastructure using CDK for a serverless application.

## User Request

```
tell q to create a CDK stack for a Lambda function with S3 trigger and DynamoDB table
```

## Agent Selection Process

1. **Parse request:**
   - Trigger: "tell q to"
   - Task: "create a CDK stack for a Lambda function with S3 trigger and DynamoDB table"
   - Explicit agent: None

2. **Keyword analysis:**
   - Detected keywords: CDK, Lambda, S3, DynamoDB
   - Matched agent: `aws-expert` (has AWS, CDK, Lambda, S3 keywords)
   - Confidence: High

3. **Selected agent:** `aws-expert`

## Command Execution

```bash
q chat --agent aws-expert --no-interactive --trust-all-tools "create a CDK stack for a Lambda function with S3 trigger and DynamoDB table"
```

## Response to User

```
Starting Q agent 'aws-expert' in background to: create a CDK stack for a Lambda function with S3 trigger and DynamoDB table

Command: q chat --agent aws-expert --no-interactive --trust-all-tools "create a CDK stack for a Lambda function with S3 trigger and DynamoDB table"
Background process ID: async_session_123

You can check progress with: read_bash sessionId: async_session_123
Or stop the agent with: stop_bash sessionId: async_session_123
```

## Expected Outcome

The aws-expert agent will:

1. Create a new CDK stack file
2. Define Lambda function with appropriate configuration
3. Set up S3 bucket with event notification
4. Create DynamoDB table with appropriate schema
5. Configure IAM roles and permissions
6. Add necessary dependencies to package.json
7. Provide deployment instructions

## Monitoring Progress

After 30 seconds, check progress:

```bash
read_bash sessionId: async_session_123 delay: 5
```

Expected output:

```
Creating CDK stack structure...
✓ Created lib/my-stack.ts
✓ Configured Lambda function
✓ Added S3 trigger
✓ Created DynamoDB table
✓ Set up IAM permissions
✓ Updated dependencies

Stack created successfully at lib/my-stack.ts
To deploy: cdk deploy
```

## Why aws-expert Agent?

The `aws-expert` agent is the best choice because:

- Has access to AWS documentation MCP server
- Understands CDK patterns and best practices
- Can generate proper IAM policies
- Familiar with Lambda, S3, and DynamoDB integration
- Has diagram MCP server for architecture visualization
