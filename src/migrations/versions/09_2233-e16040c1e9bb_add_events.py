"""add events

Revision ID: e16040c1e9bb
Revises: 75f090dc3cd5
Create Date: 2026-04-09 22:33:21.410932

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e16040c1e9bb"
down_revision: Union[str, Sequence[str], None] = "75f090dc3cd5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("descriptions", sa.String(length=300), nullable=True),
        sa.Column("address", sa.String(length=200), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title"),
    )
    op.create_table(
        "users_events",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "event_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("users_events")
    op.drop_table("events")
