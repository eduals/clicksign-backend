from functools import wraps
from flask import request, jsonify
from app.config import Config

def require_auth(f):
    """Decorator para exigir autenticação Bearer token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'Authorization header missing',
                'message': 'Bearer token é obrigatório'
            }), 401
        
        try:
            # Formato esperado: "Bearer {token}"
            token_type, token = auth_header.split(' ', 1)
            
            if token_type.lower() != 'bearer':
                return jsonify({
                    'error': 'Invalid authorization type',
                    'message': 'Tipo de autorização deve ser Bearer'
                }), 401
            
            # Validar token
            if token != Config.BACKEND_API_TOKEN:
                return jsonify({
                    'error': 'Invalid token',
                    'message': 'Token inválido'
                }), 401
            
        except ValueError:
            return jsonify({
                'error': 'Invalid authorization header format',
                'message': 'Formato do header Authorization inválido. Use: Bearer {token}'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

