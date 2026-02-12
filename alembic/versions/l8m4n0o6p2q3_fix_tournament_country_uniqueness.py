"""fix_tournament_country_uniqueness

Revision ID: l8m4n0o6p2q3
Revises: k7l3m9n5o1p2
Create Date: 2026-02-12 10:00:00.000000

Fixes tournament data integrity (BUG-016):
1. Sets NULL countries to 'Unknown'
2. Handles duplicates by appending tournament ID suffix
3. Makes country column NOT NULL
4. Adds composite unique constraint (sport_id, name, country)

This migration is safe to run multiple times - it checks for existing
duplicates before attempting to create the constraint.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'l8m4n0o6p2q3'
down_revision: Union[str, Sequence[str], None] = 'k7l3m9n5o1p2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix tournament country data and add uniqueness constraint.

    Steps:
    1. Set NULL countries to 'Unknown' (data cleanup)
    2. Find and resolve duplicates (same sport_id, name, country)
    3. Alter country column to NOT NULL with default
    4. Add composite unique constraint
    """
    conn = op.get_bind()

    # Step 1: Set NULL countries to 'Unknown'
    conn.execute(text("""
        UPDATE tournaments
        SET country = 'Unknown'
        WHERE country IS NULL
    """))

    # Step 2: Handle duplicates - append ID suffix to make unique
    # Find duplicates first
    duplicates = conn.execute(text("""
        SELECT sport_id, name, country, array_agg(id ORDER BY id) as ids
        FROM tournaments
        GROUP BY sport_id, name, country
        HAVING COUNT(*) > 1
    """)).fetchall()

    # For each duplicate group, update all but the first to have unique country
    for dup in duplicates:
        ids = dup.ids
        # Keep the first one as-is, update the rest
        for tournament_id in ids[1:]:
            conn.execute(text("""
                UPDATE tournaments
                SET country = country || ' (' || :tid || ')'
                WHERE id = :tid
            """), {"tid": tournament_id})

    # Step 3: Make country NOT NULL with default
    op.alter_column(
        'tournaments',
        'country',
        existing_type=sa.String(100),
        nullable=False,
        server_default='Unknown'
    )

    # Step 4: Add composite unique constraint
    op.create_unique_constraint(
        'uq_tournaments_sport_name_country',
        'tournaments',
        ['sport_id', 'name', 'country']
    )


def downgrade() -> None:
    """Remove constraint and make country nullable again.

    Note: Does not undo data changes (country values remain as modified).
    """
    # Drop unique constraint
    op.drop_constraint(
        'uq_tournaments_sport_name_country',
        'tournaments',
        type_='unique'
    )

    # Make country nullable again
    op.alter_column(
        'tournaments',
        'country',
        existing_type=sa.String(100),
        nullable=True,
        server_default=None
    )
