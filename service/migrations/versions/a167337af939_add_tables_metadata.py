"""add tables_metadata

Revision ID: a167337af939
Revises: bb9fe32018b6
Create Date: 2023-09-08 19:00:54.438146

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a167337af939'
down_revision: Union[str, None] = 'bb9fe32018b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('database', sa.Column('tables_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('database', 'tables_metadata')
    # ### end Alembic commands ###