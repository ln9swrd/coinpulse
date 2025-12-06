"""Current schema snapshot

Revision ID: b68429ce9c72
Revises:
Create Date: 2025-11-30 01:38:07.170983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b68429ce9c72'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Initial migration - marks current database state.

    This migration does not make any changes.
    It simply records the current schema as the baseline.

    To use: alembic stamp head
    """
    # No operations - current database state is the baseline
    pass


def downgrade() -> None:
    """
    Downgrade not supported for initial migration.
    """
    # Cannot downgrade from initial state
    pass
