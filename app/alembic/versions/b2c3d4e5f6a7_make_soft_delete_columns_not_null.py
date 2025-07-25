"""make soft delete columns not null on users and currency

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2024-07-24

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'aabbccddeeff'
branch_labels = None
depends_on = None

def upgrade():
    op.execute('UPDATE currency SET deleted = FALSE WHERE deleted IS NULL')
    op.execute('UPDATE users SET deleted = FALSE WHERE deleted IS NULL')
    op.alter_column('currency', 'deleted', nullable=False)
    op.alter_column('users', 'deleted', nullable=False)
    op.alter_column('currency', 'deleted', server_default=None)
    op.alter_column('users', 'deleted', server_default=None)

def downgrade():
    op.alter_column('currency', 'deleted', nullable=True)
    op.alter_column('users', 'deleted', nullable=True)