"""Add microsoft fields to templates

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2025-01-20 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'k1l2m3n4o5p6'
down_revision = 'j0k1l2m3n4o5'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar campos Microsoft
    op.add_column('templates', sa.Column('microsoft_file_id', sa.String(255), nullable=True))
    op.add_column('templates', sa.Column('microsoft_file_type', sa.String(50), nullable=True))


def downgrade():
    # Remover campos Microsoft
    op.drop_column('templates', 'microsoft_file_type')
    op.drop_column('templates', 'microsoft_file_id')

