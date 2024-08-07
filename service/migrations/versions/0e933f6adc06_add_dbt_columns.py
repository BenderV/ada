"""Add dbt columns

Revision ID: 0e933f6adc06
Revises: 961090ec9af1
Create Date: 2024-05-18 08:49:52.924672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0e933f6adc06'
down_revision: Union[str, None] = '961090ec9af1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('database', sa.Column('dbt_catalog', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('database', sa.Column('dbt_manifest', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('database', 'dbt_manifest')
    op.drop_column('database', 'dbt_catalog')
    # ### end Alembic commands ###
