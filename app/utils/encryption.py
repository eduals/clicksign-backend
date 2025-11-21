from cryptography.fernet import Fernet
from app.config import Config
import base64
import os
import hashlib

# Gerar chave de criptografia (em produção, usar variável de ambiente)
def get_encryption_key():
    """Obtém chave de criptografia"""
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        # Em desenvolvimento, usar chave derivada do SECRET_KEY
        from hashlib import sha256
        key = sha256(Config.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(key)
    else:
        key = key.encode()
    
    return key

def encrypt_credentials(data: dict) -> str:
    """
    Criptografa credenciais (tokens, API keys, etc.).
    
    Args:
        data: Dicionário com credenciais
    
    Returns:
        String criptografada (base64)
    """
    import json
    key = get_encryption_key()
    f = Fernet(key)
    
    json_data = json.dumps(data)
    encrypted = f.encrypt(json_data.encode())
    
    return base64.b64encode(encrypted).decode()

def decrypt_credentials(encrypted_data: str) -> dict:
    """
    Descriptografa credenciais.
    
    Args:
        encrypted_data: String criptografada (base64)
    
    Returns:
        Dicionário com credenciais
    """
    import json
    key = get_encryption_key()
    f = Fernet(key)
    
    encrypted_bytes = base64.b64decode(encrypted_data.encode())
    decrypted = f.decrypt(encrypted_bytes)
    
    return json.loads(decrypted.decode())

