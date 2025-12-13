"""Add webhook_token to workflow_nodes

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2025-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'j0k1l2m3n4o5'
down_revision = 'i9j0k1l2m3n4'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar coluna webhook_token
    op.add_column(
        'workflow_nodes',
        sa.Column('webhook_token', sa.String(255), nullable=True, unique=True)
    )
    
    # Criar índice único para webhook_token
    op.create_index(
        'idx_workflow_node_webhook_token',
        'workflow_nodes',
        ['webhook_token'],
        unique=True
    )


def downgrade():
    # Remover índice
    op.drop_index('idx_workflow_node_webhook_token', table_name='workflow_nodes')
    
    # Remover coluna
    op.drop_column('workflow_nodes', 'webhook_token')

