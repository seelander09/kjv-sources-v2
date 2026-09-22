# Dependency Management

## Strategy

- `requirements.txt` is the single source of truth for base runtime dependencies.
- `api_requirements.txt` layers API/test extras on top of `requirements.txt`.
- CI installs both files to validate the full runtime path.

## Upgrade Workflow

1. Update versions in `requirements.txt` first.
2. Keep API-only/test-only packages in `api_requirements.txt`.
3. Run:
   - `ruff check .`
   - `pytest -q`
4. Open a PR and let CI validate lint/tests/secrets.
