"""
Rotas para OAuth do Microsoft Graph API.
Similar ao Google OAuth, mas para Microsoft 365/OneDrive.
"""
from flask import Blueprint, request, jsonify, redirect, g
from app.database import db
from app.models import DataSourceConnection, Organization
from app.utils.auth import require_auth, require_org
from app.utils.hubspot_auth import flexible_hubspot_auth
from app.utils.encryption import encrypt_credentials, decrypt_credentials
from app.config import Config
from datetime import datetime, timedelta
from urllib.parse import urlencode
import os
import json
import uuid
import logging
import secrets
import base64
import hashlib
import requests

logger = logging.getLogger(__name__)
microsoft_oauth_bp = Blueprint('microsoft_oauth', __name__, url_prefix='/api/v1/microsoft/oauth')

# Microsoft OAuth endpoints
MICROSOFT_AUTHORIZATION_ENDPOINT = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
MICROSOFT_TOKEN_ENDPOINT = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'

# Scopes necessários para Microsoft Graph API
SCOPES = [
    'Files.ReadWrite.All',  # Ler e escrever arquivos no OneDrive/SharePoint
    'Mail.Send',             # Enviar emails (para Outlook)
    'User.Read',             # Ler perfil do usuário
    'offline_access'         # Refresh token
]

# Armazenamento temporário para PKCE (usar mesmo modelo do Google)
_PKCE_TTL = 600  # 10 minutos

def _generate_code_verifier():
    """Gera um code_verifier para PKCE (43-128 caracteres, URL-safe)"""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

def _generate_code_challenge(verifier):
    """Gera code_challenge a partir do code_verifier usando SHA256"""
    challenge = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(challenge).decode('utf-8').rstrip('=')

def _store_pkce_verifier(state, verifier, frontend_redirect_uri=None):
    """Armazena code_verifier temporariamente associado ao state no banco de dados"""
    from app.models import PKCEVerifier
    
    expires_at = datetime.utcnow() + timedelta(seconds=_PKCE_TTL)
    
    # Remover entrada existente se houver (one-time use)
    existing = PKCEVerifier.query.filter_by(state=state).first()
    if existing:
        db.session.delete(existing)
    
    # Criar nova entrada
    pkce_entry = PKCEVerifier(
        state=state,
        code_verifier=verifier,
        frontend_redirect_uri=frontend_redirect_uri,
        expires_at=expires_at
    )
    db.session.add(pkce_entry)
    db.session.commit()
    
    return pkce_entry

def _get_pkce_verifier(state):
    """Recupera code_verifier do banco de dados"""
    from app.models import PKCEVerifier
    
    pkce_entry = PKCEVerifier.query.filter_by(state=state).first()
    if not pkce_entry:
        return None
    
    # Verificar se expirou
    if pkce_entry.expires_at < datetime.utcnow():
        db.session.delete(pkce_entry)
        db.session.commit()
        return None
    
    # Remover após uso (one-time use)
    verifier = pkce_entry.code_verifier
    db.session.delete(pkce_entry)
    db.session.commit()
    
    return verifier


@microsoft_oauth_bp.route('/authorize', methods=['GET'])
@flexible_hubspot_auth
@require_org
def authorize():
    """
    Inicia o fluxo OAuth do Microsoft.
    
    Query params:
    - frontend_redirect_uri: URI para redirecionar após autenticação
    - organization_id: ID da organização (opcional, usa g.organization_id se não fornecido)
    """
    frontend_redirect_uri = request.args.get('frontend_redirect_uri')
    organization_id = request.args.get('organization_id') or g.organization_id
    
    if not organization_id:
        return jsonify({'error': 'organization_id é obrigatório'}), 400
    
    # Obter credenciais do Microsoft do config
    client_id = os.getenv('MICROSOFT_CLIENT_ID')
    client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        return jsonify({
            'error': 'Microsoft OAuth não configurado. Configure MICROSOFT_CLIENT_ID e MICROSOFT_CLIENT_SECRET'
        }), 500
    
    # Gerar state e PKCE
    state = secrets.token_urlsafe(32)
    code_verifier = _generate_code_verifier()
    code_challenge = _generate_code_challenge(code_verifier)
    
    # Armazenar code_verifier
    _store_pkce_verifier(state, code_verifier, frontend_redirect_uri)
    
    # Construir URL de autorização
    redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI', f'{request.url_root.rstrip("/")}/api/v1/microsoft/oauth/callback')
    scope_string = ' '.join(SCOPES)
    
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'response_mode': 'query',
        'scope': scope_string,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    
    authorization_url = f"{MICROSOFT_AUTHORIZATION_ENDPOINT}?{urlencode(params)}"
    
    return jsonify({
        'success': True,
        'authorization_url': authorization_url,
        'state': state
    })


