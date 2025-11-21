import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

def normalize_database_url(url):
    """Normaliza a URL do banco para usar o driver psycopg2"""
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif url.startswith('postgresql://') and '+psycopg2' not in url:
        return url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    return url

class Config:
    # Database
    _db_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/clicksign_db')
    SQLALCHEMY_DATABASE_URI = normalize_database_url(_db_url)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    BACKEND_API_TOKEN = os.getenv('BACKEND_API_TOKEN', 'dev-backend-token-change-in-production')
    
    # Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Trial settings
    TRIAL_DAYS = 20
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', '')

