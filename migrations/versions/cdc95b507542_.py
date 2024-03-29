"""empty message

Revision ID: cdc95b507542
Revises: 74df2f932009
Create Date: 2019-09-24 14:21:40.711487

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cdc95b507542'
down_revision = '74df2f932009'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('nick_name', table_name='cm_user')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('nick_name', 'cm_user', ['nick_name'], unique=True)
    # ### end Alembic commands ###
