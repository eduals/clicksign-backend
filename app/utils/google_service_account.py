"""
Utilitário para carregar credenciais da Google Service Account.
Suporta carregar de arquivo JSON ou de variáveis de ambiente.
"""
import os
import json
import logging
from typing import Optional, Dict
from google.oauth2 import service_account
from google.auth.transport import requests

logger = logging.getLogger(__name__)


def get_service_account_credentials(scopes: list = None) -> Optional[service_account.Credentials]:
    """
    Obtém credenciais da Google Service Account.
    
    Tenta carregar das seguintes fontes (em ordem de prioridade):
    1. Variáveis de ambiente (GOOGLE_SERVICE_ACCOUNT_*)
    2. Arquivo JSON (GOOGLE_SERVICE_ACCOUNT_KEY_PATH ou GOOGLE_APPLICATION_CREDENTIALS)
    
    Args:
        scopes: Lista de scopes OAuth (opcional)
        
    Returns:
        Credentials object ou None se não conseguir carregar
    """
    scopes = scopes or ['https://www.googleapis.com/auth/risc.configuration.readwrite']
    
    # Tentar carregar de variáveis de ambiente primeiro
    service_account_info = _load_from_env()
    
    if service_account_info:
        try:
            logger.info("Carregando credenciais da service account de variáveis de ambiente")
            return service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=scopes
            )
        except Exception as e:
            logger.error(f"Erro ao carregar credenciais de variáveis de ambiente: {str(e)}")
            return None
    
    # Tentar carregar de arquivo JSON
    key_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH') or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if key_path and os.path.exists(key_path):
        try:
            logger.info(f"Carregando credenciais da service account de arquivo: {key_path}")
            return service_account.Credentials.from_service_account_file(
                key_path,
                scopes=scopes
            )
        except Exception as e:
            logger.error(f"Erro ao carregar credenciais de arquivo: {str(e)}")
            return None
    
    logger.warning("Nenhuma credencial de service account encontrada")
    return None


def _load_from_env() -> Optional[Dict]:
    """
    Carrega informações da service account de variáveis de ambiente.
    
    Variáveis esperadas:
    - GOOGLE_SERVICE_ACCOUNT_TYPE
    - GOOGLE_SERVICE_ACCOUNT_PROJECT_ID
    - GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID
    - GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY
    - GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL
    - GOOGLE_SERVICE_ACCOUNT_CLIENT_ID
    - GOOGLE_SERVICE_ACCOUNT_AUTH_URI
    - GOOGLE_SERVICE_ACCOUNT_TOKEN_URI
    - GOOGLE_SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL
    - GOOGLE_SERVICE_ACCOUNT_CLIENT_X509_CERT_URL
    - GOOGLE_SERVICE_ACCOUNT_UNIVERSE_DOMAIN (opcional)
    
    Returns:
        Dict com informações da service account ou None
    """
    required_vars = [
        'GOOGLE_SERVICE_ACCOUNT_TYPE',
        'GOOGLE_SERVICE_ACCOUNT_PROJECT_ID',
        'GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID',
        'GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY',
        'GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL',
        'GOOGLE_SERVICE_ACCOUNT_CLIENT_ID',
        'GOOGLE_SERVICE_ACCOUNT_AUTH_URI',
        'GOOGLE_SERVICE_ACCOUNT_TOKEN_URI',
        'GOOGLE_SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL',
        'GOOGLE_SERVICE_ACCOUNT_CLIENT_X509_CERT_URL'
    ]
    
    # Verificar se todas as variáveis obrigatórias estão presentes
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        # Se faltar alguma variável obrigatória, retornar None
        # (não logar como erro, pois pode estar usando arquivo JSON)
        return None
    
    # Construir dict com informações da service account
    service_account_info = {
        'type': os.getenv('GOOGLE_SERVICE_ACCOUNT_TYPE'),
        'project_id': os.getenv('GOOGLE_SERVICE_ACCOUNT_PROJECT_ID'),
        'private_key_id': os.getenv('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID'),
        'private_key': os.getenv('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY').replace('\\n', '\n'),
        'client_email': os.getenv('GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL'),
        'client_id': os.getenv('GOOGLE_SERVICE_ACCOUNT_CLIENT_ID'),
        'auth_uri': os.getenv('GOOGLE_SERVICE_ACCOUNT_AUTH_URI'),
        'token_uri': os.getenv('GOOGLE_SERVICE_ACCOUNT_TOKEN_URI'),
        'auth_provider_x509_cert_url': os.getenv('GOOGLE_SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL'),
        'client_x509_cert_url': os.getenv('GOOGLE_SERVICE_ACCOUNT_CLIENT_X509_CERT_URL')
    }
    
    # Adicionar universe_domain se presente
    universe_domain = os.getenv('GOOGLE_SERVICE_ACCOUNT_UNIVERSE_DOMAIN')
    if universe_domain:
        service_account_info['universe_domain'] = universe_domain
    
    return service_account_info


def get_access_token(scopes: list = None) -> Optional[str]:
    """
    Obtém um token de acesso da service account.
    
    Args:
        scopes: Lista de scopes OAuth (opcional)
        
    Returns:
        Token de acesso ou None
    """
    credentials = get_service_account_credentials(scopes)
    
    if not credentials:
        return None
    
    try:
        request = requests.Request()
        credentials.refresh(request)
        return credentials.token
    except Exception as e:
        logger.error(f"Erro ao obter token de acesso: {str(e)}")
        return None

