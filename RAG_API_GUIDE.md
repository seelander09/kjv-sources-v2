# KJV Sources API Guide

## Overview

The API is served by `src/kjv_sources/api.py` and targets local Qdrant-backed analysis and visualization workflows.

- Base URL: `http://127.0.0.1:8001`
- OpenAPI docs: `http://127.0.0.1:8001/docs`
- Liveness: `GET /health`
- Readiness: `GET /ready`

## Start the API

```powershell
.\start_api_server.ps1
```

Or:

```powershell
python -m uvicorn src.kjv_sources.api:app --reload --port 8001
```

## Security Controls

- `ALLOWED_ORIGINS` controls CORS (comma-separated)
- `ALLOW_FILE_ORIGIN=true` allows `file://` via origin `null`
- `REQUIRE_API_KEY=true` enables API key checks for API routes
- `KJV_API_KEY` defines required key value (`X-API-Key`)
- In-memory request rate limiting is enabled by:
  - `RATE_LIMIT_REQUESTS` (default `120`)
  - `RATE_LIMIT_WINDOW_SECONDS` (default `60`)

## Core Endpoint Groups

### Bird's Eye

- `GET /api/v1/bird-eye/source-stratigraphy`
- `GET /api/v1/bird-eye/source-flow-network`
- `GET /api/v1/bird-eye/doublet-heatmap`
- `GET /api/v1/bird-eye/source-dominance-matrix`
- `GET /api/v1/bird-eye/timeline`

### Doublets and Verses

- `GET /api/v1/doublets/compare`
- `GET /api/v1/doublets/timeline`
- `GET /api/v1/doublets/source-contribution-timeline`
- `GET /api/v1/verses/by-chapter`
- `GET /api/v1/verses/search`

### ML Insights

- `GET /api/v1/ml/embedding-projection`
- `GET /api/v1/ml/similarity-network`
- `GET /api/v1/ml/feature-analysis`

ML endpoints include deterministic cache metadata:

- `meta.cache_key`
- `meta.collection_stamp`

## Notes

- This guide supersedes older references to `rag_api_server.py` and port `8000`.
- API error responses are sanitized for production-safe behavior.
