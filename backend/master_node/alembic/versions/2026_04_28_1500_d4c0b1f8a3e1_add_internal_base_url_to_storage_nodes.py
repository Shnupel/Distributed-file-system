"""add internal base url to storage nodes

Revision ID: d4c0b1f8a3e1
Revises: 2f59c9db2c9f
Create Date: 2026-04-28 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4c0b1f8a3e1"
down_revision: Union[str, Sequence[str], None] = "2f59c9db2c9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "storage_nodes",
        sa.Column("internal_base_url", sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("storage_nodes", "internal_base_url")
