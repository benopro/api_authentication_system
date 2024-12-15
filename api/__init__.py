from flask import Flask
from flask_cors import CORS
from config import Config
from .database import db, login_manager
from .auth import jwt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    jwt.init_app(app)
    login_manager.init_app(app)
    
    # Register blueprints
    from .auth_routes import auth
    from .routes import api
    
    app.register_blueprint(auth, url_prefix='/api/auth')
    app.register_blueprint(api, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app