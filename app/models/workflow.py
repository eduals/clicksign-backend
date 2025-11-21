import uuid
from datetime import datetime
from app.database import db
from sqlalchemy.dialects.postgresql import UUID, JSONB

class Workflow(db.Model):
    __tablename__ = 'workflows'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='draft')  # draft, active, paused, archived
    
    # Source
    source_connection_id = db.Column(UUID(as_uuid=True), db.ForeignKey('data_source_connections.id'))
    source_object_type = db.Column(db.String(100))
    source_config = db.Column(JSONB)
    
    # Template
    template_id = db.Column(UUID(as_uuid=True), db.ForeignKey('templates.id'))
    
    # Output
    output_folder_id = db.Column(db.String(255))
    output_name_template = db.Column(db.String(500))
    create_pdf = db.Column(db.Boolean, default=True)
    
    # Trigger
    trigger_type = db.Column(db.String(50), default='manual')
    trigger_config = db.Column(JSONB)
    
    # Post Actions
    post_actions = db.Column(JSONB)
    
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    field_mappings = db.relationship('WorkflowFieldMapping', backref='workflow', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('GeneratedDocument', backref='workflow', lazy='dynamic')
    executions = db.relationship('WorkflowExecution', backref='workflow', lazy='dynamic')
    
    def to_dict(self, include_mappings=False):
        result = {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'source_connection_id': str(self.source_connection_id) if self.source_connection_id else None,
            'source_object_type': self.source_object_type,
            'source_config': self.source_config,
            'template_id': str(self.template_id) if self.template_id else None,
            'output_folder_id': self.output_folder_id,
            'output_name_template': self.output_name_template,
            'create_pdf': self.create_pdf,
            'trigger_type': self.trigger_type,
            'trigger_config': self.trigger_config,
            'post_actions': self.post_actions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_mappings:
            result['field_mappings'] = [
                m.to_dict() for m in self.field_mappings
            ]
        
        if self.template:
            result['template'] = {
                'id': str(self.template.id),
                'name': self.template.name,
                'google_file_type': self.template.google_file_type,
                'thumbnail_url': self.template.thumbnail_url
            }
        
        return result


class WorkflowFieldMapping(db.Model):
    __tablename__ = 'workflow_field_mappings'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = db.Column(UUID(as_uuid=True), db.ForeignKey('workflows.id'), nullable=False)
    template_tag = db.Column(db.String(255), nullable=False)
    source_field = db.Column(db.String(255), nullable=False)
    transform_type = db.Column(db.String(50))
    transform_config = db.Column(JSONB)
    default_value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('workflow_id', 'template_tag', name='unique_workflow_tag'),
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'workflow_id': str(self.workflow_id),
            'template_tag': self.template_tag,
            'source_field': self.source_field,
            'transform_type': self.transform_type,
            'transform_config': self.transform_config,
            'default_value': self.default_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

