from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from app.config import Config
from app.database import db, init_db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar CORS
    CORS(app)
    
    # Inicializar banco de dados
    db.init_app(app)
    
    # Inicializar Flask-Migrate
    migrate = Migrate(app, db)
    
    init_db(app)
    
    # Registrar rotas
    from app.routes import account_routes
    app.register_blueprint(account_routes.bp)
    
    return app

