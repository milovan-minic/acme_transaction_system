"""Add soft delete columns as nullable with default False

Revision ID: aabbccddeeff
Revises: 845341e899eb
Create Date: 2025-07-25

"""
from alembic import op
import sqlalchemy as sa

revision = 'aabbccddeeff'
down_revision = '845341e899eb'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('currency', sa.Column('deleted', sa.Boolean(), nullable=True, server_default=sa.false()))
    op.add_column('users', sa.Column('deleted', sa.Boolean(), nullable=True, server_default=sa.false()))

def downgrade():
    op.drop_column('currency', 'deleted')
    op.drop_column('users', 'deleted') 