"""Add functionCallId

Revision ID: 4a0f8721eb48
Revises: 04c991f0d2ae
Create Date: 2024-09-07 15:25:16.927004

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4a0f8721eb48"
down_revision: Union[str, None] = "04c991f0d2ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "conversation_message", sa.Column("functionCallId", sa.String(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("conversation_message", "functionCallId")
    # ### end Alembic commands ###