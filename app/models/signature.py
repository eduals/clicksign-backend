import uuid
from datetime import datetime
from app.database import db
from sqlalchemy.dialects.postgresql import UUID, JSONB

class SignatureRequest(db.Model):
    __tablename__ = 'signature_requests'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    generated_document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('generated_documents.id'), nullable=False)
    
    # Provider
    provider = db.Column(db.String(50), nullable=False)
    external_id = db.Column(db.String(255))
    external_url = db.Column(db.String(500))
    
    # Status
    status = db.Column(db.String(50), default='pending')
    # pending, sent, viewed, signed, declined, expired, error
    
    # Signers
    signers = db.Column(JSONB)
    
    # Timestamps
    sent_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    webhook_data = db.Column(JSONB)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'generated_document_id': str(self.generated_document_id),
            'provider': self.provider,
            'external_id': self.external_id,
            'external_url': self.external_url,
            'status': self.status,
            'signers': self.signers,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

