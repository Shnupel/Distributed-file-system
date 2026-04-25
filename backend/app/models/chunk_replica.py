from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


if TYPE_CHECKING:
    from .chunk import Chunk
    from .storage_node import StorageNode


class ChunkReplica(Base):
    __tablename__ = "chunk_replicas"
    __table_args__ = (
        UniqueConstraint("chunk_id", "node_id", name="uq_chunk_replicas_chunk_id_node_id"),
    )

    chunk_id: Mapped[int] = mapped_column(
        ForeignKey("chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_id: Mapped[int] = mapped_column(
        ForeignKey("storage_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="stored",
        server_default="stored",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    chunk: Mapped["Chunk"] = relationship(back_populates="replicas")
    node: Mapped["StorageNode"] = relationship(back_populates="replicas")