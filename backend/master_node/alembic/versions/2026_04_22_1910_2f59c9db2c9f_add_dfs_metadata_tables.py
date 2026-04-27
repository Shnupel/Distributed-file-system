"""add dfs metadata tables

Revision ID: 2f59c9db2c9f
Revises: a67f0fdc19e2
Create Date: 2026-04-22 19:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f59c9db2c9f"
down_revision: Union[str, Sequence[str], None] = "a67f0fdc19e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "storage_nodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "is_local",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("total_space", sa.BigInteger(), nullable=True),
        sa.Column("free_space", sa.BigInteger(), nullable=True),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_storage_nodes")),
        sa.UniqueConstraint("name", name=op.f("uq_storage_nodes_name")),
    )

    op.create_table(
        "fs_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "is_dir",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "size",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("file_sha256", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="ready",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_fs_entries_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["fs_entries.id"],
            name=op.f("fk_fs_entries_parent_id_fs_entries"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fs_entries")),
        sa.UniqueConstraint(
            "owner_id",
            "parent_id",
            "name",
            name=op.f("uq_fs_entries_owner_parent_name"),
        ),
    )
    op.create_index(op.f("ix_fs_entries_owner_id"), "fs_entries", ["owner_id"], unique=False)
    op.create_index(op.f("ix_fs_entries_parent_id"), "fs_entries", ["parent_id"], unique=False)

    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["fs_entries.id"],
            name=op.f("fk_chunks_file_id_fs_entries"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chunks")),
        sa.UniqueConstraint("file_id", "chunk_index", name=op.f("uq_chunks_file_id_chunk_index")),
    )
    op.create_index(op.f("ix_chunks_file_id"), "chunks", ["file_id"], unique=False)

    op.create_table(
        "chunk_replicas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("node_id", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="stored",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["chunks.id"],
            name=op.f("fk_chunk_replicas_chunk_id_chunks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["node_id"],
            ["storage_nodes.id"],
            name=op.f("fk_chunk_replicas_node_id_storage_nodes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chunk_replicas")),
        sa.UniqueConstraint("chunk_id", "node_id", name=op.f("uq_chunk_replicas_chunk_id_node_id")),
    )
    op.create_index(op.f("ix_chunk_replicas_chunk_id"), "chunk_replicas", ["chunk_id"], unique=False)
    op.create_index(op.f("ix_chunk_replicas_node_id"), "chunk_replicas", ["node_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_chunk_replicas_node_id"), table_name="chunk_replicas")
    op.drop_index(op.f("ix_chunk_replicas_chunk_id"), table_name="chunk_replicas")
    op.drop_table("chunk_replicas")

    op.drop_index(op.f("ix_chunks_file_id"), table_name="chunks")
    op.drop_table("chunks")

    op.drop_index(op.f("ix_fs_entries_parent_id"), table_name="fs_entries")
    op.drop_index(op.f("ix_fs_entries_owner_id"), table_name="fs_entries")
    op.drop_table("fs_entries")

    op.drop_table("storage_nodes")