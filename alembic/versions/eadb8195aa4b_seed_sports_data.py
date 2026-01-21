"""seed_sports_data

Revision ID: eadb8195aa4b
Revises: 845263fcf673
Create Date: 2026-01-21 10:50:18.297735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eadb8195aa4b'
down_revision: Union[str, Sequence[str], None] = '845263fcf673'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed sports table with reference data."""
    op.execute("""
        INSERT INTO sports (id, name, slug) VALUES
        (1, 'Football', 'football')
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    """Remove seeded sports data."""
    op.execute("DELETE FROM sports WHERE id = 1")
