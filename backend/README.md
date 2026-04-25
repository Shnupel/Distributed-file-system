# DFS Master + Storage Nodes

Monorepo backend for a distributed file system built on FastAPI.

It contains:

- `app` - master node (auth, metadata, manifests, replication coordinator)
- `storage_app` - storage node (chunk storage/read endpoints)
- `shared` - shared contracts and cryptography helpers used by both apps

Master auth is production-oriented JWT with access/refresh token rotation, Redis-backed revocation, and async PostgreSQL.

## What Is Implemented

- FastAPI app with versioned API prefix: `/api/v1`
- JWT authentication:
  - Access token in response body
  - Refresh token in `HttpOnly` cookie
- Refresh token rotation with one-time use semantics via Redis `GETDEL`
- Password hashing with Argon2 (Passlib)
- Async SQLAlchemy + asyncpg
- Alembic migration setup
- Centralized exception handling
- Basic rate limiting middleware (SlowAPI)
- DFS metadata schema: files/folders (`fs_entries`), `chunks`, `chunk_replicas`, `storage_nodes`
- DFS upload flow with chunking on master and replication to storage nodes
- Replication quorum checks (`DFS_WRITE_QUORUM`)
- Download manifest with signed chunk URLs
- Storage node app with:
  - `GET /health`
  - `POST /chunks/{chunk_id}` (internal token protected)
  - `GET /chunks/{chunk_id}` (signed URL protected)
  - `DELETE /chunks/{chunk_id}` (internal token protected)

## Tech Stack

- Python
- FastAPI
- SQLAlchemy (async)
- PostgreSQL (asyncpg)
- Redis
- Alembic
- PyJWT
- Passlib (argon2)
- Pydantic Settings

## Project Structure

```text
.
|- alembic/
|  |- env.py
|  |- versions/
|- app/
|  |- main.py
|  |- lifespan.py
|  |- api/
|  |  |- dependencies/
|  |  |- middlewares/
|  |  |- v1/endpoints/
|  |- core/
|  |- crud/
|  |- db/
|  |- exceptions/
|  |- models/
|  |- schemas/
|  |- services/
|  |- utils/
|- storage_app/
|  |- main.py
|  |- config.py
|- shared/
|  |- security.py
|  |- constants.py
|  |- contracts/
|- alembic.ini
|- requirements.txt
|- .env.template
```

## Authentication Flow

1. Register a user (`POST /api/v1/register`)
2. Login (`POST /api/v1/login`)
3. Receive:
   - `access_token` in JSON response
   - `refresh_token` in secure `HttpOnly` cookie
