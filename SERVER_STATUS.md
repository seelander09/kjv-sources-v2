# KJV Sources API Status

## Current Runtime Contract

- API server: `http://127.0.0.1:8001`
- OpenAPI docs: `http://127.0.0.1:8001/docs`
- Liveness: `GET /health`
- Readiness: `GET /ready`

## Start Commands

```powershell
# Start API only
.\start_api_server.ps1

# Start API + dashboard helper
.\run_project.ps1
```

## Current Architecture Notes

- Active vector layer: **Qdrant**
- FastAPI app module: `src/kjv_sources/api.py`
- Local Qdrant data path: `qdrant_data/`
- Bird's Eye endpoints are under `/api/v1/bird-eye/*`

## Operational Checks

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/health" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8001/ready" -Method GET
```

## Security Defaults

- CORS origins are configured by `ALLOWED_ORIGINS`
- API-key enforcement can be enabled via `REQUIRE_API_KEY=true` and `KJV_API_KEY`
- Basic in-memory rate limiting is enabled for API routes
