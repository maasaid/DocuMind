import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from .config import Config
from flask_wtf.csrf import CSRFProtect
db_host = os.getenv('DB_HOST', 'localhost')
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', 'your_password')
db_name = os.getenv('DB_NAME', 'your_database')
csrf = CSRFProtect()

migrate=Migrate()
bc=Bcrypt()
def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)
    
    
    bc.init_app(app)
    
    csrf.init_app(app)

    from .routes import main
    app.register_blueprint(main)
    return app