from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


if TYPE_CHECKING:
    from .chunk_replica import ChunkReplica


class StorageNode(Base):
    __tablename__ = "storage_nodes"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    internal_base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    is_local: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    total_space: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    free_space: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    replicas: Mapped[list["ChunkReplica"]] = relationship(back_populates="node")