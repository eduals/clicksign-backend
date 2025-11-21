"""add_new_tables_for_clicksign

Revision ID: 2a3b4c5d6e7f
Revises: 16f16d3cbb7e
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2a3b4c5d6e7f'
down_revision = '16f16d3cbb7e'
branch_labels = None
depends_on = None


def upgrade():
    # Create field_mappings table
    op.create_table(
        'field_mappings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portal_id', sa.String(255), nullable=False, index=True),
        sa.Column('object_type', sa.String(50), nullable=False),
        sa.Column('clicksign_field_name', sa.String(255), nullable=False),
        sa.Column('clicksign_field_type', sa.String(50), nullable=False),
        sa.Column('hubspot_property_name', sa.String(255), nullable=False),
        sa.Column('hubspot_property_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create envelope_relations table
    op.create_table(
        'envelope_relations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portal_id', sa.String(255), nullable=False, index=True),
        sa.Column('hubspot_object_type', sa.String(50), nullable=False),
        sa.Column('hubspot_object_id', sa.String(255), nullable=False),
        sa.Column('clicksign_envelope_id', sa.String(255), nullable=False, index=True),
        sa.Column('envelope_name', sa.String(500), nullable=True),
        sa.Column('envelope_status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create index on envelope_relations
    op.create_index('idx_portal_object', 'envelope_relations', ['portal_id', 'hubspot_object_type', 'hubspot_object_id'])

    # Create google_oauth_tokens table
    op.create_table(
        'google_oauth_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portal_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expiry', sa.DateTime(), nullable=True),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create google_drive_config table
    op.create_table(
        'google_drive_config',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portal_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('templates_folder_id', sa.String(255), nullable=True),
        sa.Column('library_folder_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create envelope_execution_logs table
    op.create_table(
        'envelope_execution_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portal_id', sa.String(255), nullable=False, index=True),
        sa.Column('execution_id', sa.String(36), nullable=False, index=True),
        sa.Column('envelope_id', sa.String(255), nullable=True),
        sa.Column('step_name', sa.String(255), nullable=False),
        sa.Column('step_status', sa.String(50), nullable=False),
        sa.Column('step_message', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    # Create index on envelope_execution_logs
    op.create_index('idx_execution_order', 'envelope_execution_logs', ['execution_id', 'step_order'])


def downgrade():
    # Drop indexes first
    op.drop_index('idx_execution_order', 'envelope_execution_logs')
    op.drop_index('idx_portal_object', 'envelope_relations')
    
    # Drop tables
    op.drop_table('envelope_execution_logs')
    op.drop_table('google_drive_config')
    op.drop_table('google_oauth_tokens')
    op.drop_table('envelope_relations')
    op.drop_table('field_mappings')