@microsoft_oauth_bp.route('/callback', methods=['GET'])
def callback():
    """
    Callback do OAuth do Microsoft.
    Recebe o código de autorização e troca por access token.
    """
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        logger.error(f'Erro no callback do Microsoft OAuth: {error}')
        return jsonify({'error': f'OAuth error: {error}'}), 400
    
    if not code or not state:
        return jsonify({'error': 'code e state são obrigatórios'}), 400
    
    # Recuperar code_verifier
    code_verifier = _get_pkce_verifier(state)
    if not code_verifier:
        return jsonify({'error': 'State inválido ou expirado'}), 400
    
    # Obter credenciais
    client_id = os.getenv('MICROSOFT_CLIENT_ID')
    client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
    redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI', f'{request.url_root.rstrip("/")}/api/v1/microsoft/oauth/callback')
    
    # Trocar código por token
    try:
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
            'code_verifier': code_verifier,
        }
        
        response = requests.post(MICROSOFT_TOKEN_ENDPOINT, data=token_data)
        response.raise_for_status()
        token_response = response.json()
        
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')
        expires_in = token_response.get('expires_in', 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Obter informações do usuário
        user_info_response = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        user_info = user_info_response.json() if user_info_response.ok else {}
        
        # Buscar organization_id do state (pode estar no frontend_redirect_uri ou precisar ser passado)
        # Por enquanto, usar g.organization_id se disponível
        organization_id = g.organization_id if hasattr(g, 'organization_id') else None
        
        if not organization_id:
            # Tentar extrair do frontend_redirect_uri ou usar default
            # Por enquanto, retornar erro se não tiver
            return jsonify({'error': 'organization_id não encontrado'}), 400
        
        # Criar ou atualizar conexão
        connection = DataSourceConnection.query.filter_by(
            organization_id=organization_id,
            source_type='microsoft'
        ).first()
        
        # Criptografar credenciais
        credentials_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at.isoformat(),
            'user_email': user_info.get('mail') or user_info.get('userPrincipalName'),
            'user_name': user_info.get('displayName'),
        }
        
        encrypted_credentials = encrypt_credentials(credentials_data)
        
        if connection:
            connection.credentials = {'encrypted': encrypted_credentials}
            connection.status = 'active'
            connection.updated_at = datetime.utcnow()
        else:
            connection = DataSourceConnection(
                organization_id=organization_id,
                source_type='microsoft',
                name=f'Microsoft ({user_info.get("displayName", "User")})',
                credentials={'encrypted': encrypted_credentials},
                status='active'
            )
            db.session.add(connection)
        
        db.session.commit()
        
        # Redirecionar para frontend se fornecido
        frontend_redirect_uri = request.args.get('frontend_redirect_uri')
        if frontend_redirect_uri:
            return redirect(f"{frontend_redirect_uri}?success=true&organization_id={organization_id}")
        
        return jsonify({
            'success': True,
            'organization_id': str(organization_id),
            'connection_id': str(connection.id),
            'user': {
                'email': credentials_data['user_email'],
                'name': credentials_data['user_name']
            }
        })
        
    except requests.exceptions.RequestException as e:
        logger.exception(f'Erro ao trocar código por token: {str(e)}')
        return jsonify({'error': f'Erro ao autenticar: {str(e)}'}), 500
    except Exception as e:
        logger.exception(f'Erro inesperado no callback: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@microsoft_oauth_bp.route('/status', methods=['GET'])
@flexible_hubspot_auth
@require_org
def status():
    """
    Verifica status da conexão Microsoft.
    """
    organization_id = g.organization_id
    
    connection = DataSourceConnection.query.filter_by(
        organization_id=organization_id,
        source_type='microsoft',
        status='active'
    ).first()
    
    if not connection:
        return jsonify({
            'success': True,
            'connected': False
        })
    
    # Verificar se token está válido
    try:
        credentials = connection.get_decrypted_credentials()
        access_token = credentials.get('access_token')
        expires_at_str = credentials.get('expires_at')
        
        if not access_token:
            return jsonify({
                'success': True,
                'connected': False
            })
        
        # Verificar se expirou
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            if expires_at < datetime.utcnow():
                # Tentar refresh
                refreshed = _refresh_microsoft_token(connection)
                if not refreshed:
                    return jsonify({
                        'success': True,
                        'connected': False,
                        'message': 'Token expirado e não foi possível renovar'
                    })
        
        # Verificar token fazendo request simples
        test_response = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=5
        )
        
        if test_response.ok:
            user_info = test_response.json()
            return jsonify({
                'success': True,
                'connected': True,
                'email': user_info.get('mail') or user_info.get('userPrincipalName'),
                'name': user_info.get('displayName'),
                'scopes': SCOPES
            })
        else:
            return jsonify({
                'success': True,
                'connected': False,
                'message': 'Token inválido'
            })
            
    except Exception as e:
        logger.exception(f'Erro ao verificar status: {str(e)}')
        return jsonify({
            'success': True,
            'connected': False,
            'message': str(e)
        })


def _refresh_microsoft_token(connection: DataSourceConnection) -> bool:
    """
    Atualiza o access token usando refresh token.
    
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        from flask import current_app
        credentials = connection.get_decrypted_credentials()
        refresh_token = credentials.get('refresh_token')
        
        if not refresh_token:
            return False
        
        client_id = os.getenv('MICROSOFT_CLIENT_ID')
        client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
        # Usar URL base do config ou padrão
        api_base_url = current_app.config.get('API_BASE_URL', 'http://localhost:5000')
        redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI', f'{api_base_url.rstrip("/")}/api/v1/microsoft/oauth/callback')
        
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
            'redirect_uri': redirect_uri,
        }
        
        response = requests.post(MICROSOFT_TOKEN_ENDPOINT, data=token_data)
        response.raise_for_status()
        token_response = response.json()
        
        access_token = token_response.get('access_token')
        new_refresh_token = token_response.get('refresh_token', refresh_token)  # Manter o antigo se não vier novo
        expires_in = token_response.get('expires_in', 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Atualizar credenciais
        credentials['access_token'] = access_token
        credentials['refresh_token'] = new_refresh_token
        credentials['expires_at'] = expires_at.isoformat()
        
        encrypted_credentials = encrypt_credentials(credentials)
        connection.credentials = {'encrypted': encrypted_credentials}
        connection.updated_at = datetime.utcnow()
        
        db.session.commit()
        return True
        
    except Exception as e:
        logger.exception(f'Erro ao atualizar token: {str(e)}')
        db.session.rollback()
        return False

