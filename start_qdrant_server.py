"""
Start an embedded Qdrant server for local access without emoji output.
"""

import subprocess
import sys
from pathlib import Path


def start_qdrant_server() -> bool:
    qdrant_path = Path("qdrant_data")
    if not qdrant_path.exists():
        print("Qdrant data directory not found:", qdrant_path.resolve())
        return False

    print("Starting embedded Qdrant server...")
    print(f"Using data directory: {qdrant_path.resolve()}")

    cmd = [
        sys.executable,
        "-c",
        (
            "import sys,time\n"
            "sys.path.append('.')\n"
            "from qdrant_client import QdrantClient\n"
            "client = QdrantClient(path='qdrant_data')\n"
            "print('Qdrant server started on http://localhost:6333/dashboard')\n"
            "try:\n"
            "    cols = client.get_collections()\n"
            "    for coll in cols.collections:\n"
            "        info = client.get_collection(coll.name)\n"
            "        print(f' - {coll.name}: {info.points_count} points')\n"
            "except Exception as exc:\n"
            "    print(f'Failed to list collections: {exc}')\n"
            "print('Press Ctrl+C to stop the server.')\n"
            "try:\n"
            "    while True:\n"
            "        time.sleep(1)\n"
            "except KeyboardInterrupt:\n"
            "    print('Server stopped.')\n"
        ),
    ]

    try:
        subprocess.run(cmd, check=False)
    except Exception as exc:  # pragma: no cover - defensive
        print("Error starting Qdrant server:", exc)
        return False

    return True


if __name__ == "__main__":
    start_qdrant_server()
