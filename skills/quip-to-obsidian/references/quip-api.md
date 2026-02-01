# Quip API Reference for Blob Downloads

## Authentication

### Obtaining a Token

1. Navigate to your Quip instance's developer token page:
   - Amazon internal: `https://quip-amazon.com/dev/token`
   - Public Quip: `https://quip.com/dev/token`

2. Copy the generated token (format: `BASE64_ID|TIMESTAMP|SIGNATURE`)

### Token Format

Quip API tokens contain three pipe-separated components:

```text
R2NLOU1BZHNVQmc=|1801222477|8F2n7n3+K4ZBTlL79N1bUVyHYJ7z7RNCZ+aG8bw5YWQ=
│                │           │
│                │           └── Signature (base64)
│                └── Expiration timestamp (Unix epoch)
└── Encoded user ID (base64)
```

**Important**: Tokens contain special characters (`|`, `=`, `+`) that require proper quoting in shell scripts.

### Using the Token

```bash
# Authorization header format
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  "https://platform.quip-amazon.com/1/blob/THREAD_ID/BLOB_ID"
```

## Blob API Endpoints

### Amazon Internal Quip

```text
Base URL: https://platform.quip-amazon.com
Blob endpoint: /1/blob/{thread_id}/{blob_id}
```

### Public Quip

```text
Base URL: https://platform.quip.com
Blob endpoint: /1/blob/{thread_id}/{blob_id}
```

## Blob URL Structure

### In Markdown Documents

When Quip documents are exported to markdown, embedded images appear as reference-style links:

```markdown
![Image description][1]

[1]: /blob/YPB9AAFeXJF/-YJg5mj0jDMMpAoTT-X06w
```

### URL Components

```text
/blob/YPB9AAFeXJF/-YJg5mj0jDMMpAoTT-X06w
      │            │
      │            └── Blob ID (base64-like, may contain - and _)
      └── Thread ID (document identifier)
```

### Full API URL

```text
https://platform.quip-amazon.com/1/blob/YPB9AAFeXJF/-YJg5mj0jDMMpAoTT-X06w
│                               │ │    │            │
│                               │ │    │            └── Blob ID
│                               │ │    └── Thread ID
│                               │ └── API version
│                               └── Blob endpoint
└── Platform base URL
```

## Response Handling

### Success (HTTP 200)

- Returns raw binary image data
- Content-Type header indicates image format (image/png, image/jpeg, etc.)

### Common Errors

| HTTP Code | Meaning      | Solution                             |
| --------- | ------------ | ------------------------------------ |
| 400       | Bad Request  | Check token format and quoting       |
| 401       | Unauthorized | Token expired or invalid             |
| 403       | Forbidden    | No access to this document           |
| 404       | Not Found    | Blob deleted or thread doesn't exist |

## File Type Detection

Downloaded blobs should be type-detected since Quip doesn't include extensions:

```bash
# Using file command
file_type=$(file -b --mime-type downloaded_file.tmp)

# Common types
# image/png  -> .png
# image/jpeg -> .jpg
# image/gif  -> .gif
# image/svg+xml -> .svg
# image/webp -> .webp
# application/pdf -> .pdf
```

## Rate Limiting

Quip API has rate limits. For large migrations:

- Add delays between requests (0.5-1 second)
- Use batch processing with progress tracking
- Handle 429 (Too Many Requests) with exponential backoff

```bash
# Simple rate limiting
while read blob_path; do
    download_blob "$blob_path"
    sleep 0.5  # Half-second delay
done < blob_list.txt
```

## amzn-mcp Integration

The Amazon internal MCP server (`amzn-mcp`) can also access Quip content:

```bash
# Configure token
echo 'QUIP_API_TOKEN="your-token"' > ~/.amazon-internal-mcp-server/.env

# Test with MCP
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"read_internal_website","arguments":{"url":"https://quip-amazon.com/DOCUMENT_ID"}}}' | amzn-mcp
```

**Note**: The `read_internal_website` tool returns document metadata/content but doesn't directly download blobs. Use
the direct API for blob downloads.

## Extracting Blob References

### Find All Blob References

```bash
# Extract unique blob paths from markdown files
grep -rhoE '/blob/[A-Za-z0-9]+/[A-Za-z0-9_-]+' /path/to/docs | sort -u
```

### Filter Non-Quip Patterns

Some documentation may contain `/blob/` in other contexts:

```bash
# Filter out common false positives
grep -v "main/articles\|pattern/\|github.com" blob_list.txt
```

## Naming Convention

Downloaded blobs use this naming pattern:

```text
{thread_id}_{blob_id}.{extension}
```

Example:

```text
YPB9AAFeXJF_-YJg5mj0jDMMpAoTT-X06w.png
```

This preserves the original identifiers for traceability while adding the detected file extension.

## Troubleshooting

### Token Issues

**Symptom**: "Token verification failed with status 400"

**Solutions**:

1. Ensure token is properly quoted (special characters)
2. Check token hasn't expired (middle component is Unix timestamp)
3. Verify using correct API endpoint for your Quip instance

### Download Failures

**Symptom**: Some blobs return 404

**Causes**:

- Image was deleted from source document
- Thread (document) was deleted
- No permission to access the document

**Solution**: Log failures and review manually; some images may no longer exist.

### Obsidian Rendering

**Symptom**: Images don't render in Obsidian

**Solutions**:

1. Use inline markdown syntax: `![alt](path)` not reference-style
2. Check relative paths are correct
3. Try Obsidian wikilinks: `![[attachments/image.png]]`
4. Ensure no special characters in filenames
