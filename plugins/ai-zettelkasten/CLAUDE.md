# AI Zettelkasten Plugin

Python plugin for Zettelkasten knowledge management with pluggable vector store and embeddings backends.

## Development

Requires Python >= 3.11. Uses [uv](https://docs.astral.sh/uv/) as the package and project manager.

### Setup

```bash
uv venv --python 3.11 && uv pip install -e ".[dev]"
```

### Commands

| Command            | Description                                    |
| ------------------ | ---------------------------------------------- |
| `uv run test`      | Run tests                                      |
| `uv run test-cov`  | Run tests with coverage report                 |
| `uv run lint`      | Check lint rules (ruff)                        |
| `uv run lint-fix`  | Auto-fix lint issues                           |
| `uv run fmt`       | Format code (ruff format)                      |
| `uv run fmt-check` | Check formatting without changes               |
| `uv run typecheck` | Run mypy type checking                         |
| `uv run check`     | Run all checks (format + lint + types + tests) |
| `uv run fix`       | Auto-fix formatting + lint                     |

## Architecture

### Vector Store Backends

Configured via `ZETTELKASTEN_BACKEND` env var:

- **`chromadb`** (default) - Local persistent storage, no cloud credentials needed
- **`s3`** - AWS S3 Vectors, requires AWS credentials and `pip install -e ".[s3]"`

### Embeddings Providers

Configured via `ZETTELKASTEN_EMBEDDINGS` env var:

- **`ollama`** (default) - Local Ollama instance (`nomic-embed-text`, 768-dim)
- **`bedrock`** - AWS Bedrock Titan (`amazon.titan-embed-text-v1`, 1536-dim)
- **`local`** - sentence-transformers (`all-MiniLM-L6-v2`, 384-dim), requires `pip install -e ".[local-embeddings]"`

### Environment Variables

| Variable                  | Default                  | Description                    |
| ------------------------- | ------------------------ | ------------------------------ |
| `ZETTELKASTEN_BACKEND`    | `chromadb`               | Vector store backend           |
| `ZETTELKASTEN_EMBEDDINGS` | `ollama`                 | Embeddings provider            |
| `ZETTELKASTEN_CHROMA_DIR` | `~/.chroma-data`         | ChromaDB storage path          |
| `ZETTELKASTEN_COLLECTION` | `zettelkasten`           | ChromaDB collection name       |
| `OLLAMA_BASE_URL`         | `http://localhost:11434` | Ollama API URL                 |
| `ZETTELKASTEN_BUCKET`     | `zettelkasten-prod`      | S3 Vectors bucket (s3 backend) |
| `ZETTELKASTEN_INDEX`      | `knowledge-index`        | S3 Vectors index (s3 backend)  |

## Standards

- Lint rules from [cajias/lint-configs](https://github.com/cajias/lint-configs)
- Google-style docstrings, type hints required
- Line length: 120
- Test coverage threshold: 80%
