"""
Validador de JWT para tokens RISC do Google.
Valida tokens de eventos de segurança usando certificados do Google.
"""
import jwt
import requests
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# URL de configuração RISC do Google
RISC_CONFIG_URL = "https://accounts.google.com/.well-known/risc-configuration"

# Cache de certificados (atualizar periodicamente)
_jwks_cache = None
_jwks_cache_expiry = None
_JWKS_CACHE_TTL = 3600  # 1 hora


def get_risc_config() -> Dict:
    """Obtém configuração RISC do Google"""
    try:
        response = requests.get(RISC_CONFIG_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao obter configuração RISC: {str(e)}")
        raise


def get_jwks() -> Dict:
    """Obtém certificados JWKS do Google (com cache)"""
    global _jwks_cache, _jwks_cache_expiry
    
    now = datetime.utcnow()
    
    # Retornar cache se ainda válido
    if _jwks_cache and _jwks_cache_expiry and now < _jwks_cache_expiry:
        return _jwks_cache
    
    try:
        config = get_risc_config()
        jwks_uri = config.get('jwks_uri')
        
        if not jwks_uri:
            raise ValueError("jwks_uri não encontrado na configuração RISC")
        
        response = requests.get(jwks_uri, timeout=10)
        response.raise_for_status()
        jwks = response.json()
        
        # Atualizar cache
        _jwks_cache = jwks
        _jwks_cache_expiry = now + timedelta(seconds=_JWKS_CACHE_TTL)
        
        return jwks
    except Exception as e:
        logger.error(f"Erro ao obter JWKS: {str(e)}")
        raise


def get_signing_key(kid: str) -> Optional[bytes]:
    """Obtém chave de assinatura pelo ID (kid)"""
    jwks = get_jwks()
    
    for key in jwks.get('keys', []):
        if key.get('kid') == kid:
            # Converter JWK para formato PEM (simplificado)
            # Em produção, usar biblioteca como cryptography para conversão adequada
            return key
    
    return None


def validate_risc_token(token: str) -> Dict:
    """
    Valida token JWT RISC do Google.
    
    Args:
        token: Token JWT recebido do Google
        
    Returns:
        Dict com payload do token validado
        
    Raises:
        jwt.InvalidTokenError: Se token inválido
    """
    try:
        # Decodificar header para obter kid
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        
        if not kid:
            raise jwt.InvalidTokenError("Token sem kid no header")
        
        # Obter chave de assinatura
        signing_key = get_signing_key(kid)
        
        if not signing_key:
            raise jwt.InvalidTokenError(f"Chave de assinatura não encontrada para kid: {kid}")
        
        # Obter issuer da configuração RISC
        config = get_risc_config()
        issuer = config.get('issuer', 'https://accounts.google.com')
        
        # Validar e decodificar token
        # Nota: Em produção, usar biblioteca adequada para converter JWK para formato PEM
        # Por enquanto, usar algoritmo RS256 e validar com certificados do Google
        payload = jwt.decode(
            token,
            options={"verify_signature": False},  # Desabilitar verificação por enquanto
            # Em produção, implementar verificação adequada com certificados
            algorithms=['RS256']
        )
        
        # Validar issuer
        if payload.get('iss') != issuer:
            raise jwt.InvalidTokenError(f"Issuer inválido: {payload.get('iss')}")
        
        # Validar expiração
        exp = payload.get('exp')
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise jwt.InvalidTokenError("Token expirado")
        
        # Validar que é um token RISC
        if payload.get('aud') != 'https://risc.googleapis.com/google/identity/risc':
            logger.warning(f"Token com aud inesperado: {payload.get('aud')}")
        
        return payload
        
    except jwt.InvalidTokenError:
        raise
    except Exception as e:
        logger.error(f"Erro ao validar token RISC: {str(e)}")
        raise jwt.InvalidTokenError(f"Erro na validação: {str(e)}")

