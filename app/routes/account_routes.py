from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import text
import json
from app.database import db
from app.models import Account
from app.auth import require_auth
from app.config import Config

bp = Blueprint('account', __name__, url_prefix='/api/account')

@bp.route('/health', methods=['GET'])
def healthcheck():
    """Healthcheck endpoint para verificar se a API está online"""
    try:
        # Testar conexão com o banco de dados
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'message': 'API is online and database connection is working',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': 'API is online but database connection failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@bp.route('/<portal_id>', methods=['GET'])
@require_auth
def get_account(portal_id):
    """Recupera informações da conta e API key do Clicksign"""
    try:
        account = Account.query.filter_by(portal_id=portal_id).first()
        
        if not account:
            return jsonify({
                'error': 'Account not found',
                'message': f'Conta com portal_id {portal_id} não encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'data': account.to_dict(include_api_key=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@bp.route('/<portal_id>', methods=['POST'])
@require_auth
def create_account(portal_id):
    """Cria nova conta (se não existir)"""
    try:
        # Verificar se conta já existe
        existing_account = Account.query.filter_by(portal_id=portal_id).first()
        
        if existing_account:
            return jsonify({
                'error': 'Account already exists',
                'message': f'Conta com portal_id {portal_id} já existe',
                'data': existing_account.to_dict()
            }), 409
        
        # Obter clicksign_api_key do body se fornecido
        # Usar force=True para forçar parse do JSON mesmo sem Content-Type header
        data = request.get_json(force=True, silent=True) or {}
        if not isinstance(data, dict):
            data = {}
        clicksign_api_key = data.get('clicksign_api_key')
        
        # Criar nova conta
        account = Account(
            portal_id=portal_id,
            clicksign_api_key=clicksign_api_key,
            trial_days=Config.TRIAL_DAYS
        )
        
        db.session.add(account)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Conta criada com sucesso',
            'data': account.to_dict(include_api_key=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@bp.route('/<portal_id>/clicksign-key', methods=['POST'])
@require_auth
def update_clicksign_key(portal_id):
    """Salva/atualiza API key do Clicksign"""
    try:
        data = None
        body_str = None
        
        # Método 1: Tentar request.get_json com force=True
        try:
            data = request.get_json(force=True, silent=True)
            if data and isinstance(data, dict):
                # Sucesso!
                pass
        except Exception:
            pass
        
        # Método 2: Se não funcionou, tentar obter body como string e fazer parse manual
        if not data or not isinstance(data, dict):
            try:
                # Tentar como texto primeiro
                body_str = request.get_data(as_text=True)
                if not body_str or not body_str.strip():
                    # Se não funcionou, tentar como bytes e converter
                    body_bytes = request.get_data()
                    if body_bytes:
                        body_str = body_bytes.decode('utf-8')
                
                if body_str and body_str.strip():
                    # Tentar fazer parse direto
                    data = json.loads(body_str)
            except (json.JSONDecodeError, ValueError, TypeError, AttributeError, UnicodeDecodeError):
                pass
        
        # Método 3: Tentar request.get_json sem force
        if not data or not isinstance(data, dict):
            try:
                data = request.get_json(silent=True)
            except Exception:
                pass
        
        # Método 4: Tentar obter de request.form (caso venha como form data)
        if not data or not isinstance(data, dict):
            try:
                if request.form:
                    data = dict(request.form)
                    # Se vier como form, pode estar como string JSON
                    if 'clicksign_api_key' in data:
                        clicksign_api_key = data['clicksign_api_key']
                        if isinstance(clicksign_api_key, list) and len(clicksign_api_key) > 0:
                            clicksign_api_key = clicksign_api_key[0]
                        # Pular para usar a chave diretamente
                        if clicksign_api_key:
                            account = Account.query.filter_by(portal_id=portal_id).first()
                            if not account:
                                account = Account(
                                    portal_id=portal_id,
                                    clicksign_api_key=clicksign_api_key,
                                    trial_days=Config.TRIAL_DAYS
                                )
                                db.session.add(account)
                            else:
                                account.clicksign_api_key = clicksign_api_key
                                account.updated_at = datetime.utcnow()
                            db.session.commit()
                            return jsonify({
                                'success': True,
                                'message': 'API key salva com sucesso',
                                'data': {
                                    'portal_id': account.portal_id,
                                    'updated_at': account.updated_at.isoformat()
                                }
                            }), 200
            except Exception:
                pass
        
        # Verificar se finalmente temos dados válidos
        if not data or not isinstance(data, dict):
            # Obter body_str se ainda não tiver
            if not body_str:
                try:
                    body_str = request.get_data(as_text=True)
                except:
                    body_str = None
            
            # Retornar erro com informações úteis para debug
            error_response = {
                'error': 'Invalid request body',
                'message': 'Não foi possível processar o body da requisição. Envie JSON válido com clicksign_api_key.',
                'debug_info': {
                    'body_received': body_str[:500] if body_str else 'Empty body',
                    'body_length': len(body_str) if body_str else 0,
                    'content_type': request.content_type or 'Not set',
                    'method': request.method,
                    'has_form': bool(request.form),
                    'form_keys': list(request.form.keys()) if request.form else [],
                    'has_json': request.is_json if hasattr(request, 'is_json') else 'unknown'
                }
            }
            return jsonify(error_response), 400
        
        # Verificar se tem a chave obrigatória
        if 'clicksign_api_key' not in data:
            return jsonify({
                'error': 'Missing required field',
                'message': 'clicksign_api_key é obrigatório no body',
                'received_keys': list(data.keys()) if isinstance(data, dict) else None
            }), 400
        
        clicksign_api_key = data['clicksign_api_key']
        
        # Buscar ou criar conta
        account = Account.query.filter_by(portal_id=portal_id).first()
        
        if not account:
            # Criar conta se não existir
            account = Account(
                portal_id=portal_id,
                clicksign_api_key=clicksign_api_key,
                trial_days=Config.TRIAL_DAYS
            )
            db.session.add(account)
        else:
            # Atualizar API key
            account.clicksign_api_key = clicksign_api_key
            account.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'API key salva com sucesso',
            'data': {
                'portal_id': account.portal_id,
                'updated_at': account.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@bp.route('/<portal_id>/status', methods=['GET'])
@require_auth
def get_account_status(portal_id):
    """Retorna status da conta (trial ativo, expirado, plano ativo)"""
    try:
        account = Account.query.filter_by(portal_id=portal_id).first()
        
        if not account:
            return jsonify({
                'error': 'Account not found',
                'message': f'Conta com portal_id {portal_id} não encontrada'
            }), 404
        
        status = account.get_status()
        
        return jsonify({
            'success': True,
            'data': {
                'status': status,
                'trial_expires_at': account.trial_expires_at.isoformat() if account.trial_expires_at else None,
                'plan_expires_at': account.plan_expires_at.isoformat() if account.plan_expires_at else None,
                'is_active': account.is_active
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

