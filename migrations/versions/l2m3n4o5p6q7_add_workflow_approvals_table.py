"""Add workflow_approvals table

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'l2m3n4o5p6q7'
down_revision = 'k1l2m3n4o5p6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'workflow_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_context', postgresql.JSONB),
        sa.Column('approver_email', sa.String(255), nullable=False),
        sa.Column('approval_token', sa.String(255), unique=True, nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('message_template', sa.Text),
        sa.Column('timeout_hours', sa.Integer, default=48),
        sa.Column('auto_approve_on_timeout', sa.Boolean, default=False),
        sa.Column('document_urls', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('approved_at', sa.DateTime),
        sa.Column('rejected_at', sa.DateTime),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('rejection_comment', sa.Text),
        sa.ForeignKeyConstraint(['workflow_execution_id'], ['workflow_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['node_id'], ['workflow_nodes.id'], ondelete='CASCADE'),
    )
    
    op.create_index('idx_approval_token', 'workflow_approvals', ['approval_token'], unique=True)
    op.create_index('idx_approval_execution', 'workflow_approvals', ['workflow_execution_id'])
    op.create_index('idx_approval_status', 'workflow_approvals', ['status'])
    op.create_index('idx_approval_expires', 'workflow_approvals', ['expires_at'])


def downgrade():
    op.drop_index('idx_approval_expires', table_name='workflow_approvals')
    op.drop_index('idx_approval_status', table_name='workflow_approvals')
    op.drop_index('idx_approval_execution', table_name='workflow_approvals')
    op.drop_index('idx_approval_token', table_name='workflow_approvals')
    op.drop_table('workflow_approvals')

