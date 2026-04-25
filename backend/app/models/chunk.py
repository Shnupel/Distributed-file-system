from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


if TYPE_CHECKING:
    from .chunk_replica import ChunkReplica
    from .fs_entry import FileSystemEntry


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("file_id", "chunk_index", name="uq_chunks_file_id_chunk_index"),
    )

    file_id: Mapped[int] = mapped_column(
        ForeignKey("fs_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    file: Mapped["FileSystemEntry"] = relationship(back_populates="chunks")
    replicas: Mapped[list["ChunkReplica"]] = relationship(
        back_populates="chunk",
        cascade="all, delete-orphan",
    )