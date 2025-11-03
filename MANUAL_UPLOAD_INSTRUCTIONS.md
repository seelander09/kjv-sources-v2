# Manual Upload Instructions

## Problem: Qdrant Database Locked

The Qdrant database is locked because the API server or another process has it open.

## Solution Steps

### Step 1: Stop ALL Processes

**Close these manually:**
1. Stop the API server (press `Ctrl+C` in the terminal running uvicorn)
2. Close ALL terminal windows that might have Python processes
3. Check Task Manager for any remaining Python processes

### Step 2: Wait and Upload

After stopping everything, wait 10 seconds, then run:

```powershell
python upload_torah_with_progress.py
```

### Step 3: Alternative - Use Direct Upload Script

If the above doesn't work, try uploading directly:

```powershell
python -c "import sys; sys.path.insert(0, 'src'); from kjv_sources.qdrant_client import KJVQdrantClient, create_qdrant_client; client = create_qdrant_client(use_local=True); client.upload_book_data('Genesis', 'output/Genesis/Genesis.csv')"
```

### Step 4: Check if Data Already Exists

Run this to check if data is already in Qdrant:

```powershell
python -c "import sys; sys.path.insert(0, 'src'); from kjv_sources.qdrant_client import create_qdrant_client; client = create_qdrant_client(use_local=True); stats = client.get_collection_stats(); print(f'Total points: {stats.get(\"total_points\", 0)}')"
```

If it shows points > 0, the data is already there and you just need to refresh the browser!

### Step 5: Restart API Server

After upload completes:

```powershell
.\start_api_server.ps1
```

## Alternative: Use Qdrant Server Mode

If local file mode keeps having locking issues, you can use Qdrant server mode:

1. Start Qdrant server:
   ```powershell
   docker-compose --profile qdrant up -d
   ```

2. Modify the client to use server mode instead of local file mode

---

**Current Status**: The API server is running but Qdrant shows 0 points, indicating data needs to be uploaded.

