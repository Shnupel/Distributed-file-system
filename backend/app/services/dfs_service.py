import asyncio
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import httpx
from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import API_V1_PREFIX, Settings
from app.crud import DFSCRUD
from app.exceptions import (
    ChunkNotFound,
    ChunkUrlInvalid,
    FileNotReady,
    FileUploadFailed,
    FsEntryAlreadyExists,
    FsEntryIsDirectory,
    FsEntryNotFound,
    FsParentInvalid,
    ReplicationQuorumNotReached,
    StorageNodeUnavailable,
)
from app.models import Chunk, ChunkReplica, FileSystemEntry, StorageNode
from app.schemas import (
    ChunkManifestRead,
    ChunkReplicaURLRead,
    DownloadManifestRead,
    FileDeleteRead,
    FileUploadRead,
    StorageNodeCreate,
    StorageNodeHeartbeat,
)
from shared import INTERNAL_TOKEN_HEADER, build_chunk_signature, is_chunk_signature_valid


@dataclass
class ReplicaCleanupTarget:
    chunk_id: int
    is_local: bool
    storage_path: str
    base_url: str | None


class DFSService:
    def __init__(self, dfs_crud: DFSCRUD, settings: Settings):
        self.dfs_crud = dfs_crud
        self.settings = settings
        self.local_chunks_dir = Path(settings.dfs_local_chunks_dir)
        self.master_public_base_url = settings.dfs_master_public_base_url.rstrip("/")

    async def _ensure_local_node(self, session: AsyncSession) -> StorageNode:
        node = await self.dfs_crud.get_local_storage_node(session)
        if node is not None:
            return node

        node = StorageNode(
            name=self.settings.dfs_local_node_name,
            base_url=self.master_public_base_url,
            is_active=True,
            is_local=True,
            last_heartbeat=datetime.now(timezone.utc),
        )
        await self.dfs_crud.create_storage_node(session, node)
        await session.commit()
        await session.refresh(node)
        return node

    async def _validate_parent(
        self,
        session: AsyncSession,
        owner_id: int,
        parent_id: int | None,
    ) -> FileSystemEntry | None:
        if parent_id is None:
            return None

        parent = await self.dfs_crud.get_entry_for_owner(session, parent_id, owner_id)
        if parent is None:
            raise FsEntryNotFound("Parent entry not found")

        if not parent.is_dir:
            raise FsParentInvalid("Parent entry must be a directory")

        return parent

    @staticmethod
    def _validate_entry_name(name: str) -> None:
        clean = name.strip()
        if not clean:
            raise FsParentInvalid("Entry name cannot be empty")
        if "/" in clean or "\\" in clean:
            raise FsParentInvalid("Entry name must not contain path separators")

    def _target_nodes_for_chunk(self, nodes: Sequence[StorageNode], chunk_index: int) -> list[StorageNode]:
        if not nodes:
            raise StorageNodeUnavailable()

        replication_factor = min(len(nodes), self.settings.dfs_replication_factor)
        if replication_factor <= 0:
            raise StorageNodeUnavailable()

        shift = chunk_index % len(nodes)
        rotated = list(nodes[shift:]) + list(nodes[:shift])
        return rotated[:replication_factor]

    async def _store_chunk_locally(self, chunk_id: int, payload: bytes) -> str:
        await asyncio.to_thread(self.local_chunks_dir.mkdir, parents=True, exist_ok=True)
        chunk_path = self.local_chunks_dir / f"{chunk_id}.bin"
        await asyncio.to_thread(chunk_path.write_bytes, payload)
        return str(chunk_path)

    async def _push_chunk_to_remote_node(
        self,
        client: httpx.AsyncClient,
        node: StorageNode,
        chunk_id: int,
        payload: bytes,
        chunk_hash: str,
    ) -> tuple[bool, str, str | None]:
        if not node.base_url:
            return False, "", "Node base_url is empty"

        url = f"{node.base_url.rstrip('/')}/chunks/{chunk_id}"
        headers = {INTERNAL_TOKEN_HEADER: self.settings.dfs_internal_token}

        try:
            response = await client.post(
                url,
                content=payload,
                params={"sha256": chunk_hash},
                headers=headers,
            )
            if response.is_success:
                return True, url, None
            return False, url, f"HTTP {response.status_code}"
        except httpx.HTTPError as exc:
            return False, url, str(exc)

    async def _cleanup_uploaded_replicas(self, replicas: Sequence[ReplicaCleanupTarget]) -> None:
        if not replicas:
            return

        timeout = httpx.Timeout(self.settings.dfs_storage_timeout_s)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for replica in replicas:
                if replica.is_local:
                    path = Path(replica.storage_path)
                    try:
                        await asyncio.to_thread(path.unlink)
                    except FileNotFoundError:
                        continue
                    continue

                if not replica.base_url:
                    continue

                try:
                    await client.delete(
                        f"{replica.base_url.rstrip('/')}/chunks/{replica.chunk_id}",
                        headers={INTERNAL_TOKEN_HEADER: self.settings.dfs_internal_token},
                    )
                except httpx.HTTPError:
                    continue

    async def _mark_entry_failed(self, session: AsyncSession, owner_id: int, file_id: int) -> None:
        entry = await self.dfs_crud.get_entry_for_owner(session, file_id, owner_id)
        if entry is None:
            return

        entry.status = "failed"
        await session.commit()

    async def register_storage_node(
        self,
        session: AsyncSession,
        payload: StorageNodeCreate,
    ) -> StorageNode:
        existing = await self.dfs_crud.get_storage_node_by_name(session, payload.name)
        if existing is not None:
            raise FsEntryAlreadyExists("Storage node with this name already exists")

        node = StorageNode(
            name=payload.name,
            base_url=payload.base_url,
            total_space=payload.total_space,
            free_space=payload.free_space,
            is_active=True,
            is_local=False,
            last_heartbeat=datetime.now(timezone.utc),
        )

        try:
            await self.dfs_crud.create_storage_node(session, node)
            await session.commit()
            await session.refresh(node)
        except IntegrityError as exc:
            await session.rollback()
            raise FsEntryAlreadyExists("Storage node with this name already exists") from exc

        return node

    async def heartbeat_storage_node(
        self,
        session: AsyncSession,
        node_id: int,
        payload: StorageNodeHeartbeat,
    ) -> StorageNode:
        node = await self.dfs_crud.get_storage_node_by_id(session, node_id)
        if node is None:
            raise FsEntryNotFound("Storage node not found")

        node.total_space = payload.total_space
        node.free_space = payload.free_space
        node.last_heartbeat = datetime.now(timezone.utc)
        node.is_active = True

        await session.commit()
        await session.refresh(node)
        return node

    async def list_storage_nodes(self, session: AsyncSession) -> list[StorageNode]:
        rows = await self.dfs_crud.list_storage_nodes(session)
        return list(rows)

    async def create_directory(
        self,
        session: AsyncSession,
        owner_id: int,
        name: str,
        parent_id: int | None,
    ) -> FileSystemEntry:
        self._validate_entry_name(name)
        await self._validate_parent(session, owner_id, parent_id)

        duplicate = await self.dfs_crud.get_entry_by_name(session, owner_id, parent_id, name)
        if duplicate is not None:
            raise FsEntryAlreadyExists()

        entry = FileSystemEntry(
            owner_id=owner_id,
            parent_id=parent_id,
            name=name.strip(),
            is_dir=True,
            size=0,
            status="ready",
        )

        try:
            await self.dfs_crud.create_entry(session, entry)
            await session.commit()
            await session.refresh(entry)
        except IntegrityError as exc:
            await session.rollback()
            raise FsEntryAlreadyExists() from exc

        return entry

    async def list_entries(
        self,
        session: AsyncSession,
        owner_id: int,
        parent_id: int | None,
    ) -> list[FileSystemEntry]:
        await self._validate_parent(session, owner_id, parent_id)
        entries = await self.dfs_crud.list_entries(session, owner_id, parent_id)
        return list(entries)

    async def upload_file(
        self,
        session: AsyncSession,
        owner_id: int,
        parent_id: int | None,
        upload: UploadFile,
    ) -> FileUploadRead:
        filename = (upload.filename or "uploaded.bin").strip()
        filename = Path(filename).name
        self._validate_entry_name(filename)
        await self._validate_parent(session, owner_id, parent_id)

        duplicate = await self.dfs_crud.get_entry_by_name(session, owner_id, parent_id, filename)
        if duplicate is not None:
            raise FsEntryAlreadyExists()

        await self._ensure_local_node(session)
        active_nodes = list(await self.dfs_crud.list_active_storage_nodes(session))
        if not active_nodes:
            raise StorageNodeUnavailable()
        if len(active_nodes) < self.settings.dfs_write_quorum:
            raise StorageNodeUnavailable(
                f"Not enough active nodes for write quorum: {len(active_nodes)} < {self.settings.dfs_write_quorum}"
            )

        entry = FileSystemEntry(
            owner_id=owner_id,
            parent_id=parent_id,
            name=filename,
            is_dir=False,
            size=0,
            mime_type=upload.content_type,
            status="uploading",
        )

        await self.dfs_crud.create_entry(session, entry)
        await session.commit()
        await session.refresh(entry)

        cleanup_targets: list[ReplicaCleanupTarget] = []
        chunk_count = 0
        total_size = 0
        file_hasher = hashlib.sha256()

        timeout = httpx.Timeout(self.settings.dfs_storage_timeout_s)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                while True:
                    payload = await upload.read(self.settings.dfs_chunk_size_bytes)
                    if not payload:
                        break

                    file_hasher.update(payload)
                    total_size += len(payload)
                    chunk_hash = hashlib.sha256(payload).hexdigest()

                    chunk = Chunk(
                        file_id=entry.id,
                        chunk_index=chunk_count,
                        chunk_size=len(payload),
                        sha256=chunk_hash,
                    )
                    await self.dfs_crud.create_chunk(session, chunk)

                    targets = self._target_nodes_for_chunk(active_nodes, chunk_count)
                    write_quorum = min(max(1, self.settings.dfs_write_quorum), len(targets))
                    stored_count = 0

                    for node in targets:
                        stored = False
                        last_error: str | None = None
                        storage_path = ""

                        if node.is_local:
                            try:
                                storage_path = await self._store_chunk_locally(chunk.id, payload)
                                stored = True
                            except OSError as exc:
                                last_error = str(exc)
                        else:
                            stored, storage_path, last_error = await self._push_chunk_to_remote_node(
                                client,
                                node,
                                chunk.id,
                                payload,
                                chunk_hash,
                            )

                        replica = ChunkReplica(
                            chunk_id=chunk.id,
                            node_id=node.id,
                            storage_path=storage_path or f"{node.base_url or ''}/chunks/{chunk.id}",
                            status="stored" if stored else "failed",
                        )
                        await self.dfs_crud.create_replica(session, replica)

                        if stored:
                            stored_count += 1
                            cleanup_targets.append(
                                ReplicaCleanupTarget(
                                    chunk_id=chunk.id,
                                    is_local=node.is_local,
                                    storage_path=storage_path,
                                    base_url=node.base_url,
                                )
                            )
                        elif node.is_local and last_error:
                            raise FileUploadFailed(f"Local storage write failed: {last_error}")

                    if stored_count < write_quorum:
                        raise ReplicationQuorumNotReached(
                            f"Chunk {chunk_count} stored on {stored_count} replicas, quorum is {write_quorum}"
                        )

                    chunk_count += 1

            entry.size = total_size
            entry.file_sha256 = file_hasher.hexdigest()
            entry.status = "ready"

            await session.commit()
            await session.refresh(entry)
        except (ReplicationQuorumNotReached, StorageNodeUnavailable, FileUploadFailed):
            await session.rollback()
            await self._mark_entry_failed(session, owner_id, entry.id)
            await self._cleanup_uploaded_replicas(cleanup_targets)
            raise
        except Exception as exc:
            await session.rollback()
            await self._mark_entry_failed(session, owner_id, entry.id)
            await self._cleanup_uploaded_replicas(cleanup_targets)
            raise FileUploadFailed() from exc
        finally:
            await upload.close()

        return FileUploadRead(
            file_id=entry.id,
            file_name=entry.name,
            size=entry.size,
            chunks_count=chunk_count,
            file_sha256=entry.file_sha256 or "",
            status=entry.status,
        )

    async def get_download_manifest(
        self,
        session: AsyncSession,
        owner_id: int,
        file_id: int,
    ) -> DownloadManifestRead:
        entry = await self.dfs_crud.get_entry_for_owner(session, file_id, owner_id)
        if entry is None:
            raise FsEntryNotFound()
        if entry.is_dir:
            raise FsParentInvalid("Entry is a directory")
        if entry.status != "ready":
            raise FileNotReady()

        chunks = await self.dfs_crud.list_chunks_for_file(session, entry.id)

        expires_at = int(datetime.now(timezone.utc).timestamp()) + self.settings.dfs_manifest_url_ttl_s
        chunk_items: list[ChunkManifestRead] = []

        for chunk in chunks:
            signature = build_chunk_signature(chunk.id, expires_at, self.settings.dfs_chunk_url_secret)
            replica_items: list[ChunkReplicaURLRead] = []

            for replica in chunk.replicas:
                node = replica.node
                if node is None or not node.is_active or replica.status != "stored":
                    continue

                if node.is_local:
                    url = (
                        f"{self.master_public_base_url}{API_V1_PREFIX}/dfs/chunks/{chunk.id}"
                        f"?exp={expires_at}&sig={signature}"
                    )
                elif node.base_url:
                    base_url = node.base_url.rstrip("/")
                    url = f"{base_url}/chunks/{chunk.id}?exp={expires_at}&sig={signature}"
                else:
                    continue

                replica_items.append(
                    ChunkReplicaURLRead(
                        node_id=node.id,
                        node_name=node.name,
                        url=url,
                    )
                )

            chunk_items.append(
                ChunkManifestRead(
                    chunk_id=chunk.id,
                    index=chunk.chunk_index,
                    size=chunk.chunk_size,
                    sha256=chunk.sha256,
                    replicas=replica_items,
                )
            )

        return DownloadManifestRead(
            file_id=entry.id,
            file_name=entry.name,
            size=entry.size,
            file_sha256=entry.file_sha256 or "",
            expires_at_unix=expires_at,
            chunks=chunk_items,
        )

    async def resolve_local_chunk_path(
        self,
        session: AsyncSession,
        chunk_id: int,
        exp: int,
        sig: str,
    ) -> Path:
        if not is_chunk_signature_valid(chunk_id, exp, sig, self.settings.dfs_chunk_url_secret):
            raise ChunkUrlInvalid()

        replica = await self.dfs_crud.get_local_chunk_replica(session, chunk_id)
        if replica is None:
            raise ChunkNotFound()

        path = Path(replica.storage_path)
        if not path.exists() or not path.is_file():
            raise ChunkNotFound()

        return path

    async def delete_file(
        self,
        session: AsyncSession,
        owner_id: int,
        file_id: int,
    ) -> FileDeleteRead:
        entry = await self.dfs_crud.get_entry_for_owner(session, file_id, owner_id)
        if entry is None:
            raise FsEntryNotFound()
        if entry.is_dir:
            raise FsEntryIsDirectory()

        chunks = await self.dfs_crud.list_chunks_for_file(session, entry.id)
        cleanup_targets: list[ReplicaCleanupTarget] = []

        for chunk in chunks:
            for replica in chunk.replicas:
                node = replica.node
                if node is None or replica.status != "stored":
                    continue
                cleanup_targets.append(
                    ReplicaCleanupTarget(
                        chunk_id=chunk.id,
                        is_local=node.is_local,
                        storage_path=replica.storage_path,
                        base_url=node.base_url,
                    )
                )

        await self.dfs_crud.delete_entry(session, entry)
        await session.commit()

        await self._cleanup_uploaded_replicas(cleanup_targets)

        return FileDeleteRead(file_id=file_id, deleted=True)
