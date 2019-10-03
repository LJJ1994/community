"""empty message

Revision ID: 57313f90880d
Revises: 15e154e2d769
Create Date: 2019-10-01 11:49:45.263100

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '57313f90880d'
down_revision = '15e154e2d769'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.Float(), nullable=True),
    sa.Column('payload_json', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['cm_user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_name'), 'notifications', ['name'], unique=False)
    op.create_index(op.f('ix_notifications_timestamp'), 'notifications', ['timestamp'], unique=False)
    op.drop_column('cm_user', 'followers_count')
    op.drop_column('cm_user', 'followed_count')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cm_user', sa.Column('followed_count', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.add_column('cm_user', sa.Column('followers_count', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.drop_index(op.f('ix_notifications_timestamp'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_name'), table_name='notifications')
    op.drop_table('notifications')
    # ### end Alembic commands ###
