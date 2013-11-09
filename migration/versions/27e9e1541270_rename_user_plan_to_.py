"""Rename user.plan to user.plan_id

Revision ID: 27e9e1541270
Revises: 2997080bf164
Create Date: 2013-11-09 09:40:25.465037

"""

# revision identifiers, used by Alembic.
revision = '27e9e1541270'
down_revision = '2997080bf164'

from alembic import op
import sqlalchemy as sa



def upgrade():
    op.alter_column('user', 'plan', name='plan_id')


def downgrade():
    op.alter_column('user', 'plan_id', name='plan')
