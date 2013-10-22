"""Report.num_sent

Revision ID: 2411b28d8811
Revises: 0000
Create Date: 2013-10-22 23:53:09.861713

"""

# revision identifiers, used by Alembic.
revision = '2411b28d8811'
down_revision = '0000'

from alembic import op
import sqlalchemy as sa



def upgrade():
    op.add_column('report', sa.Column('num_sent', sa.Integer(), nullable=True, default=0))


def downgrade():
    op.drop_column('report', 'num_sent')
