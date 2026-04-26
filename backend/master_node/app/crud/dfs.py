from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Chunk, ChunkReplica, FileSystemEntry, StorageNode


class DFSCRUD:
    async def create_storage_node(
        self,
        session: AsyncSession,
        node: StorageNode,
    ) -> StorageNode:
        session.add(node)
        await session.flush()
        return node

    async def get_storage_node_by_name(
        self,
        session: AsyncSession,
        name: str,
    ) -> StorageNode | None:
        stmt = select(StorageNode).where(StorageNode.name == name)
        return await session.scalar(stmt)

    async def get_storage_node_by_id(
        self,
        session: AsyncSession,
        node_id: int,
    ) -> StorageNode | None:
        stmt = select(StorageNode).where(StorageNode.id == node_id)
        return await session.scalar(stmt)

    async def get_local_storage_node(
        self,
        session: AsyncSession,
    ) -> StorageNode | None:
        stmt = select(StorageNode).where(StorageNode.is_local.is_(True))
        return await session.scalar(stmt)

    async def list_storage_nodes(self, session: AsyncSession) -> Sequence[StorageNode]:
        stmt = select(StorageNode).order_by(StorageNode.id)
        rows = await session.scalars(stmt)
        return rows.all()

    async def list_active_storage_nodes(self, session: AsyncSession) -> Sequence[StorageNode]:
        stmt = (
            select(StorageNode)
            .where(StorageNode.is_active.is_(True))
            .order_by(StorageNode.is_local.desc(), StorageNode.id)
        )
        rows = await session.scalars(stmt)
        return rows.all()

    async def create_entry(
        self,
        session: AsyncSession,
        entry: FileSystemEntry,
    ) -> FileSystemEntry:
        session.add(entry)
        await session.flush()
        return entry

    async def get_entry_for_owner(
        self,
        session: AsyncSession,
        entry_id: int,
        owner_id: int,
    ) -> FileSystemEntry | None:
        stmt = select(FileSystemEntry).where(
            FileSystemEntry.id == entry_id,
            FileSystemEntry.owner_id == owner_id,
        )
        return await session.scalar(stmt)

    async def get_entry_by_name(
        self,
        session: AsyncSession,
        owner_id: int,
        parent_id: int | None,
        name: str,
    ) -> FileSystemEntry | None:
        stmt = select(FileSystemEntry).where(
            FileSystemEntry.owner_id == owner_id,
            FileSystemEntry.name == name,
        )

        if parent_id is None:
            stmt = stmt.where(FileSystemEntry.parent_id.is_(None))
        else:
            stmt = stmt.where(FileSystemEntry.parent_id == parent_id)

        return await session.scalar(stmt)

    async def list_entries(
        self,
        session: AsyncSession,
        owner_id: int,
        parent_id: int | None,
    ) -> Sequence[FileSystemEntry]:
        stmt = select(FileSystemEntry).where(FileSystemEntry.owner_id == owner_id)

        if parent_id is None:
            stmt = stmt.where(FileSystemEntry.parent_id.is_(None))
        else:
            stmt = stmt.where(FileSystemEntry.parent_id == parent_id)

        stmt = stmt.order_by(FileSystemEntry.is_dir.desc(), FileSystemEntry.name, FileSystemEntry.id)
        rows = await session.scalars(stmt)
        return rows.all()

    async def delete_entry(self, session: AsyncSession, entry: FileSystemEntry) -> None:
        await session.delete(entry)

    async def create_chunk(
        self,
        session: AsyncSession,
        chunk: Chunk,
    ) -> Chunk:
        session.add(chunk)
        await session.flush()
        return chunk

    async def create_replica(
        self,
        session: AsyncSession,
        replica: ChunkReplica,
    ) -> ChunkReplica:
        session.add(replica)
        await session.flush()
        return replica

    async def list_chunks_for_file(
        self,
        session: AsyncSession,
        file_id: int,
    ) -> Sequence[Chunk]:
        stmt = (
            select(Chunk)
            .options(selectinload(Chunk.replicas).selectinload(ChunkReplica.node))
            .where(Chunk.file_id == file_id)
            .order_by(Chunk.chunk_index)
        )
        rows = await session.scalars(stmt)
        return rows.all()

    async def get_local_chunk_replica(
        self,
        session: AsyncSession,
        chunk_id: int,
    ) -> ChunkReplica | None:
        stmt = (
            select(ChunkReplica)
            .join(ChunkReplica.node)
            .where(
                ChunkReplica.chunk_id == chunk_id,
                ChunkReplica.status == "stored",
                StorageNode.is_local.is_(True),
                StorageNode.is_active.is_(True),
            )
        )
        return await session.scalar(stmt)