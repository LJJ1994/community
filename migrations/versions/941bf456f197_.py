"""empty message

Revision ID: 941bf456f197
Revises: c013ec43aee6
Create Date: 2019-10-01 12:01:03.128852

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '941bf456f197'
down_revision = 'c013ec43aee6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post_like', sa.Column('post_id', sa.Integer(), nullable=False))
    op.drop_constraint('post_like_ibfk_1', 'post_like', type_='foreignkey')
    op.create_foreign_key(None, 'post_like', 'post', ['post_id'], ['id'])
    op.drop_column('post_like', 'comment_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post_like', sa.Column('comment_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'post_like', type_='foreignkey')
    op.create_foreign_key('post_like_ibfk_1', 'post_like', 'post', ['comment_id'], ['id'])
    op.drop_column('post_like', 'post_id')
    # ### end Alembic commands ###
