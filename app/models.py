from datetime import datetime, timedelta
from app.database import db
import uuid

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portal_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    clicksign_api_key = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    trial_expires_at = db.Column(db.DateTime, nullable=False)
    plan_expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, portal_id, clicksign_api_key=None, trial_days=20):
        self.portal_id = portal_id
        self.clicksign_api_key = clicksign_api_key
        self.created_at = datetime.utcnow()
        self.trial_expires_at = datetime.utcnow() + timedelta(days=trial_days)
        self.plan_expires_at = None
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_api_key=False):
        """Converte o modelo para dicionário"""
        data = {
            'id': self.id,
            'portal_id': self.portal_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'trial_expires_at': self.trial_expires_at.isoformat() if self.trial_expires_at else None,
            'plan_expires_at': self.plan_expires_at.isoformat() if self.plan_expires_at else None,
            'is_active': self.is_active,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_api_key:
            data['clicksign_api_key'] = self.clicksign_api_key
        
        return data
    
    def get_status(self):
        """Retorna o status da conta: 'trial', 'expired', ou 'active'"""
        now = datetime.utcnow()
        
        # Se tem plano ativo e não expirou
        if self.plan_expires_at and self.plan_expires_at > now:
            return 'active'
        
        # Se trial ainda está ativo
        if self.trial_expires_at and self.trial_expires_at > now:
            return 'trial'
        
        # Trial expirado e sem plano
        return 'expired'
    
    def __repr__(self):
        return f'<Account {self.portal_id}>'