4. Use access token for protected endpoints (Bearer auth)
5. Refresh access token (`POST /api/v1/refresh`) using refresh cookie
6. Logout (`POST /api/v1/logout`) revokes refresh token in Redis and clears cookie

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/register` | No | Register new user |
| POST | `/api/v1/login` | No | Login with username/password form |
| POST | `/api/v1/refresh` | No | Rotate refresh token and issue new access token |
| POST | `/api/v1/logout` | No | Revoke current refresh token and clear cookie |
| GET | `/api/v1/about_me` | Bearer | Get current authenticated user |
| POST | `/api/v1/dfs/nodes` | Bearer | Register storage node in master metadata |
| GET | `/api/v1/dfs/nodes` | Bearer | List storage nodes |
| POST | `/api/v1/dfs/nodes/{node_id}/heartbeat` | Bearer | Update node heartbeat and free space |
| POST | `/api/v1/dfs/directories` | Bearer | Create directory |
| GET | `/api/v1/dfs/entries` | Bearer | List directory entries |
| POST | `/api/v1/dfs/files/upload` | Bearer | Upload file to DFS (master chunks + replicates) |
| GET | `/api/v1/dfs/files/{file_id}/manifest` | Bearer | Get signed download manifest |
| DELETE | `/api/v1/dfs/files/{file_id}` | Bearer | Delete file and chunk replicas |
| GET | `/api/v1/dfs/chunks/{chunk_id}` | Signed URL | Stream local chunk via master |

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL
- Redis

### 2. Create and activate virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
. .\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create `.env` from template:

```bash
cp .env.template .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.template .env
```

Set the required variables:

| Variable | Required | Notes |
|---|---|---|
| `DEBUG` | No | `true` or `false` |
| `DATABASE_URL` | Yes | Must start with `postgresql+asyncpg://` or `postgres+asyncpg://` |
| `REDIS_URL` | Yes | Must start with `redis://` or `rediss://` |
| `ACCESS_SECRET` | Yes | Min length: 32 |
| `REFRESH_SECRET` | Yes | Min length: 32 |
| `ACCESS_TOKEN_EXPIRE_M` | No | Default: `15` |
| `REFRESH_TOKEN_EXPIRE_M` | No | Default: `43200` |
| `COOKIE_SECURE` | No | Default: `true` |
| `COOKIE_SAMESITE` | No | One of `lax`, `strict`, `none` |
| `DFS_MASTER_PUBLIC_BASE_URL` | No | Base URL used for local chunk links in manifest |
| `DFS_CHUNK_SIZE_BYTES` | No | Default: `4194304` (4 MiB) |
| `DFS_MANIFEST_URL_TTL_S` | No | Signed chunk URL TTL, default `300` |
| `DFS_LOCAL_CHUNKS_DIR` | No | Local chunk storage path for master-local node |
| `DFS_LOCAL_NODE_NAME` | No | Name of built-in local storage node |
| `DFS_REPLICATION_FACTOR` | No | Number of target nodes per chunk |
| `DFS_WRITE_QUORUM` | No | Required successful replicas per chunk |
| `DFS_STORAGE_TIMEOUT_S` | No | Timeout for master -> storage HTTP calls |
| `DFS_CHUNK_URL_SECRET` | Yes | Shared with storage app, min length 32 |
| `DFS_INTERNAL_TOKEN` | Yes | Shared internal token, min length 32 |
| `STORAGE_NODE_NAME` | No | Storage app node name |
| `STORAGE_CHUNKS_DIR` | No | Local chunk dir used by storage app |

Important for local HTTP development:

- If you test without HTTPS, set `COOKIE_SECURE=false`
- Otherwise browser/client may not send refresh cookie, and `/refresh`/`/logout` can fail with `401`

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start master app

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start storage app (same repository)

```bash
uvicorn storage_app.main:app --reload --host 0.0.0.0 --port 8010
```

Then register this node in master metadata:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/dfs/nodes" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"storage-node-1","base_url":"http://127.0.0.1:8010"}'
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Request Examples

### Register

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","email":"john@example.com","password":"StrongPass123"}'
```

### Login (stores refresh cookie into file)

```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -c cookies.txt \
  -d "username=john_doe&password=StrongPass123"
```

### Refresh

```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/refresh" \
  -b cookies.txt \
  -c cookies.txt
```

### About Me

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/about_me" \
  -H "Authorization: Bearer <access_token>"
```

### Logout

```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/logout" \
  -b cookies.txt \
  -c cookies.txt
```

## Error Model

Application-specific errors use this shape:

```json
{"detail": "..."}
```

Common statuses:

- `201` Created (register)
- `200` OK (login, refresh, logout, about_me)
- `401` Unauthorized (invalid credentials/token)
- `404` Not Found (user not found)
- `409` Conflict (user already exists)
- `429` Too Many Requests (rate limit exceeded)

## Migrations

Create migration:

```bash
alembic revision --autogenerate -m "describe change"
```

Upgrade DB:

```bash
alembic upgrade head
```

Downgrade one revision:

```bash
alembic downgrade -1
```

## Current Limitations

- No background repair/rebalance workers yet
- No direct browser-to-storage upload yet (upload still goes through master)
- No automated test suite in repository yet