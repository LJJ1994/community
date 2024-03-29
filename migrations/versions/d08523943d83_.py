"""empty message

Revision ID: d08523943d83
Revises: abe01f40bbd0
Create Date: 2019-09-26 21:22:03.373977

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd08523943d83'
down_revision = 'abe01f40bbd0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cm_user', sa.Column('followed_count', sa.Integer(), nullable=True))
    op.add_column('cm_user', sa.Column('followers_count', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('cm_user', 'followers_count')
    op.drop_column('cm_user', 'followed_count')
    # ### end Alembic commands ###
