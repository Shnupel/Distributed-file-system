import asyncio
import contextlib

import httpx
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from shutil import disk_usage

from shared import (
    INTERNAL_TOKEN_HEADER,
    is_chunk_signature_valid,
    is_internal_token_valid,
)
from shared.contracts import ChunkUploadResponse, StorageHealthResponse

from .config import StorageSettings, get_storage_settings


app = FastAPI(title="DFS Storage Node", version="1.0.0")


def _chunks_dir(settings: StorageSettings) -> Path:
    path = Path(settings.storage_chunks_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _node_payload(settings: StorageSettings) -> dict[str, str]:
    return {
        "name": settings.storage_node_name,
        "base_url": settings.storage_public_base_url,
    }


async def _storage_usage(settings: StorageSettings) -> tuple[int, int]:
    chunks_path = _chunks_dir(settings)
    usage = await asyncio.to_thread(disk_usage, chunks_path)
    return usage.total, usage.free


async def _resolve_node_id(client: httpx.AsyncClient, settings: StorageSettings) -> int | None:
    total_space, free_space = await _storage_usage(settings)
    response = await client.post(
        f"{settings.dfs_master_base_url}/api/v1/dfs/nodes",
        json={
            **_node_payload(settings),
            "total_space": total_space,
            "free_space": free_space,
        },
        headers={INTERNAL_TOKEN_HEADER: settings.dfs_internal_token},
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("id")


async def _send_heartbeat(client: httpx.AsyncClient, settings: StorageSettings, node_id: int) -> None:
    total_space, free_space = await _storage_usage(settings)
    response = await client.post(
        f"{settings.dfs_master_base_url}/api/v1/dfs/nodes/{node_id}/heartbeat",
        json={
            "total_space": total_space,
            "free_space": free_space,
        },
        headers={INTERNAL_TOKEN_HEADER: settings.dfs_internal_token},
    )
    response.raise_for_status()


async def _heartbeat_loop(settings: StorageSettings) -> None:
    timeout = httpx.Timeout(10.0)
    node_id: int | None = None
    logger = logging.getLogger(__name__)

    async with httpx.AsyncClient(timeout=timeout) as client:
        while True:
            try:
                if node_id is None:
                    node_id = await _resolve_node_id(client, settings)
                if node_id is not None:
                    await _send_heartbeat(client, settings, node_id)
            except Exception as exc:
                logger.warning("Failed to register heartbeat with master: %s", exc)
                node_id = None

            await asyncio.sleep(settings.dfs_heartbeat_interval_s)


@app.on_event("startup")
async def startup() -> None:
    settings = get_storage_settings()
    app.state.heartbeat_task = asyncio.create_task(_heartbeat_loop(settings))


@app.on_event("shutdown")
async def shutdown() -> None:
    heartbeat_task: asyncio.Task | None = getattr(app.state, "heartbeat_task", None)
    if heartbeat_task is not None:
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task


@app.get("/health", response_model=StorageHealthResponse)
async def health(settings: StorageSettings = Depends(get_storage_settings)):
    chunks_dir = _chunks_dir(settings)
    usage = disk_usage(chunks_dir)

    return StorageHealthResponse(
        node_name=settings.storage_node_name,
        total_space=usage.total,
        free_space=usage.free,
        timestamp=datetime.now(timezone.utc),
    )


@app.post("/chunks/{chunk_id}", response_model=ChunkUploadResponse)
async def upload_chunk(
    chunk_id: int,
    payload: bytes = Body(...),
    sha256: str = Query(..., min_length=64, max_length=64),
    internal_token: str | None = Header(default=None, alias=INTERNAL_TOKEN_HEADER),
    settings: StorageSettings = Depends(get_storage_settings),
):
    if not is_internal_token_valid(internal_token, settings.dfs_internal_token):
        raise HTTPException(status_code=401, detail="Invalid internal token")

    chunk_hash = hashlib.sha256(payload).hexdigest()
    if chunk_hash != sha256:
        raise HTTPException(status_code=400, detail="Chunk checksum mismatch")

    chunks_dir = _chunks_dir(settings)
    path = chunks_dir / f"{chunk_id}.bin"
    path.write_bytes(payload)

    return ChunkUploadResponse(
        chunk_id=chunk_id,
        size=len(payload),
        sha256=chunk_hash,
        stored=True,
    )


@app.get("/chunks/{chunk_id}")
async def download_chunk(
    chunk_id: int,
    exp: int = Query(..., ge=1),
    sig: str = Query(..., min_length=64, max_length=64),
    settings: StorageSettings = Depends(get_storage_settings),
):
    if not is_chunk_signature_valid(chunk_id, exp, sig, settings.dfs_chunk_url_secret):
        raise HTTPException(status_code=403, detail="Chunk URL signature is invalid or expired")

    chunks_dir = _chunks_dir(settings)
    path = chunks_dir / f"{chunk_id}.bin"
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Chunk not found")

    return FileResponse(path=path, media_type="application/octet-stream")


@app.delete("/chunks/{chunk_id}", status_code=204)
async def delete_chunk(
    chunk_id: int,
    internal_token: str | None = Header(default=None, alias=INTERNAL_TOKEN_HEADER),
    settings: StorageSettings = Depends(get_storage_settings),
):
    if not is_internal_token_valid(internal_token, settings.dfs_internal_token):
        raise HTTPException(status_code=401, detail="Invalid internal token")

    chunks_dir = _chunks_dir(settings)
    path = chunks_dir / f"{chunk_id}.bin"
    if path.exists() and path.is_file():
        path.unlink()
