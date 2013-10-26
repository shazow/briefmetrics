"""User payment

Revision ID: b8252809387
Revises: 2411b28d8811
Create Date: 2013-10-26 11:27:28.410463

"""

# revision identifiers, used by Alembic.
revision = 'b8252809387'
down_revision = '2411b28d8811'

from alembic import op
import sqlalchemy as sa



def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('report', u'num_sent')
    op.add_column('user', sa.Column('num_remaining', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('plan', sa.String(), nullable=True, default='tester'))
    op.add_column('user', sa.Column('stripe_customer_id', sa.String(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'stripe_customer_id')
    op.drop_column('user', 'plan')
    op.drop_column('user', 'num_remaining')
    op.add_column('report', sa.Column(u'num_sent', sa.INTEGER(), nullable=True))
    ### end Alembic commands ###
