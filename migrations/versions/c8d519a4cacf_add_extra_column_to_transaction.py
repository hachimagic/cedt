"""Add extra column to Transaction

Revision ID: c8d519a4cacf
Revises: 
Create Date: 2025-03-10 23:43:55.232072

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8d519a4cacf'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.add_column(sa.Column('extra', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('line_text', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.drop_column('line_text')
        batch_op.drop_column('extra')

    # ### end Alembic commands ###
