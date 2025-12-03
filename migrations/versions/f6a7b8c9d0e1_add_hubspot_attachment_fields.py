"""Add HubSpot attachment fields to generated_documents

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar campos do HubSpot ao generated_documents
    op.add_column(
        'generated_documents',
        sa.Column('hubspot_file_id', sa.String(255), nullable=True)
    )
    op.add_column(
        'generated_documents',
        sa.Column('hubspot_file_url', sa.String(500), nullable=True)
    )
    op.add_column(
        'generated_documents',
        sa.Column('hubspot_attachment_id', sa.String(255), nullable=True)
    )


def downgrade():
    # Remover campos do HubSpot
    op.drop_column('generated_documents', 'hubspot_attachment_id')
    op.drop_column('generated_documents', 'hubspot_file_url')
    op.drop_column('generated_documents', 'hubspot_file_id')

