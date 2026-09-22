@echo off
REM Compatibility launcher for the current FastAPI module.
setlocal

echo Starting KJV Sources API server...
echo API:  http://127.0.0.1:8001
echo Docs: http://127.0.0.1:8001/docs
echo.

set PYTHONPATH=%CD%;%PYTHONPATH%
python -m uvicorn src.kjv_sources.api:app --reload --port 8001
