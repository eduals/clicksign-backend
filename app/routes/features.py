from flask import Blueprint, request, jsonify, g
from app.database import db
from app.models import OrganizationFeature
from app.utils.auth import require_auth, require_org, require_admin
from app.utils.encryption import encrypt_credentials, decrypt_credentials
import logging

logger = logging.getLogger(__name__)
features_bp = Blueprint('features', __name__, url_prefix='/api/v1/features')


@features_bp.route('/clicksign', methods=['GET'])
@require_auth
@require_org
def get_clicksign_config():
    """Retorna configuração do ClickSign para a organização"""
    feature = OrganizationFeature.query.filter_by(
        organization_id=g.organization_id,
        feature_name='clicksign'
    ).first()
    
    if not feature:
        return jsonify({
            'success': True,
            'enabled': False,
            'configured': False
        }), 200
    
    config = feature.config or {}
    api_key = config.get('api_key') if config else None
    
    return jsonify({
        'success': True,
        'enabled': feature.enabled,
        'configured': bool(api_key),
        'has_api_key': bool(api_key)
    }), 200


@features_bp.route('/clicksign', methods=['POST'])
@require_auth
@require_org
@require_admin
def enable_clicksign():
    """
    Habilita e configura ClickSign para a organização.
    
    Body:
    {
        "api_key": "clicksign_api_key_here"
    }
    """
    data = request.get_json()
    
    if not data or not data.get('api_key'):
        return jsonify({'error': 'api_key é obrigatório'}), 400
    
    # Buscar ou criar feature
    feature = OrganizationFeature.query.filter_by(
        organization_id=g.organization_id,
        feature_name='clicksign'
    ).first()
    
    if feature:
        # Atualizar
        feature.enabled = True
        if not feature.config:
            feature.config = {}
        feature.config['api_key'] = data['api_key']
    else:
        # Criar nova
        feature = OrganizationFeature(
            organization_id=g.organization_id,
            feature_name='clicksign',
            enabled=True,
            config={'api_key': data['api_key']}
        )
        db.session.add(feature)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'ClickSign habilitado e configurado com sucesso',
        'feature': feature.to_dict()
    }), 200


@features_bp.route('/clicksign', methods=['PUT'])
@require_auth
@require_org
@require_admin
def update_clicksign_config():
    """Atualiza configuração do ClickSign"""
    data = request.get_json()
    
    feature = OrganizationFeature.query.filter_by(
        organization_id=g.organization_id,
        feature_name='clicksign'
    ).first_or_404()
    
    if 'api_key' in data:
        if not feature.config:
            feature.config = {}
        feature.config['api_key'] = data['api_key']
    
    if 'enabled' in data:
        feature.enabled = data['enabled']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Configuração atualizada com sucesso',
        'feature': feature.to_dict()
    }), 200


@features_bp.route('/clicksign', methods=['DELETE'])
@require_auth
@require_org
@require_admin
def disable_clicksign():
    """Desabilita ClickSign para a organização"""
    feature = OrganizationFeature.query.filter_by(
        organization_id=g.organization_id,
        feature_name='clicksign'
    ).first_or_404()
    
    feature.enabled = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'ClickSign desabilitado com sucesso'
    }), 200

