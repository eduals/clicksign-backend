from flask import Blueprint, request, jsonify, g
from app.database import db
from app.models import DataSourceConnection
from app.services.data_sources.hubspot import HubSpotDataSource
from app.utils.auth import require_auth, require_org, require_admin
from app.utils.encryption import encrypt_credentials, decrypt_credentials
import logging

logger = logging.getLogger(__name__)
connections_bp = Blueprint('connections', __name__, url_prefix='/api/v1/connections')


@connections_bp.route('', methods=['GET'])
@require_auth
@require_org
def list_connections():
    """Lista conexões de dados da organização"""
    org_id = g.organization_id
    source_type = request.args.get('source_type')
    
    query = DataSourceConnection.query.filter_by(organization_id=org_id)
    
    if source_type:
        query = query.filter_by(source_type=source_type)
    
    connections = query.order_by(DataSourceConnection.created_at.desc()).all()
    
    return jsonify({
        'connections': [conn.to_dict() for conn in connections]
    })


@connections_bp.route('/<connection_id>', methods=['GET'])
@require_auth
@require_org
def get_connection(connection_id):
    """Retorna detalhes de uma conexão"""
    connection = DataSourceConnection.query.filter_by(
        id=connection_id,
        organization_id=g.organization_id
    ).first_or_404()
    
    return jsonify(connection.to_dict(include_credentials=False))


@connections_bp.route('', methods=['POST'])
@require_auth
@require_org
@require_admin
def create_connection():
    """
    Cria uma nova conexão de dados.
    
    Body:
    {
        "source_type": "hubspot",
        "name": "HubSpot Production",
        "credentials": {
            "access_token": "..."
        },
        "config": {
            "portal_id": "123456"
        }
    }
    """
    data = request.get_json()
    
    required = ['source_type', 'name']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} é obrigatório'}), 400
    
    # Criptografar credenciais
    credentials = data.get('credentials', {})
    if credentials:
        encrypted_creds = encrypt_credentials(credentials)
        credentials = {'encrypted': encrypted_creds}
    
    # Criar conexão
    connection = DataSourceConnection(
        organization_id=g.organization_id,
        source_type=data['source_type'],
        name=data['name'],
        credentials=credentials,
        config=data.get('config', {}),
        status='active'
    )
    
    db.session.add(connection)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'connection': connection.to_dict(include_credentials=False)
    }), 201


@connections_bp.route('/<connection_id>', methods=['PUT'])
@require_auth
@require_org
@require_admin
def update_connection(connection_id):
    """Atualiza uma conexão"""
    connection = DataSourceConnection.query.filter_by(
        id=connection_id,
        organization_id=g.organization_id
    ).first_or_404()
    
    data = request.get_json()
    
    # Atualizar campos permitidos
    if 'name' in data:
        connection.name = data['name']
    
    if 'credentials' in data:
        encrypted_creds = encrypt_credentials(data['credentials'])
        connection.credentials = {'encrypted': encrypted_creds}
    
    if 'config' in data:
        connection.config = data['config']
    
    if 'status' in data:
        connection.status = data['status']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'connection': connection.to_dict(include_credentials=False)
    })


@connections_bp.route('/<connection_id>/test', methods=['POST'])
@require_auth
@require_org
def test_connection(connection_id):
    """Testa uma conexão"""
    connection = DataSourceConnection.query.filter_by(
        id=connection_id,
        organization_id=g.organization_id
    ).first_or_404()
    
    try:
        if connection.source_type == 'hubspot':
            # Descriptografar credenciais
            if connection.credentials and connection.credentials.get('encrypted'):
                decrypted = decrypt_credentials(connection.credentials['encrypted'])
                connection.credentials = decrypted
            
            data_source = HubSpotDataSource(connection)
            is_valid = data_source.test_connection()
            
            if is_valid:
                connection.status = 'active'
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Conexão testada com sucesso'
                })
            else:
                connection.status = 'error'
                db.session.commit()
                return jsonify({
                    'success': False,
                    'message': 'Falha ao testar conexão'
                }), 400
        else:
            return jsonify({
                'error': f'Tipo de fonte {connection.source_type} não suportado para teste'
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao testar conexão: {str(e)}")
        connection.status = 'error'
        db.session.commit()
        return jsonify({
            'error': str(e)
        }), 500


@connections_bp.route('/<connection_id>', methods=['DELETE'])
@require_auth
@require_org
@require_admin
def delete_connection(connection_id):
    """Deleta uma conexão"""
    connection = DataSourceConnection.query.filter_by(
        id=connection_id,
        organization_id=g.organization_id
    ).first_or_404()
    
    # Verificar se tem workflows usando
    if connection.workflows.count() > 0:
        return jsonify({
            'error': 'Conexão está sendo usada por workflows. Remova os workflows primeiro.'
        }), 400
    
    db.session.delete(connection)
    db.session.commit()
    
    return jsonify({'success': True})

