"""Add isAnswer

Revision ID: 006f21a18554
Revises: 5f9469b957c8
Create Date: 2024-10-06 10:41:18.195151

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006f21a18554"
down_revision: Union[str, None] = "5f9469b957c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "conversation_message",
        sa.Column(
            "isAnswer", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("conversation_message", "isAnswer")
    # ### end Alembic commands ###