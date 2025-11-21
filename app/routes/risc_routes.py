"""
Rotas para receber eventos RISC (Cross-Account Protection) do Google.
Endpoint público que recebe notificações de eventos de segurança.
"""
from flask import Blueprint, request, jsonify
from app.services.risc_service import RiscService
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('risc', __name__, url_prefix='/api/v1/risc')


@bp.route('/events', methods=['POST'])
def receive_security_event():
    """
    Endpoint para receber eventos de segurança RISC do Google.
    
    Este endpoint é público e é chamado pelo Google via webhook.
    Não requer autenticação tradicional, mas valida tokens JWT assinados pelo Google.
    
    Body esperado:
    {
        "security_event": "eyJhbGciOiJSUzI1NiIs..."  # JWT token
    }
    
    Ou diretamente o token JWT como string no body.
    """
    try:
        # Obter token do body
        data = request.get_json()
        
        if not data:
            # Tentar obter token diretamente como string
            token = request.data.decode('utf-8') if request.data else None
            if not token:
                return jsonify({
                    'error': 'Token de evento de segurança não fornecido'
                }), 400
        else:
            # Token pode estar em diferentes campos
            token = data.get('security_event') or data.get('token') or data.get('jwt')
            
            if not token:
                return jsonify({
                    'error': 'Token de evento de segurança não encontrado no body',
                    'expected_fields': ['security_event', 'token', 'jwt']
                }), 400
        
        # Processar evento
        result = RiscService.process_security_event(token)
        
        logger.info(f"Evento RISC processado com sucesso: {result.get('event_id')}")
        
        # Retornar 200 OK conforme especificação RISC
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Erro de validação no evento RISC: {str(e)}")
        return jsonify({
            'error': 'Token inválido',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Erro ao processar evento RISC: {str(e)}", exc_info=True)
        # Retornar 200 mesmo em caso de erro para evitar retries excessivos do Google
        # Mas logar o erro para investigação
        return jsonify({
            'error': 'Erro ao processar evento',
            'message': 'Evento recebido mas não processado corretamente'
        }), 200


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check para verificar se endpoint está acessível"""
    return jsonify({
        'status': 'ok',
        'service': 'risc',
        'endpoint': '/api/v1/risc/events'
    }), 200

