"""Add account.service

Revision ID: 4c2d27b91e10
Revises: 1b5395ed8b5c
Create Date: 2014-06-06 00:18:46.683763

"""

# revision identifiers, used by Alembic.
revision = '4c2d27b91e10'
down_revision = '1b5395ed8b5c'

from alembic import op
import sqlalchemy as sa



def upgrade():
    op.add_column('account', sa.Column('service', sa.Integer(), nullable=True, default=1))


def downgrade():
    op.drop_column('account', 'type')
