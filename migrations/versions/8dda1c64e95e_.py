"""empty message

Revision ID: 8dda1c64e95e
Revises: ec41b9063ebc
Create Date: 2019-09-27 10:34:01.601401

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '8dda1c64e95e'
down_revision = 'ec41b9063ebc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('post_like',
    sa.Column('create_time', sa.DateTime(), nullable=True),
    sa.Column('update_time', sa.DateTime(), nullable=True),
    sa.Column('delete_time', sa.DateTime(), nullable=True),
    sa.Column('comment_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['comment_id'], ['post.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['cm_user.id'], ),
    sa.PrimaryKeyConstraint('comment_id', 'user_id')
    )
    op.add_column('cm_category', sa.Column('comment_count', sa.Integer(), nullable=True))
    op.drop_constraint('comment_like_ibfk_2', 'comment_like', type_='foreignkey')
    op.drop_column('comment_like', 'post_id')
    op.add_column('user_fans', sa.Column('create_time', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_fans', 'create_time')
    op.add_column('comment_like', sa.Column('post_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False))
    op.create_foreign_key('comment_like_ibfk_2', 'comment_like', 'post', ['post_id'], ['id'])
    op.drop_column('cm_category', 'comment_count')
    op.drop_table('post_like')
    # ### end Alembic commands ###
