# DFS Storage Node

Storage node microservice for chunk storage and retrieval.

## Responsibilities

- Store chunks: `POST /chunks/{chunk_id}`
- Serve chunks via signed URL: `GET /chunks/{chunk_id}`
- Delete chunks: `DELETE /chunks/{chunk_id}`
- Report health: `GET /health`
- Register itself and send heartbeat to master service

## Requirements

- Python 3.11+
- Reachable master service (`DFS_MASTER_BASE_URL`)
- Same shared secrets as master:
  - `DFS_CHUNK_URL_SECRET`
  - `DFS_INTERNAL_TOKEN`

## Quick Start

1. Create and activate virtual environment.
2. Install dependencies.
3. Create `.env` from `.env.template`.
4. Start the service.

Windows PowerShell:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.template .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

## Environment Variables

- `STORAGE_NODE_NAME`: node name in master metadata
- `STORAGE_PUBLIC_BASE_URL`: public URL used by master to access this node
- `STORAGE_CHUNKS_DIR`: local path for chunks
- `DFS_MASTER_BASE_URL`: master base URL
- `DFS_HEARTBEAT_INTERVAL_S`: heartbeat interval in seconds
- `DFS_CHUNK_URL_SECRET`: shared chunk URL signing secret
- `DFS_INTERNAL_TOKEN`: shared internal token
