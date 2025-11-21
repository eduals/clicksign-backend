"""add_docgen_tables

Revision ID: 3b4c5d6e7f8a
Revises: 2a3b4c5d6e7f
Create Date: 2024-11-21 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3b4c5d6e7f8a'
down_revision = '2a3b4c5d6e7f'
branch_labels = None
depends_on = None


def upgrade():
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('plan', sa.String(50), server_default='free'),
        sa.Column('documents_limit', sa.Integer, server_default='10'),
        sa.Column('documents_used', sa.Integer, server_default='0'),
        sa.Column('users_limit', sa.Integer, server_default='1'),
        sa.Column('billing_email', sa.String(255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), server_default='user'),
        sa.Column('hubspot_user_id', sa.String(100), nullable=True),
        sa.Column('google_user_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'email', name='unique_user_org_email')
    )
    
    # Create data_source_connections table
    op.create_table(
        'data_source_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('credentials', postgresql.JSONB, nullable=True),
        sa.Column('config', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create templates table
    op.create_table(
        'templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('google_file_id', sa.String(255), nullable=False),
        sa.Column('google_file_type', sa.String(50), nullable=False),
        sa.Column('google_file_url', sa.String(500), nullable=True),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('detected_tags', postgresql.JSONB, nullable=True),
        sa.Column('version', sa.Integer, server_default='1'),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('source_connection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_source_connections.id'), nullable=True),
        sa.Column('source_object_type', sa.String(100), nullable=True),
        sa.Column('source_config', postgresql.JSONB, nullable=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('templates.id'), nullable=True),
        sa.Column('output_folder_id', sa.String(255), nullable=True),
        sa.Column('output_name_template', sa.String(500), nullable=True),
        sa.Column('create_pdf', sa.Boolean(), server_default='true'),
        sa.Column('trigger_type', sa.String(50), server_default='manual'),
        sa.Column('trigger_config', postgresql.JSONB, nullable=True),
        sa.Column('post_actions', postgresql.JSONB, nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create workflow_field_mappings table
    op.create_table(
        'workflow_field_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('template_tag', sa.String(255), nullable=False),
        sa.Column('source_field', sa.String(255), nullable=False),
        sa.Column('transform_type', sa.String(50), nullable=True),
        sa.Column('transform_config', postgresql.JSONB, nullable=True),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('workflow_id', 'template_tag', name='unique_workflow_tag')
    )
    
    # Create generated_documents table
    op.create_table(
        'generated_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workflows.id'), nullable=True),
        sa.Column('source_connection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_source_connections.id'), nullable=True),
        sa.Column('source_object_type', sa.String(100), nullable=True),
        sa.Column('source_object_id', sa.String(255), nullable=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('templates.id'), nullable=True),
        sa.Column('template_version', sa.Integer, nullable=True),
        sa.Column('name', sa.String(500), nullable=True),
        sa.Column('google_doc_id', sa.String(255), nullable=True),
        sa.Column('google_doc_url', sa.String(500), nullable=True),
        sa.Column('pdf_file_id', sa.String(255), nullable=True),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), server_default='generating'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('generated_data', postgresql.JSONB, nullable=True),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create signature_requests table
    op.create_table(
        'signature_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('generated_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('generated_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('external_url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('signers', postgresql.JSONB, nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('webhook_data', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('generated_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('generated_documents.id'), nullable=True),
        sa.Column('trigger_type', sa.String(50), nullable=True),
        sa.Column('trigger_data', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(50), server_default='running'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    
    # Create organization_features table
    op.create_table(
        'organization_features',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('feature_name', sa.String(100), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='false'),
        sa.Column('config', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'feature_name', name='unique_org_feature')
    )
    
    # Create indexes
    op.create_index('idx_users_organization', 'users', ['organization_id'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_templates_organization', 'templates', ['organization_id'])
    op.create_index('idx_workflows_organization', 'workflows', ['organization_id'])
    op.create_index('idx_workflows_status', 'workflows', ['status'])
    op.create_index('idx_generated_documents_organization', 'generated_documents', ['organization_id'])
    op.create_index('idx_generated_documents_workflow', 'generated_documents', ['workflow_id'])
    op.create_index('idx_generated_documents_source', 'generated_documents', ['source_object_type', 'source_object_id'])
    op.create_index('idx_generated_documents_status', 'generated_documents', ['status'])
    op.create_index('idx_signature_requests_document', 'signature_requests', ['generated_document_id'])
    op.create_index('idx_signature_requests_status', 'signature_requests', ['status'])
    op.create_index('idx_workflow_executions_workflow', 'workflow_executions', ['workflow_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_workflow_executions_workflow')
    op.drop_index('idx_signature_requests_status')
    op.drop_index('idx_signature_requests_document')
    op.drop_index('idx_generated_documents_status')
    op.drop_index('idx_generated_documents_source')
    op.drop_index('idx_generated_documents_workflow')
    op.drop_index('idx_generated_documents_organization')
    op.drop_index('idx_workflows_status')
    op.drop_index('idx_workflows_organization')
    op.drop_index('idx_templates_organization')
    op.drop_index('idx_users_email')
    op.drop_index('idx_users_organization')
    
    # Drop tables
    op.drop_table('organization_features')
    op.drop_table('workflow_executions')
    op.drop_table('signature_requests')
    op.drop_table('generated_documents')
    op.drop_table('workflow_field_mappings')
    op.drop_table('workflows')
    op.drop_table('templates')
    op.drop_table('data_source_connections')
    op.drop_table('users')
    op.drop_table('organizations')

