@echo off
echo Starting Document Ingestion Pipeline...
echo.

REM Activate virtual environment
call sources-env\Scripts\activate.bat

REM Run the pipeline
python document_ingestion_pipeline.py

echo.
echo Pipeline completed. Check the results above.
pause
