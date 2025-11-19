from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Inicializa o banco de dados e cria as tabelas"""
    with app.app_context():
        db.create_all()

