"""USer.config

Revision ID: 1b5395ed8b5c
Revises: 67f8ec8554
Create Date: 2014-03-19 10:56:29.391764

"""

# revision identifiers, used by Alembic.
revision = '1b5395ed8b5c'
down_revision = '67f8ec8554'

from alembic import op
import sqlalchemy as sa



def upgrade():
    op.add_column('user', sa.Column('config', sa.LargeBinary(), nullable=True))


def downgrade():
    op.drop_column('user', 'config')
